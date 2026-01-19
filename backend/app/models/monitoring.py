"""
File monitoring model for tracking hand history directory monitoring.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, DateTime, Integer, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class FileMonitoring(Base, UUIDMixin, TimestampMixin):
    """Model for tracking file monitoring configuration and status."""
    
    __tablename__ = "file_monitoring"
    
    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Platform and directory information
    platform: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Poker platform: pokerstars, ggpoker"
    )
    
    directory_path: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Path to hand history directory being monitored"
    )
    
    # Monitoring status
    last_scan: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        comment="Last time directory was scanned"
    )
    
    file_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of files found in last scan"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether monitoring is currently active"
    )
    
    # Relationships
    user = relationship("User", back_populates="file_monitoring")
    
    # Indexes
    __table_args__ = (
        Index("idx_file_monitoring_user_platform", "user_id", "platform"),
        Index("idx_file_monitoring_active", "is_active"),
    )
    
    def __repr__(self) -> str:
        return f"<FileMonitoring(id={self.id}, user_id={self.user_id}, platform={self.platform})>"