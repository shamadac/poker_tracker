"""
User model for authentication and user management.
"""
from typing import Dict, Any, Optional

from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, UUIDMixin, TimestampMixin


class User(Base, UUIDMixin, TimestampMixin):
    """User model for storing user accounts and preferences."""
    
    __tablename__ = "users"
    
    # Basic user information
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        nullable=False,
        index=True
    )
    
    password_hash: Mapped[str] = mapped_column(
        String(255), 
        nullable=False
    )
    
    # Encrypted API keys for AI providers
    api_keys: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Encrypted API keys for Gemini and Groq providers"
    )
    
    # Hand history directory paths for different platforms
    hand_history_paths: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Directory paths for PokerStars and GGPoker hand histories"
    )
    
    # User preferences and settings
    preferences: Mapped[Dict[str, Any]] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        comment="User preferences including UI settings and analysis options"
    )
    
    # Relationships
    poker_hands = relationship("PokerHand", back_populates="user", cascade="all, delete-orphan")
    statistics_cache = relationship("StatisticsCache", back_populates="user", cascade="all, delete-orphan")
    file_monitoring = relationship("FileMonitoring", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"