"""
File monitoring service for real-time hand history file detection.

This service provides comprehensive file monitoring capabilities for poker
hand history directories across multiple platforms (PokerStars, GGPoker).
It includes automatic path detection, real-time monitoring, and background
processing of new files.
"""
import os
import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading
import time

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False
    Observer = None
    FileSystemEventHandler = object  # Use object as base class when watchdog is not available

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from ..models.monitoring import FileMonitoring
from ..models.user import User
from .hand_parser import HandParserService
from .exceptions import FileMonitoringError


logger = logging.getLogger(__name__)


@dataclass
class MonitoringConfig:
    """Configuration for file monitoring."""
    scan_interval: int = 30  # seconds
    file_extensions: List[str] = None
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    debounce_delay: float = 2.0  # seconds
    
    def __post_init__(self):
        if self.file_extensions is None:
            self.file_extensions = ['.txt', '.log']


if WATCHDOG_AVAILABLE:
    class HandHistoryFileHandler(FileSystemEventHandler):
        """File system event handler for hand history files."""
        
        def __init__(self, callback: Callable[[str], None], config: MonitoringConfig):
            """
            Initialize file handler.
            
            Args:
                callback: Function to call when new files are detected
                config: Monitoring configuration
            """
            super().__init__()
            self.callback = callback
            self.config = config
            self.debounce_files: Dict[str, float] = {}
            self.lock = threading.Lock()
            
        def on_created(self, event):
            """Handle file creation events."""
            if not event.is_directory:
                self._handle_file_event(event.src_path)
        
        def on_modified(self, event):
            """Handle file modification events."""
            if not event.is_directory:
                self._handle_file_event(event.src_path)
        
        def _handle_file_event(self, file_path: str):
            """
            Handle file system events with debouncing.
            
            Args:
                file_path: Path to the file that changed
            """
            # Check file extension
            if not any(file_path.lower().endswith(ext) for ext in self.config.file_extensions):
                return
            
            # Check file size
            try:
                if os.path.getsize(file_path) > self.config.max_file_size:
                    logger.warning(f"File too large, skipping: {file_path}")
                    return
            except OSError:
                return
            
            # Debounce file events
            current_time = time.time()
            with self.lock:
                last_event_time = self.debounce_files.get(file_path, 0)
                if current_time - last_event_time < self.config.debounce_delay:
                    return
                self.debounce_files[file_path] = current_time
            
            # Call the callback
            try:
                self.callback(file_path)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
else:
    # Dummy class when watchdog is not available
    class HandHistoryFileHandler:
        """Dummy file handler when watchdog is not available."""
        
        def __init__(self, callback: Callable[[str], None], config: MonitoringConfig):
            self.callback = callback
            self.config = config


class FileWatcherService:
    """
    Service for monitoring poker hand history directories and processing new files.
    
    This service provides real-time monitoring of hand history directories,
    automatic platform detection, and background processing of new files.
    """
    
    def __init__(self, db_session_factory, config: Optional[MonitoringConfig] = None):
        """
        Initialize file watcher service.
        
        Args:
            db_session_factory: Factory function for database sessions
            config: Monitoring configuration
        """
        self.db_session_factory = db_session_factory
        self.config = config or MonitoringConfig()
        self.hand_parser = HandParserService()
        
        # Monitoring state
        self.observers: Dict[str, Observer] = {}
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}
        self.active_monitors: Set[str] = set()
        self.executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="file_watcher")
        
        # File processing queue
        self.file_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        
        self.logger = logging.getLogger(__name__)
        
        if not WATCHDOG_AVAILABLE:
            self.logger.warning(
                "Watchdog library not available. File monitoring will use polling mode."
            )
    
    async def start_service(self):
        """Start the file monitoring service."""
        self.logger.info("Starting file monitoring service")
        
        # Start file processing task
        self.processing_task = asyncio.create_task(self._process_file_queue())
        
        # Load existing monitoring configurations
        await self._load_existing_monitors()
        
        self.logger.info("File monitoring service started")
    
    async def stop_service(self):
        """Stop the file monitoring service."""
        self.logger.info("Stopping file monitoring service")
        
        # Stop all observers
        for observer in self.observers.values():
            observer.stop()
            observer.join()
        
        # Cancel monitoring tasks
        for task in self.monitoring_tasks.values():
            task.cancel()
        
        # Cancel processing task
        if self.processing_task:
            self.processing_task.cancel()
        
        # Shutdown executor
        self.executor.shutdown(wait=True)
        
        self.logger.info("File monitoring service stopped")
    
    async def get_default_paths(self, platform: str) -> List[str]:
        """
        Get default hand history paths for a platform.
        
        Args:
            platform: Platform name ('pokerstars' or 'ggpoker')
            
        Returns:
            List of default directory paths
        """
        paths = []
        
        try:
            if platform == 'pokerstars':
                paths.extend(self._get_pokerstars_paths())
            elif platform == 'ggpoker':
                paths.extend(self._get_ggpoker_paths())
            else:
                self.logger.warning(f"Unknown platform: {platform}")
        
        except Exception as e:
            self.logger.error(f"Error getting default paths for {platform}: {e}")
        
        return [path for path in paths if os.path.exists(path)]
    
    def _get_pokerstars_paths(self) -> List[str]:
        """Get PokerStars default paths for current OS."""
        paths = []
        
        if os.name == 'nt':  # Windows
            base_path = os.path.expandvars(r'%LOCALAPPDATA%\PokerStars\HandHistory')
            if os.path.exists(base_path):
                # Look for username directories
                try:
                    for item in os.listdir(base_path):
                        user_path = os.path.join(base_path, item)
                        if os.path.isdir(user_path):
                            paths.append(user_path)
                except OSError:
                    pass
        else:  # macOS/Linux
            home = os.path.expanduser('~')
            
            # macOS path
            mac_path = os.path.join(home, 'Library/Application Support/PokerStars/HandHistory')
            if os.path.exists(mac_path):
                try:
                    for item in os.listdir(mac_path):
                        user_path = os.path.join(mac_path, item)
                        if os.path.isdir(user_path):
                            paths.append(user_path)
                except OSError:
                    pass
            
            # Linux (Wine) path
            username = os.getenv('USER', 'user')
            linux_path = os.path.join(
                home, 
                f'.wine/drive_c/users/{username}/Local Settings/Application Data/PokerStars/HandHistory'
            )
            if os.path.exists(linux_path):
                try:
                    for item in os.listdir(linux_path):
                        user_path = os.path.join(linux_path, item)
                        if os.path.isdir(user_path):
                            paths.append(user_path)
                except OSError:
                    pass
        
        return paths
    
    def _get_ggpoker_paths(self) -> List[str]:
        """Get GGPoker default paths for current OS."""
        paths = []
        
        if os.name == 'nt':  # Windows
            base_path = os.path.expandvars(r'%APPDATA%\GGPoker\HandHistory')
            if os.path.exists(base_path):
                paths.append(base_path)
        else:  # macOS
            home = os.path.expanduser('~')
            mac_path = os.path.join(home, 'Library/Application Support/GGPoker/HandHistory')
            if os.path.exists(mac_path):
                paths.append(mac_path)
        
        return paths
    
    async def start_monitoring(self, user_id: str, platform: str, directory_path: str) -> bool:
        """
        Start monitoring a directory for a user.
        
        Args:
            user_id: User ID
            platform: Platform name
            directory_path: Directory to monitor
            
        Returns:
            True if monitoring started successfully
        """
        monitor_key = f"{user_id}:{platform}:{directory_path}"
        
        if monitor_key in self.active_monitors:
            self.logger.info(f"Already monitoring {directory_path} for user {user_id}")
            return True
        
        try:
            # Validate directory
            if not os.path.exists(directory_path) or not os.path.isdir(directory_path):
                raise FileMonitoringError(f"Directory does not exist: {directory_path}")
            
            # Create or update monitoring record
            try:
                async with self.db_session_factory() as session:
                    # Check if monitoring record exists
                    stmt = select(FileMonitoring).where(
                        FileMonitoring.user_id == user_id,
                        FileMonitoring.platform == platform,
                        FileMonitoring.directory_path == directory_path
                    )
                    result = await session.execute(stmt)
                    monitoring_record = result.scalar_one_or_none()
                    
                    if monitoring_record:
                        # Update existing record
                        monitoring_record.is_active = True
                        monitoring_record.last_scan = datetime.now(timezone.utc)
                    else:
                        # Create new record
                        monitoring_record = FileMonitoring(
                            user_id=user_id,
                            platform=platform,
                            directory_path=directory_path,
                            is_active=True,
                            last_scan=datetime.now(timezone.utc)
                        )
                        session.add(monitoring_record)
                    
                    await session.commit()
            except Exception as db_error:
                self.logger.warning(f"Database operation failed, continuing with monitoring: {db_error}")
                # Continue with file monitoring even if database fails
            
            # Start file system monitoring
            if WATCHDOG_AVAILABLE:
                await self._start_watchdog_monitoring(monitor_key, user_id, platform, directory_path)
            else:
                await self._start_polling_monitoring(monitor_key, user_id, platform, directory_path)
            
            self.active_monitors.add(monitor_key)
            self.logger.info(f"Started monitoring {directory_path} for user {user_id} ({platform})")
            
            # Perform initial scan
            await self._scan_directory(user_id, platform, directory_path)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring {directory_path}: {e}")
            return False
    
    async def stop_monitoring(self, user_id: str, platform: str, directory_path: str) -> bool:
        """
        Stop monitoring a directory for a user.
        
        Args:
            user_id: User ID
            platform: Platform name
            directory_path: Directory to stop monitoring
            
        Returns:
            True if monitoring stopped successfully
        """
        monitor_key = f"{user_id}:{platform}:{directory_path}"
        
        try:
            # Stop file system monitoring
            if monitor_key in self.observers:
                self.observers[monitor_key].stop()
                self.observers[monitor_key].join()
                del self.observers[monitor_key]
            
            if monitor_key in self.monitoring_tasks:
                self.monitoring_tasks[monitor_key].cancel()
                del self.monitoring_tasks[monitor_key]
            
            # Update database record
            try:
                async with self.db_session_factory() as session:
                    stmt = update(FileMonitoring).where(
                        FileMonitoring.user_id == user_id,
                        FileMonitoring.platform == platform,
                        FileMonitoring.directory_path == directory_path
                    ).values(is_active=False)
                    
                    await session.execute(stmt)
                    await session.commit()
            except Exception as db_error:
                self.logger.warning(f"Database update failed during stop monitoring: {db_error}")
                # Continue with stopping monitoring even if database fails
            
            self.active_monitors.discard(monitor_key)
            self.logger.info(f"Stopped monitoring {directory_path} for user {user_id}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop monitoring {directory_path}: {e}")
            return False
    
    async def _start_watchdog_monitoring(self, monitor_key: str, user_id: str, platform: str, directory_path: str):
        """Start watchdog-based file monitoring."""
        def file_callback(file_path: str):
            # Queue file for processing
            asyncio.create_task(self.file_queue.put({
                'user_id': user_id,
                'platform': platform,
                'file_path': file_path,
                'directory_path': directory_path
            }))
        
        # Create event handler and observer
        event_handler = HandHistoryFileHandler(file_callback, self.config)
        observer = Observer()
        observer.schedule(event_handler, directory_path, recursive=True)
        observer.start()
        
        self.observers[monitor_key] = observer
    
    async def _start_polling_monitoring(self, monitor_key: str, user_id: str, platform: str, directory_path: str):
        """Start polling-based file monitoring."""
        async def polling_task():
            last_scan_files = set()
            
            while True:
                try:
                    current_files = set()
                    
                    # Scan directory for hand history files
                    for root, dirs, files in os.walk(directory_path):
                        for file in files:
                            if any(file.lower().endswith(ext) for ext in self.config.file_extensions):
                                file_path = os.path.join(root, file)
                                current_files.add(file_path)
                    
                    # Find new files
                    new_files = current_files - last_scan_files
                    
                    # Process new files
                    for file_path in new_files:
                        await self.file_queue.put({
                            'user_id': user_id,
                            'platform': platform,
                            'file_path': file_path,
                            'directory_path': directory_path
                        })
                    
                    last_scan_files = current_files
                    
                    # Wait before next scan
                    await asyncio.sleep(self.config.scan_interval)
                    
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    self.logger.error(f"Error in polling task for {directory_path}: {e}")
                    await asyncio.sleep(self.config.scan_interval)
        
        # Start polling task
        task = asyncio.create_task(polling_task())
        self.monitoring_tasks[monitor_key] = task
    
    async def _process_file_queue(self):
        """Process files from the monitoring queue."""
        while True:
            try:
                # Get file from queue
                file_info = await self.file_queue.get()
                
                # Process file in background
                await self._process_new_file(
                    file_info['user_id'],
                    file_info['platform'],
                    file_info['file_path'],
                    file_info['directory_path']
                )
                
                # Mark task as done
                self.file_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error processing file queue: {e}")
    
    async def _process_new_file(self, user_id: str, platform: str, file_path: str, directory_path: str):
        """
        Process a newly detected hand history file.
        
        Args:
            user_id: User ID
            platform: Platform name
            file_path: Path to the new file
            directory_path: Directory being monitored
        """
        try:
            self.logger.info(f"Processing new file: {file_path}")
            
            # Wait a moment for file to be fully written
            await asyncio.sleep(1)
            
            # Check if file still exists and is readable
            if not os.path.exists(file_path):
                return
            
            # Check file size - if large, use background processor
            file_size = os.path.getsize(file_path)
            large_file_threshold = 1024 * 1024  # 1MB
            
            if file_size > large_file_threshold:
                # Use background processor for large files
                try:
                    from ..main import background_processor_service
                    if background_processor_service:
                        task_id = await background_processor_service.submit_file_processing(
                            user_id=user_id,
                            file_path=file_path,
                            platform=platform,
                            task_name=f"Auto-process {os.path.basename(file_path)}",
                            processing_options={
                                'auto_detected': True,
                                'directory_monitoring': True,
                                'directory_path': directory_path
                            }
                        )
                        self.logger.info(f"Submitted large file {file_path} for background processing (task: {task_id})")
                        return
                except Exception as e:
                    self.logger.warning(f"Failed to submit file for background processing, falling back to direct processing: {e}")
            
            # Process smaller files directly (existing logic)
            hands, errors = self.hand_parser.parse_file(file_path)
            
            if hands:
                # TODO: Save hands to database (will be implemented in later tasks)
                self.logger.info(f"Parsed {len(hands)} hands from {file_path}")
            
            if errors:
                self.logger.warning(f"Encountered {len(errors)} errors parsing {file_path}")
            
            # Update monitoring record
            await self._update_monitoring_stats(user_id, platform, directory_path)
            
        except Exception as e:
            self.logger.error(f"Error processing file {file_path}: {e}")
    
    async def _scan_directory(self, user_id: str, platform: str, directory_path: str):
        """
        Perform initial scan of directory.
        
        Args:
            user_id: User ID
            platform: Platform name
            directory_path: Directory to scan
        """
        try:
            file_count = 0
            
            # Count hand history files
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in self.config.file_extensions):
                        file_count += 1
            
            # Update monitoring record
            try:
                async with self.db_session_factory() as session:
                    stmt = update(FileMonitoring).where(
                        FileMonitoring.user_id == user_id,
                        FileMonitoring.platform == platform,
                        FileMonitoring.directory_path == directory_path
                    ).values(
                        file_count=file_count,
                        last_scan=datetime.now(timezone.utc)
                    )
                    
                    await session.execute(stmt)
                    await session.commit()
            except Exception as db_error:
                self.logger.warning(f"Database update failed during directory scan: {db_error}")
                # Continue even if database update fails
            
            self.logger.info(f"Initial scan found {file_count} files in {directory_path}")
            
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory_path}: {e}")
    
    async def _update_monitoring_stats(self, user_id: str, platform: str, directory_path: str):
        """Update monitoring statistics."""
        try:
            async with self.db_session_factory() as session:
                stmt = update(FileMonitoring).where(
                    FileMonitoring.user_id == user_id,
                    FileMonitoring.platform == platform,
                    FileMonitoring.directory_path == directory_path
                ).values(last_scan=datetime.now(timezone.utc))
                
                await session.execute(stmt)
                await session.commit()
                
        except Exception as e:
            self.logger.warning(f"Error updating monitoring stats: {e}")
            # Don't fail file processing if stats update fails
    
    async def _load_existing_monitors(self):
        """Load and restart existing monitoring configurations."""
        try:
            async with self.db_session_factory() as session:
                stmt = select(FileMonitoring).where(FileMonitoring.is_active == True)
                result = await session.execute(stmt)
                monitors = result.scalars().all()
                
                for monitor in monitors:
                    await self.start_monitoring(
                        monitor.user_id,
                        monitor.platform,
                        monitor.directory_path
                    )
                
                self.logger.info(f"Loaded {len(monitors)} existing monitoring configurations")
                
        except Exception as e:
            self.logger.error(f"Error loading existing monitors: {e}")
            # Don't fail startup if we can't load existing monitors
            pass
    
    async def get_monitoring_status(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get monitoring status for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of monitoring status information
        """
        try:
            async with self.db_session_factory() as session:
                stmt = select(FileMonitoring).where(FileMonitoring.user_id == user_id)
                result = await session.execute(stmt)
                monitors = result.scalars().all()
                
                status_list = []
                for monitor in monitors:
                    monitor_key = f"{user_id}:{monitor.platform}:{monitor.directory_path}"
                    status_list.append({
                        'platform': monitor.platform,
                        'directory_path': monitor.directory_path,
                        'is_active': monitor.is_active,
                        'last_scan': monitor.last_scan,
                        'file_count': monitor.file_count,
                        'is_monitoring': monitor_key in self.active_monitors
                    })
                
                return status_list
                
        except Exception as e:
            self.logger.error(f"Error getting monitoring status for user {user_id}: {e}")
            # Return empty list instead of failing
            return []
    
    async def scan_directory_for_files(self, directory_path: str, recursive: bool = True) -> List[str]:
        """
        Scan directory for hand history files.
        
        Args:
            directory_path: Directory to scan
            recursive: Whether to scan subdirectories
            
        Returns:
            List of hand history file paths
        """
        return self.hand_parser.scan_directory(directory_path, recursive)