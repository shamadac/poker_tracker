"""
Pydantic schemas for education content API.
"""
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class DifficultyLevel(str, Enum):
    """Difficulty levels for education content."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ContentCategory(str, Enum):
    """Categories for education content."""
    BASIC = "basic"
    ADVANCED = "advanced"
    TOURNAMENT = "tournament"
    CASH_GAME = "cash_game"


class EducationContentBase(BaseModel):
    """Base schema for education content."""
    title: str = Field(..., min_length=1, max_length=255, description="Content title")
    slug: str = Field(..., min_length=1, max_length=255, description="URL-friendly slug")
    category: ContentCategory = Field(..., description="Content category")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    definition: str = Field(..., min_length=1, description="Brief definition")
    explanation: str = Field(..., min_length=1, description="Detailed explanation")
    examples: List[str] = Field(default_factory=list, description="Usage examples")
    related_stats: List[str] = Field(default_factory=list, description="Related statistics")
    video_url: Optional[str] = Field(None, max_length=500, description="Optional video URL")
    interactive_demo: bool = Field(default=False, description="Has interactive demo")
    tags: List[str] = Field(default_factory=list, description="Content tags")
    prerequisites: List[str] = Field(default_factory=list, description="Required knowledge")
    learning_objectives: List[str] = Field(default_factory=list, description="Learning goals")
    author: Optional[str] = Field(None, max_length=255, description="Content author")
    version: str = Field(default="1.0", max_length=50, description="Content version")
    is_published: bool = Field(default=True, description="Is content published")

    @validator('slug')
    def validate_slug(cls, v):
        """Validate slug format."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()

    @validator('video_url')
    def validate_video_url(cls, v):
        """Validate video URL format."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Video URL must start with http:// or https://')
        return v


class EducationContentCreate(EducationContentBase):
    """Schema for creating education content."""
    pass


class EducationContentUpdate(BaseModel):
    """Schema for updating education content."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[ContentCategory] = None
    difficulty: Optional[DifficultyLevel] = None
    definition: Optional[str] = Field(None, min_length=1)
    explanation: Optional[str] = Field(None, min_length=1)
    examples: Optional[List[str]] = None
    related_stats: Optional[List[str]] = None
    video_url: Optional[str] = Field(None, max_length=500)
    interactive_demo: Optional[bool] = None
    tags: Optional[List[str]] = None
    prerequisites: Optional[List[str]] = None
    learning_objectives: Optional[List[str]] = None
    author: Optional[str] = Field(None, max_length=255)
    version: Optional[str] = Field(None, max_length=50)
    is_published: Optional[bool] = None

    @validator('video_url')
    def validate_video_url(cls, v):
        """Validate video URL format."""
        if v and not (v.startswith('http://') or v.startswith('https://')):
            raise ValueError('Video URL must start with http:// or https://')
        return v


class EducationContentResponse(EducationContentBase):
    """Schema for education content responses."""
    id: str = Field(..., description="Content ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class EducationProgressBase(BaseModel):
    """Base schema for education progress."""
    is_read: bool = Field(default=False, description="Content has been read")
    is_bookmarked: bool = Field(default=False, description="Content is bookmarked")
    is_favorite: bool = Field(default=False, description="Content is favorited")
    time_spent_seconds: int = Field(default=0, ge=0, description="Time spent reading")
    user_notes: Optional[str] = Field(None, description="User's personal notes")


class EducationProgressCreate(EducationProgressBase):
    """Schema for creating education progress."""
    content_id: str = Field(..., description="Education content ID")


class EducationProgressUpdate(BaseModel):
    """Schema for updating education progress."""
    is_read: Optional[bool] = None
    is_bookmarked: Optional[bool] = None
    is_favorite: Optional[bool] = None
    time_spent_seconds: Optional[int] = Field(None, ge=0)
    user_notes: Optional[str] = None


class EducationProgressResponse(EducationProgressBase):
    """Schema for education progress responses."""
    id: str = Field(..., description="Progress ID")
    user_id: str = Field(..., description="User ID")
    content_id: str = Field(..., description="Content ID")
    last_accessed: Optional[datetime] = Field(None, description="Last access time")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    class Config:
        from_attributes = True


class EducationContentWithProgress(EducationContentResponse):
    """Schema for education content with user progress."""
    progress: Optional[EducationProgressResponse] = Field(None, description="User progress")


class EducationSearchFilters(BaseModel):
    """Schema for education content search filters."""
    category: Optional[ContentCategory] = Field(None, description="Filter by category")
    difficulty: Optional[DifficultyLevel] = Field(None, description="Filter by difficulty")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    search_query: Optional[str] = Field(None, min_length=1, description="Search in title/content")
    favorites_only: bool = Field(default=False, description="Show only favorited content")
    bookmarks_only: bool = Field(default=False, description="Show only bookmarked content")
    has_interactive_demo: Optional[bool] = Field(None, description="Filter by interactive demo availability")
    has_video: Optional[bool] = Field(None, description="Filter by video availability")
    is_published: bool = Field(default=True, description="Include only published content")
    sort_by: str = Field(default="title", description="Sort by field")
    sort_order: str = Field(default="asc", description="Sort order (asc/desc)")
    limit: int = Field(default=50, ge=1, le=100, description="Number of results")
    offset: int = Field(default=0, ge=0, description="Results offset")

    @validator('sort_by')
    def validate_sort_by(cls, v):
        """Validate sort_by field."""
        allowed_fields = ['title', 'difficulty', 'created_at', 'updated_at', 'category']
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of: {", ".join(allowed_fields)}')
        return v

    @validator('sort_order')
    def validate_sort_order(cls, v):
        """Validate sort_order field."""
        if v.lower() not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v.lower()


class EducationSearchResponse(BaseModel):
    """Schema for education content search results."""
    items: List[EducationContentWithProgress] = Field(..., description="Search results")
    total: int = Field(..., ge=0, description="Total number of results")
    limit: int = Field(..., ge=1, description="Results limit")
    offset: int = Field(..., ge=0, description="Results offset")
    has_more: bool = Field(..., description="More results available")


class EducationCategoryStats(BaseModel):
    """Schema for education category statistics."""
    category: ContentCategory = Field(..., description="Content category")
    total_content: int = Field(..., ge=0, description="Total content in category")
    by_difficulty: dict = Field(..., description="Content count by difficulty")
    user_progress: Optional[dict] = Field(None, description="User progress in category")


class EducationOverview(BaseModel):
    """Schema for education system overview."""
    total_content: int = Field(..., ge=0, description="Total education content")
    categories: List[EducationCategoryStats] = Field(..., description="Category breakdown")
    user_stats: Optional[dict] = Field(None, description="User-specific statistics")