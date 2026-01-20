"""
Education content database models.
"""
from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.sql import func
import uuid
import enum

from .base import Base


class DifficultyLevel(str, enum.Enum):
    """Difficulty levels for education content."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ContentCategory(str, enum.Enum):
    """Categories for education content."""
    BASIC = "basic"
    ADVANCED = "advanced"
    TOURNAMENT = "tournament"
    CASH_GAME = "cash_game"


class EducationContent(Base):
    """
    Education content model for poker statistics encyclopedia.
    
    Stores comprehensive educational content about poker concepts,
    statistics, and strategies organized by difficulty and category.
    """
    __tablename__ = "education_content"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    category = Column(Enum(ContentCategory), nullable=False, index=True)
    difficulty = Column(Enum(DifficultyLevel), nullable=False, index=True)
    
    # Core content
    definition = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    examples = Column(ARRAY(Text), nullable=False, default=[])
    related_stats = Column(ARRAY(String), nullable=False, default=[])
    
    # Optional multimedia content
    video_url = Column(String(500), nullable=True)
    interactive_demo = Column(Boolean, default=False)
    
    # Additional metadata
    tags = Column(ARRAY(String), nullable=False, default=[])
    prerequisites = Column(ARRAY(String), nullable=False, default=[])
    learning_objectives = Column(ARRAY(Text), nullable=False, default=[])
    
    # Content metadata
    author = Column(String(255), nullable=True)
    version = Column(String(50), default="1.0")
    is_published = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<EducationContent(id={self.id}, title='{self.title}', category='{self.category}')>"


class EducationProgress(Base):
    """
    Track user progress through education content.
    
    Allows users to mark content as read, favorite, or bookmark
    for later review.
    """
    __tablename__ = "education_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    content_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Progress tracking
    is_read = Column(Boolean, default=False)
    is_bookmarked = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    
    # Engagement metrics
    time_spent_seconds = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    # User notes
    user_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<EducationProgress(user_id={self.user_id}, content_id={self.content_id})>"