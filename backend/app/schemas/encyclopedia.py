"""
Pydantic schemas for encyclopedia API endpoints.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from ..models.encyclopedia import EncyclopediaStatus, AIProvider


class EncyclopediaEntryBase(BaseModel):
    """Base schema for encyclopedia entries."""
    title: str = Field(..., min_length=1, max_length=255, description="Entry title")
    content: str = Field(..., min_length=1, description="Entry content")


class EncyclopediaEntryCreate(BaseModel):
    """Schema for creating encyclopedia entries."""
    title: str = Field(..., min_length=1, max_length=255, description="Entry title")
    initial_prompt: str = Field(..., min_length=1, description="Initial prompt for AI content generation")
    ai_provider: AIProvider = Field(..., description="AI provider to use for content generation")


class EncyclopediaEntryRefine(BaseModel):
    """Schema for refining encyclopedia entries."""
    refinement_prompt: str = Field(..., min_length=1, description="Prompt for content refinement")
    ai_provider: AIProvider = Field(..., description="AI provider to use for refinement")


class EncyclopediaEntryApprove(BaseModel):
    """Schema for approving encyclopedia entries."""
    pass  # No additional fields needed, approval is based on user permissions


class EncyclopediaConversationResponse(BaseModel):
    """Schema for encyclopedia conversation responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    prompt: str
    response: str
    ai_provider: str
    conversation_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime


class EncyclopediaLinkResponse(BaseModel):
    """Schema for encyclopedia link responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    source_entry_id: str
    target_entry_id: str
    anchor_text: str
    context: Optional[str] = None
    created_at: datetime


class EncyclopediaEntryResponse(BaseModel):
    """Schema for encyclopedia entry responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    title: str
    content: str
    status: EncyclopediaStatus
    ai_provider: str
    created_by: str
    approved_by: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Optional related data
    conversations: Optional[List[EncyclopediaConversationResponse]] = None
    source_links: Optional[List[EncyclopediaLinkResponse]] = None
    target_links: Optional[List[EncyclopediaLinkResponse]] = None


class EncyclopediaEntryListResponse(BaseModel):
    """Schema for encyclopedia entry list responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    title: str
    status: EncyclopediaStatus
    ai_provider: str
    created_by: str
    approved_by: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TopicSuggestionResponse(BaseModel):
    """Schema for topic suggestion responses."""
    title: str = Field(..., description="Suggested topic title")
    description: str = Field(..., description="Description of why this topic is important")


class TopicSuggestionsRequest(BaseModel):
    """Schema for requesting topic suggestions."""
    ai_provider: AIProvider = Field(..., description="AI provider to use for suggestions")
    limit: int = Field(default=10, ge=1, le=50, description="Maximum number of suggestions")


class GenerateLinksRequest(BaseModel):
    """Schema for generating entry links."""
    ai_provider: AIProvider = Field(..., description="AI provider to use for link generation")


class EncyclopediaSearchRequest(BaseModel):
    """Schema for encyclopedia search requests."""
    query: str = Field(..., min_length=1, description="Search query")
    status_filter: Optional[EncyclopediaStatus] = Field(None, description="Optional status filter")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of results")


class EncyclopediaSearchResponse(BaseModel):
    """Schema for encyclopedia search responses."""
    entries: List[EncyclopediaEntryListResponse]
    total_count: int = Field(..., description="Total number of matching entries")
    query: str = Field(..., description="The search query used")


class EncyclopediaStatsResponse(BaseModel):
    """Schema for encyclopedia statistics."""
    total_entries: int
    published_entries: int
    draft_entries: int
    archived_entries: int
    total_conversations: int
    total_links: int
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list)


# Error response schemas
class EncyclopediaErrorResponse(BaseModel):
    """Schema for encyclopedia error responses."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    error_code: Optional[str] = Field(None, description="Error code for client handling")


# Bulk operation schemas
class BulkApprovalRequest(BaseModel):
    """Schema for bulk approval operations."""
    entry_ids: List[str] = Field(..., min_items=1, description="List of entry IDs to approve")


class BulkApprovalResponse(BaseModel):
    """Schema for bulk approval responses."""
    approved_count: int = Field(..., description="Number of entries successfully approved")
    failed_entries: List[Dict[str, str]] = Field(default_factory=list, description="Entries that failed to approve")


class EncyclopediaActivityResponse(BaseModel):
    """Schema for encyclopedia activity responses."""
    entry_id: str
    entry_title: str
    activity_type: str  # 'created', 'refined', 'approved', 'published'
    user_id: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


# Admin-specific schemas
class EncyclopediaAdminStatsResponse(BaseModel):
    """Schema for admin encyclopedia statistics."""
    total_entries: int
    entries_by_status: Dict[str, int]
    entries_by_provider: Dict[str, int]
    recent_entries: List[EncyclopediaEntryListResponse]
    top_contributors: List[Dict[str, Any]]
    conversation_stats: Dict[str, int]
    link_stats: Dict[str, int]


class ContentGenerationMetrics(BaseModel):
    """Schema for content generation metrics."""
    total_generations: int
    successful_generations: int
    failed_generations: int
    average_response_time: float
    provider_usage: Dict[str, int]
    token_usage: Dict[str, int]