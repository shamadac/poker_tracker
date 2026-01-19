"""
Pydantic schemas for file processing operations.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from decimal import Decimal

from pydantic import BaseModel, Field, ConfigDict

from ..models.file_processing import ProcessingStatus


class FileProcessingTaskBase(BaseModel):
    """Base schema for file processing tasks."""
    task_name: str = Field(..., description="Human-readable task name")
    task_type: str = Field(..., description="Type of processing task")
    platform: Optional[str] = Field(None, description="Poker platform")
    processing_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Processing options")


class FileProcessingTaskCreate(FileProcessingTaskBase):
    """Schema for creating file processing tasks."""
    user_id: str = Field(..., description="User ID")
    file_path: Optional[str] = Field(None, description="File path")
    file_size: Optional[int] = Field(None, description="File size in bytes")


class FileProcessingTaskUpdate(BaseModel):
    """Schema for updating file processing tasks."""
    status: Optional[ProcessingStatus] = None
    progress_percentage: Optional[int] = Field(None, ge=0, le=100)
    current_step: Optional[str] = None
    hands_processed: Optional[int] = Field(None, ge=0)
    hands_failed: Optional[int] = Field(None, ge=0)
    total_hands_expected: Optional[int] = Field(None, ge=0)
    error_message: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    result_summary: Optional[Dict[str, Any]] = None


class FileProcessingTaskResponse(BaseModel):
    """Schema for file processing task responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    task_name: str
    task_type: str
    file_path: Optional[str] = None
    file_size: Optional[int] = None
    platform: Optional[str] = None
    status: ProcessingStatus
    progress_percentage: int
    current_step: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    hands_processed: int
    hands_failed: int
    total_hands_expected: Optional[int] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[Decimal] = None
    hands_per_second: Optional[Decimal] = None
    created_at: datetime
    updated_at: datetime
    
    @property
    def is_active(self) -> bool:
        """Check if task is currently active."""
        return self.status in [ProcessingStatus.PENDING, ProcessingStatus.PROCESSING]
    
    @property
    def is_completed(self) -> bool:
        """Check if task has completed."""
        return self.status in [ProcessingStatus.COMPLETED, ProcessingStatus.FAILED, ProcessingStatus.CANCELLED]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of processed hands."""
        total_processed = self.hands_processed + self.hands_failed
        if total_processed == 0:
            return 0.0
        return (self.hands_processed / total_processed) * 100.0


class ProcessingProgressResponse(BaseModel):
    """Schema for processing progress responses."""
    task_id: str
    progress_percentage: int = Field(..., ge=0, le=100)
    current_step: str
    hands_processed: int = Field(..., ge=0)
    hands_failed: int = Field(..., ge=0)
    estimated_completion: Optional[datetime] = None
    processing_rate: Optional[float] = Field(None, description="Hands per second")
    is_active: bool
    success_rate: Optional[float] = Field(None, description="Success rate percentage")


class ProcessingStatistics(BaseModel):
    """Schema for processing statistics."""
    total_tasks: int = Field(..., ge=0)
    active_tasks: int = Field(..., ge=0)
    completed_tasks: int = Field(..., ge=0)
    failed_tasks: int = Field(..., ge=0)
    total_hands_processed: int = Field(..., ge=0)
    total_processing_time: float = Field(..., ge=0)
    average_processing_rate: Optional[float] = None


class BatchProcessingRequest(BaseModel):
    """Schema for batch processing requests."""
    file_paths: List[str] = Field(..., min_items=1, description="List of file paths to process")
    platform: Optional[str] = Field(None, description="Poker platform (auto-detected if not provided)")
    task_name: Optional[str] = Field(None, description="Custom task name")
    processing_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional processing options")


class SingleFileProcessingRequest(BaseModel):
    """Schema for single file processing requests."""
    file_path: str = Field(..., description="Path to file to process")
    platform: Optional[str] = Field(None, description="Poker platform (auto-detected if not provided)")
    task_name: Optional[str] = Field(None, description="Custom task name")
    processing_options: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional processing options")


class ProcessingTaskCreatedResponse(BaseModel):
    """Schema for task creation responses."""
    task_id: str
    message: str
    estimated_processing_time: Optional[str] = None


class ProcessingServiceStatus(BaseModel):
    """Schema for processing service status."""
    service_status: str
    active_tasks: int = Field(..., ge=0)
    queue_size: int = Field(..., ge=0)
    max_workers: int = Field(..., gt=0)
    recent_tasks: List[Dict[str, Any]] = Field(default_factory=list)


class SupportedFormatsResponse(BaseModel):
    """Schema for supported formats response."""
    platforms: List[str]
    file_extensions: List[str]
    max_file_size: str
    batch_processing: bool
    upload_processing: bool
    auto_platform_detection: bool
    progress_tracking: bool


class TaskCancellationResponse(BaseModel):
    """Schema for task cancellation responses."""
    message: str
    task_id: str


class UserTasksResponse(BaseModel):
    """Schema for user tasks list response."""
    tasks: List[Dict[str, Any]]
    total_tasks: int = Field(..., ge=0)
    active_tasks: int = Field(..., ge=0)
    completed_tasks: int = Field(..., ge=0)
    failed_tasks: int = Field(..., ge=0)