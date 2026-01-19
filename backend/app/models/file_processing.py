"""
File processing models for tracking background file processing tasks.
"""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from enum import Enum

from sqlalchemy import (
    String, Text, Integer, DateTime, 
    DECIMAL, ForeignKey, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class ProcessingStatus(str, Enum):
    """File processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class FileProcessingTask(Base, UUIDMixin, TimestampMixin):
    """Model for tracking background file processing tasks."""
    
    __tablename__ = "file_processing_tasks"
    
    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Task identification
    task_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Human-readable task name"
    )
    
    task_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of processing: file_parse, batch_import, etc."
    )
    
    # File information
    file_path: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Path to file being processed"
    )
    
    file_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="File size in bytes"
    )
    
    platform: Mapped[Optional[str]] = mapped_column(
        String(20),
        comment="Poker platform: pokerstars, ggpoker"
    )
    
    # Processing status and progress
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="Status: pending, processing, completed, failed, cancelled"
    )
    
    progress_percentage: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Progress percentage (0-100)"
    )
    
    current_step: Mapped[Optional[str]] = mapped_column(
        String(200),
        comment="Current processing step description"
    )
    
    # Timing information
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="When processing started"
    )
    
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="When processing completed"
    )
    
    estimated_completion: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="Estimated completion time"
    )
    
    # Results and statistics
    hands_processed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of hands successfully processed"
    )
    
    hands_failed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of hands that failed processing"
    )
    
    total_hands_expected: Mapped[Optional[int]] = mapped_column(
        Integer,
        comment="Expected total number of hands to process"
    )
    
    # Error information
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        comment="Error message if processing failed"
    )
    
    error_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Detailed error information and stack trace"
    )
    
    # Processing metadata
    processing_options: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Processing configuration and options"
    )
    
    result_summary: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        comment="Summary of processing results"
    )
    
    # Performance metrics
    processing_time_seconds: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 3),
        comment="Total processing time in seconds"
    )
    
    hands_per_second: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 3),
        comment="Processing rate in hands per second"
    )
    
    # Relationships
    user = relationship("User", back_populates="file_processing_tasks")
    
    # Indexes
    __table_args__ = (
        Index("idx_file_processing_user_status", "user_id", "status"),
        Index("idx_file_processing_task_type", "task_type"),
        Index("idx_file_processing_created", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<FileProcessingTask(id={self.id}, task_name={self.task_name}, status={self.status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if task is currently active (pending or processing)."""
        return self.status in ["pending", "processing"]
    
    @property
    def is_completed(self) -> bool:
        """Check if task has completed (successfully or with failure)."""
        return self.status in ["completed", "failed", "cancelled"]
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of processed hands."""
        total_processed = self.hands_processed + self.hands_failed
        if total_processed == 0:
            return 0.0
        return (self.hands_processed / total_processed) * 100.0
    
    def update_progress(self, 
                       progress_percentage: int, 
                       current_step: Optional[str] = None,
                       hands_processed: Optional[int] = None,
                       hands_failed: Optional[int] = None) -> None:
        """Update task progress information."""
        self.progress_percentage = max(0, min(100, progress_percentage))
        
        if current_step is not None:
            self.current_step = current_step
        
        if hands_processed is not None:
            self.hands_processed = hands_processed
        
        if hands_failed is not None:
            self.hands_failed = hands_failed
        
        # Update estimated completion if we have enough data
        if (self.started_at and 
            self.total_hands_expected and 
            self.hands_processed > 0 and 
            progress_percentage > 0):
            
            elapsed = (datetime.now(timezone.utc) - self.started_at).total_seconds()
            estimated_total_time = elapsed * (100 / progress_percentage)
            self.estimated_completion = self.started_at + datetime.timedelta(seconds=estimated_total_time)