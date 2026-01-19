"""
Background file processing service with progress tracking.

This service handles asynchronous processing of large hand history files
with real-time progress updates and comprehensive error handling.
"""
import asyncio
import logging
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
import traceback

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..models.file_processing import FileProcessingTask, ProcessingStatus
from ..models.hand import PokerHand
from ..schemas.hand import HandCreate
from .hand_parser import HandParserService
from .exceptions import HandParsingError, UnsupportedPlatformError


logger = logging.getLogger(__name__)


@dataclass
class ProcessingProgress:
    """Progress information for file processing."""
    task_id: str
    progress_percentage: int
    current_step: str
    hands_processed: int
    hands_failed: int
    estimated_completion: Optional[datetime] = None
    processing_rate: Optional[float] = None  # hands per second


@dataclass
class ProcessingResult:
    """Result of file processing operation."""
    success: bool
    hands_processed: int
    hands_failed: int
    processing_time: float
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class BackgroundFileProcessor:
    """
    Service for processing large hand history files in the background
    with progress tracking and real-time updates.
    """
    
    def __init__(self, db_session_factory, max_workers: int = 4):
        """
        Initialize background file processor.
        
        Args:
            db_session_factory: Factory function for database sessions
            max_workers: Maximum number of concurrent processing workers
        """
        self.db_session_factory = db_session_factory
        self.max_workers = max_workers
        self.hand_parser = HandParserService()
        
        # Processing state
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.progress_callbacks: Dict[str, List[Callable[[ProcessingProgress], None]]] = {}
        self.executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="bg_processor")
        
        # Processing queue
        self.processing_queue: asyncio.Queue = asyncio.Queue()
        self.queue_processor_task: Optional[asyncio.Task] = None
        
        self.logger = logging.getLogger(__name__)
    
    async def start_service(self):
        """Start the background processing service."""
        self.logger.info("Starting background file processing service")
        
        # Start queue processor
        self.queue_processor_task = asyncio.create_task(self._process_queue())
        
        self.logger.info("Background file processing service started")
    
    async def stop_service(self):
        """Stop the background processing service."""
        self.logger.info("Stopping background file processing service")
        
        # Cancel queue processor
        if self.queue_processor_task:
            self.queue_processor_task.cancel()
        
        # Cancel all active tasks
        for task in self.active_tasks.values():
            task.cancel()
        
        # Wait for tasks to complete
        if self.active_tasks:
            await asyncio.gather(*self.active_tasks.values(), return_exceptions=True)
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        self.logger.info("Background file processing service stopped")
    
    async def submit_file_processing(self, 
                                   user_id: str,
                                   file_path: str,
                                   platform: Optional[str] = None,
                                   task_name: Optional[str] = None,
                                   processing_options: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit a file for background processing.
        
        Args:
            user_id: User ID
            file_path: Path to file to process
            platform: Platform name (auto-detected if not provided)
            task_name: Human-readable task name
            processing_options: Additional processing options
            
        Returns:
            Task ID for tracking progress
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is too large or invalid
        """
        file_path_obj = Path(file_path)
        
        # Validate file
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size = file_path_obj.stat().st_size
        if file_size == 0:
            raise ValueError("File is empty")
        
        # Create processing task record
        async with self.db_session_factory() as session:
            task = FileProcessingTask(
                user_id=user_id,
                task_name=task_name or f"Process {file_path_obj.name}",
                task_type="file_parse",
                file_path=str(file_path),
                file_size=file_size,
                platform=platform,
                status=ProcessingStatus.PENDING,
                processing_options=processing_options or {}
            )
            
            session.add(task)
            await session.commit()
            await session.refresh(task)
            
            task_id = str(task.id)
        
        # Queue for processing
        await self.processing_queue.put({
            'task_id': task_id,
            'user_id': user_id,
            'file_path': file_path,
            'platform': platform,
            'processing_options': processing_options or {}
        })
        
        self.logger.info(f"Queued file processing task {task_id} for user {user_id}")
        return task_id
    
    async def submit_batch_processing(self,
                                    user_id: str,
                                    file_paths: List[str],
                                    platform: Optional[str] = None,
                                    task_name: Optional[str] = None,
                                    processing_options: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit multiple files for batch processing.
        
        Args:
            user_id: User ID
            file_paths: List of file paths to process
            platform: Platform name (auto-detected if not provided)
            task_name: Human-readable task name
            processing_options: Additional processing options
            
        Returns:
            Task ID for tracking progress
        """
        # Validate files
        valid_files = []
        total_size = 0
        
        for file_path in file_paths:
            file_path_obj = Path(file_path)
            if file_path_obj.exists() and file_path_obj.stat().st_size > 0:
                valid_files.append(file_path)
                total_size += file_path_obj.stat().st_size
        
        if not valid_files:
            raise ValueError("No valid files found for processing")
        
        # Create processing task record
        async with self.db_session_factory() as session:
            task = FileProcessingTask(
                user_id=user_id,
                task_name=task_name or f"Batch process {len(valid_files)} files",
                task_type="batch_import",
                file_size=total_size,
                platform=platform,
                status=ProcessingStatus.PENDING,
                processing_options={
                    **(processing_options or {}),
                    'file_paths': valid_files,
                    'batch_size': len(valid_files)
                }
            )
            
            session.add(task)
            await session.commit()
            await session.refresh(task)
            
            task_id = str(task.id)
        
        # Queue for processing
        await self.processing_queue.put({
            'task_id': task_id,
            'user_id': user_id,
            'file_paths': valid_files,
            'platform': platform,
            'processing_options': processing_options or {}
        })
        
        self.logger.info(f"Queued batch processing task {task_id} for user {user_id} ({len(valid_files)} files)")
        return task_id
    
    async def get_task_progress(self, task_id: str) -> Optional[ProcessingProgress]:
        """
        Get current progress for a processing task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Progress information or None if task not found
        """
        try:
            async with self.db_session_factory() as session:
                stmt = select(FileProcessingTask).where(FileProcessingTask.id == task_id)
                result = await session.execute(stmt)
                task = result.scalar_one_or_none()
                
                if not task:
                    return None
                
                # Calculate processing rate if available
                processing_rate = None
                if task.started_at and task.hands_processed > 0:
                    elapsed = (datetime.utcnow() - task.started_at).total_seconds()
                    if elapsed > 0:
                        processing_rate = task.hands_processed / elapsed
                
                return ProcessingProgress(
                    task_id=task_id,
                    progress_percentage=task.progress_percentage,
                    current_step=task.current_step or "Initializing...",
                    hands_processed=task.hands_processed,
                    hands_failed=task.hands_failed,
                    estimated_completion=task.estimated_completion,
                    processing_rate=processing_rate
                )
                
        except Exception as e:
            self.logger.error(f"Error getting task progress for {task_id}: {e}")
            return None
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a processing task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if task was cancelled successfully
        """
        try:
            # Cancel active task if running
            if task_id in self.active_tasks:
                self.active_tasks[task_id].cancel()
                del self.active_tasks[task_id]
            
            # Update database record
            async with self.db_session_factory() as session:
                stmt = update(FileProcessingTask).where(
                    FileProcessingTask.id == task_id
                ).values(
                    status="cancelled",
                    completed_at=datetime.utcnow(),
                    current_step="Cancelled by user"
                )
                
                await session.execute(stmt)
                await session.commit()
            
            self.logger.info(f"Cancelled processing task {task_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling task {task_id}: {e}")
            return False
    
    def register_progress_callback(self, task_id: str, callback: Callable[[ProcessingProgress], None]):
        """
        Register a callback for progress updates.
        
        Args:
            task_id: Task ID to monitor
            callback: Function to call with progress updates
        """
        if task_id not in self.progress_callbacks:
            self.progress_callbacks[task_id] = []
        self.progress_callbacks[task_id].append(callback)
    
    async def _process_queue(self):
        """Process the background processing queue."""
        while True:
            try:
                # Get task from queue
                task_info = await self.processing_queue.get()
                
                # Start processing task
                task_id = task_info['task_id']
                processing_task = asyncio.create_task(self._process_task(task_info))
                self.active_tasks[task_id] = processing_task
                
                # Clean up completed task
                def cleanup_task(task):
                    if task_id in self.active_tasks:
                        del self.active_tasks[task_id]
                    if task_id in self.progress_callbacks:
                        del self.progress_callbacks[task_id]
                
                processing_task.add_done_callback(cleanup_task)
                
                # Mark queue task as done
                self.processing_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in queue processor: {e}")
    
    async def _process_task(self, task_info: Dict[str, Any]):
        """
        Process a single task.
        
        Args:
            task_info: Task information dictionary
        """
        task_id = task_info['task_id']
        start_time = time.time()
        
        try:
            # Update task status to processing
            await self._update_task_status(task_id, ProcessingStatus.PROCESSING, "Starting processing...")
            
            # Determine processing type
            if 'file_paths' in task_info:
                result = await self._process_batch_files(task_id, task_info)
            else:
                result = await self._process_single_file(task_id, task_info)
            
            # Update final status
            if result.success:
                await self._complete_task(task_id, result, start_time)
            else:
                await self._fail_task(task_id, result, start_time)
                
        except asyncio.CancelledError:
            await self._update_task_status(task_id, "cancelled", "Processing cancelled")
            raise
        except Exception as e:
            error_details = {
                'exception_type': type(e).__name__,
                'exception_message': str(e),
                'traceback': traceback.format_exc()
            }
            
            result = ProcessingResult(
                success=False,
                hands_processed=0,
                hands_failed=0,
                processing_time=time.time() - start_time,
                error_message=str(e),
                error_details=error_details
            )
            
            await self._fail_task(task_id, result, start_time)
    
    async def _process_single_file(self, task_id: str, task_info: Dict[str, Any]) -> ProcessingResult:
        """Process a single file."""
        file_path = task_info['file_path']
        user_id = task_info['user_id']
        platform = task_info.get('platform')
        
        try:
            await self._update_progress(task_id, 10, "Reading file...")
            
            # Parse file
            hands, errors = self.hand_parser.parse_file(file_path)
            
            await self._update_progress(task_id, 30, f"Parsed {len(hands)} hands, processing...")
            
            # Process hands in batches
            hands_processed = 0
            hands_failed = len(errors)
            batch_size = 100
            
            for i in range(0, len(hands), batch_size):
                batch = hands[i:i + batch_size]
                
                # Save batch to database
                saved_count = await self._save_hands_batch(user_id, batch)
                hands_processed += saved_count
                
                # Update progress
                progress = 30 + int((i + len(batch)) / len(hands) * 60)
                await self._update_progress(
                    task_id, 
                    progress, 
                    f"Processed {hands_processed} hands...",
                    hands_processed,
                    hands_failed
                )
            
            await self._update_progress(task_id, 100, "Processing complete")
            
            return ProcessingResult(
                success=True,
                hands_processed=hands_processed,
                hands_failed=hands_failed,
                processing_time=0  # Will be calculated by caller
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                hands_processed=0,
                hands_failed=0,
                processing_time=0,
                error_message=str(e)
            )
    
    async def _process_batch_files(self, task_id: str, task_info: Dict[str, Any]) -> ProcessingResult:
        """Process multiple files in batch."""
        file_paths = task_info['file_paths']
        user_id = task_info['user_id']
        
        total_hands_processed = 0
        total_hands_failed = 0
        
        try:
            for i, file_path in enumerate(file_paths):
                # Update progress
                file_progress = int((i / len(file_paths)) * 90)
                await self._update_progress(
                    task_id, 
                    file_progress, 
                    f"Processing file {i+1}/{len(file_paths)}: {Path(file_path).name}"
                )
                
                try:
                    # Parse file
                    hands, errors = self.hand_parser.parse_file(file_path)
                    
                    # Save hands
                    saved_count = await self._save_hands_batch(user_id, hands)
                    total_hands_processed += saved_count
                    total_hands_failed += len(errors)
                    
                    # Update progress with current totals
                    await self._update_progress(
                        task_id,
                        file_progress,
                        f"Processed {total_hands_processed} hands from {i+1} files...",
                        total_hands_processed,
                        total_hands_failed
                    )
                    
                except Exception as e:
                    self.logger.warning(f"Error processing file {file_path}: {e}")
                    total_hands_failed += 1
            
            await self._update_progress(task_id, 100, "Batch processing complete")
            
            return ProcessingResult(
                success=True,
                hands_processed=total_hands_processed,
                hands_failed=total_hands_failed,
                processing_time=0
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                hands_processed=total_hands_processed,
                hands_failed=total_hands_failed,
                processing_time=0,
                error_message=str(e)
            )
    
    async def _save_hands_batch(self, user_id: str, hands: List[HandCreate]) -> int:
        """
        Save a batch of hands to the database.
        
        Args:
            user_id: User ID
            hands: List of hands to save
            
        Returns:
            Number of hands successfully saved
        """
        if not hands:
            return 0
        
        saved_count = 0
        
        try:
            async with self.db_session_factory() as session:
                for hand_data in hands:
                    try:
                        # Create PokerHand instance
                        poker_hand = PokerHand(
                            user_id=user_id,
                            hand_id=hand_data.hand_id,
                            platform=hand_data.platform,
                            game_type=hand_data.game_type,
                            game_format=hand_data.game_format,
                            stakes=hand_data.stakes,
                            blinds=hand_data.blinds if isinstance(hand_data.blinds, dict) else (hand_data.blinds.dict() if hand_data.blinds else None),
                            table_size=hand_data.table_size,
                            date_played=hand_data.date_played,
                            player_cards=hand_data.player_cards,
                            board_cards=hand_data.board_cards,
                            position=hand_data.position,
                            seat_number=hand_data.seat_number,
                            button_position=hand_data.button_position,
                            actions=hand_data.actions if isinstance(hand_data.actions, dict) else (hand_data.actions.dict() if hand_data.actions else None),
                            result=hand_data.result,
                            pot_size=hand_data.pot_size,
                            rake=hand_data.rake,
                            jackpot_contribution=hand_data.jackpot_contribution,
                            tournament_info=hand_data.tournament_info if isinstance(hand_data.tournament_info, dict) else (hand_data.tournament_info.dict() if hand_data.tournament_info else None),
                            cash_game_info=hand_data.cash_game_info if isinstance(hand_data.cash_game_info, dict) else (hand_data.cash_game_info.dict() if hand_data.cash_game_info else None),
                            player_stacks=hand_data.player_stacks,
                            timebank_info=[info.dict() if hasattr(info, 'dict') else info for info in hand_data.timebank_info] if hand_data.timebank_info else None,
                            hand_duration=hand_data.hand_duration,
                            timezone=hand_data.timezone,
                            currency=hand_data.currency,
                            is_play_money=hand_data.is_play_money,
                            raw_text=hand_data.raw_text
                        )
                        
                        session.add(poker_hand)
                        saved_count += 1
                        
                    except Exception as e:
                        self.logger.warning(f"Error saving hand {hand_data.hand_id}: {e}")
                        continue
                
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving hands batch: {e}")
        
        return saved_count
    
    async def _update_task_status(self, task_id: str, status: ProcessingStatus, current_step: str):
        """Update task status in database."""
        try:
            async with self.db_session_factory() as session:
                update_data = {
                    'status': status.value if hasattr(status, 'value') else status,
                    'current_step': current_step
                }
                
                if status == "processing":
                    update_data['started_at'] = datetime.utcnow()
                
                stmt = update(FileProcessingTask).where(
                    FileProcessingTask.id == task_id
                ).values(**update_data)
                
                await session.execute(stmt)
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Error updating task status for {task_id}: {e}")
    
    async def _update_progress(self, 
                             task_id: str, 
                             progress_percentage: int, 
                             current_step: str,
                             hands_processed: Optional[int] = None,
                             hands_failed: Optional[int] = None):
        """Update task progress in database and notify callbacks."""
        try:
            async with self.db_session_factory() as session:
                # Get current task data
                stmt = select(FileProcessingTask).where(FileProcessingTask.id == task_id)
                result = await session.execute(stmt)
                task = result.scalar_one_or_none()
                
                if task:
                    # Update progress
                    task.update_progress(
                        progress_percentage, 
                        current_step, 
                        hands_processed, 
                        hands_failed
                    )
                    
                    await session.commit()
                    
                    # Notify callbacks
                    if task_id in self.progress_callbacks:
                        progress = ProcessingProgress(
                            task_id=task_id,
                            progress_percentage=progress_percentage,
                            current_step=current_step,
                            hands_processed=task.hands_processed,
                            hands_failed=task.hands_failed,
                            estimated_completion=task.estimated_completion
                        )
                        
                        for callback in self.progress_callbacks[task_id]:
                            try:
                                callback(progress)
                            except Exception as e:
                                self.logger.warning(f"Error in progress callback: {e}")
                
        except Exception as e:
            self.logger.error(f"Error updating progress for {task_id}: {e}")
    
    async def _complete_task(self, task_id: str, result: ProcessingResult, start_time: float):
        """Mark task as completed."""
        processing_time = time.time() - start_time
        hands_per_second = result.hands_processed / processing_time if processing_time > 0 else 0
        
        try:
            async with self.db_session_factory() as session:
                stmt = update(FileProcessingTask).where(
                    FileProcessingTask.id == task_id
                ).values(
                    status="completed",
                    completed_at=datetime.utcnow(),
                    processing_time_seconds=processing_time,
                    hands_per_second=hands_per_second,
                    result_summary={
                        'hands_processed': result.hands_processed,
                        'hands_failed': result.hands_failed,
                        'success_rate': (result.hands_processed / (result.hands_processed + result.hands_failed) * 100) if (result.hands_processed + result.hands_failed) > 0 else 0,
                        'processing_rate': hands_per_second
                    }
                )
                
                await session.execute(stmt)
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Error completing task {task_id}: {e}")
    
    async def _fail_task(self, task_id: str, result: ProcessingResult, start_time: float):
        """Mark task as failed."""
        processing_time = time.time() - start_time
        
        try:
            async with self.db_session_factory() as session:
                stmt = update(FileProcessingTask).where(
                    FileProcessingTask.id == task_id
                ).values(
                    status="failed",
                    completed_at=datetime.utcnow(),
                    processing_time_seconds=processing_time,
                    error_message=result.error_message,
                    error_details=result.error_details
                )
                
                await session.execute(stmt)
                await session.commit()
                
        except Exception as e:
            self.logger.error(f"Error failing task {task_id}: {e}")
    
    async def get_user_tasks(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get processing tasks for a user.
        
        Args:
            user_id: User ID
            limit: Maximum number of tasks to return
            
        Returns:
            List of task information
        """
        try:
            async with self.db_session_factory() as session:
                stmt = select(FileProcessingTask).where(
                    FileProcessingTask.user_id == user_id
                ).order_by(FileProcessingTask.created_at.desc()).limit(limit)
                
                result = await session.execute(stmt)
                tasks = result.scalars().all()
                
                return [
                    {
                        'id': str(task.id),
                        'task_name': task.task_name,
                        'task_type': task.task_type,
                        'status': task.status,
                        'progress_percentage': task.progress_percentage,
                        'current_step': task.current_step,
                        'hands_processed': task.hands_processed,
                        'hands_failed': task.hands_failed,
                        'created_at': task.created_at.isoformat() if task.created_at else None,
                        'started_at': task.started_at.isoformat() if task.started_at else None,
                        'completed_at': task.completed_at.isoformat() if task.completed_at else None,
                        'estimated_completion': task.estimated_completion.isoformat() if task.estimated_completion else None,
                        'success_rate': task.success_rate,
                        'is_active': task.is_active
                    }
                    for task in tasks
                ]
                
        except Exception as e:
            self.logger.error(f"Error getting user tasks for {user_id}: {e}")
            return []