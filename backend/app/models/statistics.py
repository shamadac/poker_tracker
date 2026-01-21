"""
Statistics cache model for storing computed poker statistics.
"""
from datetime import datetime
from typing import Dict, Any

from sqlalchemy import String, ForeignKey, DateTime, UniqueConstraint, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class StatisticsCache(Base, UUIDMixin, TimestampMixin):
    """Model for caching computed poker statistics."""
    
    __tablename__ = "statistics_cache"
    
    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Cache identification
    cache_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Unique cache key based on filters and parameters"
    )
    
    stat_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of statistics: basic, advanced, tournament, etc."
    )
    
    # Cached data
    data: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Cached statistics data"
    )
    
    # Cache expiration
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="When this cache entry expires"
    )
    
    # Relationships
    user = relationship("User", back_populates="statistics_cache")
    
    # Constraints and indexes
    __table_args__ = (
        UniqueConstraint("user_id", "cache_key", name="uq_user_cache_key"),
        Index("idx_statistics_cache_user_type", "user_id", "stat_type"),
        Index("idx_statistics_cache_expires", "expires_at"),
    )
    
    def __repr__(self) -> str:
        return f"<StatisticsCache(id={self.id}, user_id={self.user_id}, stat_type={self.stat_type})>"