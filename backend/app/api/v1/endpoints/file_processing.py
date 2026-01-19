"""
File processing endpoints for background file processing with progress tracking.
"""
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services.background_processor import BackgroundFileProcessor, ProcessingProgress
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


class FileProcessingRequest(BaseModel):
    """Request model for file processing."""
    file_path: str = Field(..., description="Path to file to process")
    platform: Optional[str] = Field(None, description="Poker platform (auto-detected if not provided)")
    task_name: Optional[str] = Field(None, description="Custom task name")
    processing_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional processing options")


class BatchProcessingRequest(BaseModel):
    """Request model for batch file processing."""
    file_paths: List[str] = Field(..., description="List of file paths to process")
    platform: Optional[str] = Field(None, description="Poker platform (auto-detected if not provided)")
    task_name: Optional[str] = Field(None, description="Custom task name")
    processing_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional processing options")


class ProcessingTaskResponse(BaseModel):
    """Response model for processing task creation."""
    task_id: str
    message: str
    estimated_processing_time: Optional[str] = None


class ProgressResponse(BaseModel):
    """Response model for task progress."""
    task_id: str
    progress_percentage: int
    current_step: str
    hands_processed: int
    hands_failed: int
    estimated_completion: Optional[str] = None
    processing_rate: Optional[float] = None
    is_active: bool


class TaskListResponse(BaseModel):
    """Response model for task list."""
    tasks: List[Dict[str, Any]]
    total_tasks: int
    active_tasks: int


def get_background_processor() -> BackgroundFileProcessor:
    """Get the background processor service instance."""
    from app.main import background_processor_service
    if background_processor_service is None:
        raise HTTPException(status_code=503, detail="Background processing service not available")
    return background_processor_service


@router.post("/process-file", response_model=ProcessingTaskResponse)
async def process_file(
    request: FileProcessingRequest,
    current_user: User = Depends(get_current_user),
    processor: BackgroundFileProcessor = Depends(get_background_processor)
):
    """
    Submit a file for background processing.
    
    Args:
        request: File processing configuration
        
    Returns:
        Task ID and processing information
    """
    try:
        task_id = await processor.submit_file_processing(
            user_id=str(current_user.id),
            file_path=request.file_path,
            platform=request.platform,
            task_name=request.task_name,
            processing_options=request.processing_options
        )
        
        return ProcessingTaskResponse(
            task_id=task_id,
            message="File processing started successfully",
            estimated_processing_time="Processing time will be estimated once started"
        )
        
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to start file processing", 
                    file_path=request.file_path, 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to start file processing")


@router.post("/process-batch", response_model=ProcessingTaskResponse)
async def process_batch(
    request: BatchProcessingRequest,
    current_user: User = Depends(get_current_user),
    processor: BackgroundFileProcessor = Depends(get_background_processor)
):
    """
    Submit multiple files for batch processing.
    
    Args:
        request: Batch processing configuration
        
    Returns:
        Task ID and processing information
    """
    try:
        task_id = await processor.submit_batch_processing(
            user_id=str(current_user.id),
            file_paths=request.file_paths,
            platform=request.platform,
            task_name=request.task_name,
            processing_options=request.processing_options
        )
        
        return ProcessingTaskResponse(
            task_id=task_id,
            message=f"Batch processing started for {len(request.file_paths)} files",
            estimated_processing_time="Processing time will be estimated once started"
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Failed to start batch processing", 
                    file_count=len(request.file_paths), 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to start batch processing")


@router.post("/upload-and-process")
async def upload_and_process(
    file: UploadFile = File(...),
    platform: Optional[str] = Form(None),
    task_name: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    processor: BackgroundFileProcessor = Depends(get_background_processor)
):
    """
    Upload a file and process it in the background.
    
    Args:
        file: Uploaded file
        platform: Poker platform (auto-detected if not provided)
        task_name: Custom task name
        
    Returns:
        Task ID and processing information
    """
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Check file size (limit to 50MB)
        max_size = 50 * 1024 * 1024  # 50MB
        content = await file.read()
        if len(content) > max_size:
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")
        
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Save uploaded file temporarily
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.txt') as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Submit for processing
            task_id = await processor.submit_file_processing(
                user_id=str(current_user.id),
                file_path=temp_file_path,
                platform=platform,
                task_name=task_name or f"Process uploaded file: {file.filename}",
                processing_options={
                    'uploaded_file': True,
                    'original_filename': file.filename,
                    'temp_file_path': temp_file_path
                }
            )
            
            return ProcessingTaskResponse(
                task_id=task_id,
                message=f"File '{file.filename}' uploaded and processing started",
                estimated_processing_time="Processing time will be estimated once started"
            )
            
        except Exception as e:
            # Clean up temp file on error
            try:
                os.unlink(temp_file_path)
            except:
                pass
            raise e
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to upload and process file", 
                    filename=file.filename, 
                    error=str(e))
        raise HTTPException(status_code=500, detail="Failed to upload and process file")


@router.get("/progress/{task_id}", response_model=ProgressResponse)
async def get_task_progress(
    task_id: str,
    current_user: User = Depends(get_current_user),
    processor: BackgroundFileProcessor = Depends(get_background_processor)
):
    """
    Get progress for a processing task.
    
    Args:
        task_id: Task ID to check
        
    Returns:
        Current progress information
    """
    try:
        progress = await processor.get_task_progress(task_id)
        
        if not progress:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return ProgressResponse(
            task_id=progress.task_id,
            progress_percentage=progress.progress_percentage,
            current_step=progress.current_step,
            hands_processed=progress.hands_processed,
            hands_failed=progress.hands_failed,
            estimated_completion=progress.estimated_completion.isoformat() if progress.estimated_completion else None,
            processing_rate=progress.processing_rate,
            is_active=progress.progress_percentage < 100
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task progress", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get task progress")


@router.post("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    processor: BackgroundFileProcessor = Depends(get_background_processor)
):
    """
    Cancel a processing task.
    
    Args:
        task_id: Task ID to cancel
        
    Returns:
        Cancellation confirmation
    """
    try:
        success = await processor.cancel_task(task_id)
        
        if not success:
            raise HTTPException(status_code=400, detail="Failed to cancel task")
        
        return {
            "message": "Task cancelled successfully",
            "task_id": task_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to cancel task", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to cancel task")


@router.get("/tasks", response_model=TaskListResponse)
async def get_user_tasks(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    processor: BackgroundFileProcessor = Depends(get_background_processor)
):
    """
    Get processing tasks for the current user.
    
    Args:
        limit: Maximum number of tasks to return
        
    Returns:
        List of user's processing tasks
    """
    try:
        tasks = await processor.get_user_tasks(str(current_user.id), limit)
        
        # Count active tasks
        active_tasks = sum(1 for task in tasks if task.get('is_active', False))
        
        return TaskListResponse(
            tasks=tasks,
            total_tasks=len(tasks),
            active_tasks=active_tasks
        )
        
    except Exception as e:
        logger.error("Failed to get user tasks", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get user tasks")


@router.get("/status")
async def get_processing_status(
    current_user: User = Depends(get_current_user),
    processor: BackgroundFileProcessor = Depends(get_background_processor)
):
    """
    Get overall processing service status.
    
    Returns:
        Service status information
    """
    try:
        # Get user's active tasks
        tasks = await processor.get_user_tasks(str(current_user.id), 10)
        active_tasks = [task for task in tasks if task.get('is_active', False)]
        
        return {
            "service_status": "running",
            "active_tasks": len(active_tasks),
            "queue_size": processor.processing_queue.qsize(),
            "max_workers": processor.max_workers,
            "recent_tasks": tasks[:5]  # Last 5 tasks
        }
        
    except Exception as e:
        logger.error("Failed to get processing status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get processing status")


@router.get("/supported-formats")
async def get_supported_formats():
    """
    Get supported file formats and platforms.
    
    Returns:
        Information about supported formats
    """
    return {
        "platforms": ["pokerstars", "ggpoker"],
        "file_extensions": [".txt", ".log"],
        "max_file_size": "50MB",
        "batch_processing": True,
        "upload_processing": True,
        "auto_platform_detection": True,
        "progress_tracking": True
    }