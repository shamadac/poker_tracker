"""
Common Pydantic schemas used across multiple endpoints.
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime


class PaginationParams(BaseModel):
    """Common pagination parameters."""
    skip: int = Field(0, ge=0, description="Number of records to skip")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of records to return")


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Standard success response format."""
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")


class ValidationError(BaseModel):
    """Validation error details."""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    value: Optional[Any] = Field(None, description="Invalid value provided")


class TimestampMixin(BaseModel):
    """Mixin for models with timestamp fields."""
    created_at: datetime = Field(..., description="Record creation timestamp")
    updated_at: datetime = Field(..., description="Record last update timestamp")


class UUIDMixin(BaseModel):
    """Mixin for models with UUID primary key."""
    id: str = Field(..., description="Unique identifier")


class FileUploadResponse(BaseModel):
    """Response for file upload operations."""
    filename: str = Field(..., description="Name of uploaded file")
    size: int = Field(..., description="File size in bytes")
    content_type: str = Field(..., description="MIME type of uploaded file")
    processed: bool = Field(..., description="Whether file was successfully processed")
    records_created: int = Field(0, description="Number of records created from file")
    errors: List[str] = Field(default_factory=list, description="Processing errors if any")


class ExportRequest(BaseModel):
    """Request for data export operations."""
    format: str = Field(..., pattern="^(csv|pdf|json)$", description="Export format")
    filters: Optional[Dict[str, Any]] = Field(None, description="Filters to apply to exported data")
    include_raw_data: bool = Field(False, description="Whether to include raw data in export")
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v):
        allowed_formats = ['csv', 'pdf', 'json']
        if v not in allowed_formats:
            raise ValueError(f'Format must be one of: {", ".join(allowed_formats)}')
        return v


class DateRangeFilter(BaseModel):
    """Date range filter for queries."""
    start_date: Optional[datetime] = Field(None, description="Start date for filtering")
    end_date: Optional[datetime] = Field(None, description="End date for filtering")
    
    @model_validator(mode='after')
    def validate_date_range(self):
        if self.end_date and self.start_date:
            if self.end_date < self.start_date:
                raise ValueError('End date must be after start date')
        return self


class PlatformFilter(BaseModel):
    """Platform-specific filter."""
    platform: Optional[str] = Field(None, pattern="^(pokerstars|ggpoker)$", description="Poker platform")
    
    @field_validator('platform')
    @classmethod
    def validate_platform(cls, v):
        if v is not None:
            allowed_platforms = ['pokerstars', 'ggpoker']
            if v not in allowed_platforms:
                raise ValueError(f'Platform must be one of: {", ".join(allowed_platforms)}')
        return v


class GameTypeFilter(BaseModel):
    """Game type filter."""
    game_type: Optional[str] = Field(None, description="Game type (Hold'em, Omaha, etc.)")
    game_format: Optional[str] = Field(None, pattern="^(tournament|cash|sng)$", description="Game format")
    stakes: Optional[str] = Field(None, description="Stakes level")
    
    @field_validator('game_format')
    @classmethod
    def validate_game_format(cls, v):
        if v is not None:
            allowed_formats = ['tournament', 'cash', 'sng']
            if v not in allowed_formats:
                raise ValueError(f'Game format must be one of: {", ".join(allowed_formats)}')
        return v


class PositionFilter(BaseModel):
    """Position-based filter."""
    position: Optional[str] = Field(None, pattern="^(UTG|MP|CO|BTN|SB|BB)$", description="Table position")
    
    @field_validator('position')
    @classmethod
    def validate_position(cls, v):
        if v is not None:
            allowed_positions = ['UTG', 'MP', 'CO', 'BTN', 'SB', 'BB']
            if v not in allowed_positions:
                raise ValueError(f'Position must be one of: {", ".join(allowed_positions)}')
        return v