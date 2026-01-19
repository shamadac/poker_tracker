"""
Analysis-related Pydantic schemas.
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from .common import UUIDMixin, TimestampMixin


class AnalysisBase(BaseModel):
    """Base schema for analysis records."""
    ai_provider: str = Field(..., pattern="^(gemini|groq)$", description="AI provider used")
    prompt_version: Optional[str] = Field(None, description="Prompt template version")
    
    @field_validator('ai_provider')
    @classmethod
    def validate_ai_provider(cls, v):
        allowed_providers = ['gemini', 'groq']
        if v not in allowed_providers:
            raise ValueError(f'AI provider must be one of: {", ".join(allowed_providers)}')
        return v


class AnalysisCreate(AnalysisBase):
    """Schema for creating analysis records."""
    hand_id: str = Field(..., description="Hand ID being analyzed")
    analysis_text: Optional[str] = Field(None, description="Full analysis text")
    strengths: Optional[List[str]] = Field(None, description="Identified strengths")
    mistakes: Optional[List[str]] = Field(None, description="Identified mistakes")
    recommendations: Optional[List[str]] = Field(None, description="Improvement recommendations")
    confidence_score: Optional[Decimal] = Field(None, ge=0, le=1, description="AI confidence score")
    analysis_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional analysis data")


class AnalysisResponse(AnalysisBase, UUIDMixin, TimestampMixin):
    """Schema for analysis response data."""
    hand_id: str = Field(..., description="Hand ID that was analyzed")
    analysis_text: Optional[str] = Field(None, description="Full analysis text")
    strengths: Optional[List[str]] = Field(None, description="Identified strengths")
    mistakes: Optional[List[str]] = Field(None, description="Identified mistakes")
    recommendations: Optional[List[str]] = Field(None, description="Improvement recommendations")
    confidence_score: Optional[Decimal] = Field(None, description="AI confidence score")
    analysis_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional analysis data")
    
    model_config = ConfigDict(from_attributes=True)


class HandAnalysisRequest(BaseModel):
    """Schema for single hand analysis request."""
    hand_id: str = Field(..., description="Hand ID to analyze")
    ai_provider: str = Field(..., pattern="^(gemini|groq)$", description="AI provider to use")
    analysis_depth: str = Field("standard", pattern="^(basic|standard|advanced)$", description="Analysis depth")
    include_coaching: bool = Field(True, description="Include coaching recommendations")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus analysis on")
    
    @field_validator('ai_provider')
    @classmethod
    def validate_ai_provider(cls, v):
        allowed_providers = ['gemini', 'groq']
        if v not in allowed_providers:
            raise ValueError(f'AI provider must be one of: {", ".join(allowed_providers)}')
        return v
    
    @field_validator('analysis_depth')
    @classmethod
    def validate_analysis_depth(cls, v):
        allowed_depths = ['basic', 'standard', 'advanced']
        if v not in allowed_depths:
            raise ValueError(f'Analysis depth must be one of: {", ".join(allowed_depths)}')
        return v
    
    @field_validator('focus_areas')
    @classmethod
    def validate_focus_areas(cls, v):
        if v is not None:
            allowed_areas = [
                'preflop', 'postflop', 'betting', 'position', 'pot_odds',
                'bluffing', 'value_betting', 'hand_reading', 'bankroll'
            ]
            for area in v:
                if area not in allowed_areas:
                    raise ValueError(f'Focus area must be one of: {", ".join(allowed_areas)}')
        return v


class SessionAnalysisRequest(BaseModel):
    """Schema for session analysis request."""
    hand_ids: List[str] = Field(..., min_length=1, max_length=1000, description="Hand IDs to analyze")
    ai_provider: str = Field(..., pattern="^(gemini|groq)$", description="AI provider to use")
    analysis_type: str = Field("summary", pattern="^(summary|detailed|coaching)$", description="Analysis type")
    include_trends: bool = Field(True, description="Include trend analysis")
    focus_on_leaks: bool = Field(True, description="Focus on identifying leaks")
    
    @field_validator('ai_provider')
    @classmethod
    def validate_ai_provider(cls, v):
        allowed_providers = ['gemini', 'groq']
        if v not in allowed_providers:
            raise ValueError(f'AI provider must be one of: {", ".join(allowed_providers)}')
        return v
    
    @field_validator('analysis_type')
    @classmethod
    def validate_analysis_type(cls, v):
        allowed_types = ['summary', 'detailed', 'coaching']
        if v not in allowed_types:
            raise ValueError(f'Analysis type must be one of: {", ".join(allowed_types)}')
        return v


class AnalysisJobResponse(BaseModel):
    """Schema for analysis job creation response."""
    analysis_id: str = Field(..., description="Analysis job ID")
    status: str = Field(..., description="Job status")
    estimated_completion: Optional[datetime] = Field(None, description="Estimated completion time")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message")


class AnalysisStatusResponse(BaseModel):
    """Schema for analysis status check response."""
    analysis_id: str = Field(..., description="Analysis job ID")
    status: str = Field(..., pattern="^(pending|processing|completed|failed|cancelled)$", description="Job status")
    progress: int = Field(..., ge=0, le=100, description="Progress percentage")
    started_at: Optional[datetime] = Field(None, description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    result_available: bool = Field(False, description="Whether result is available")
    
    @field_validator('status')
    @classmethod
    def validate_status(cls, v):
        allowed_statuses = ['pending', 'processing', 'completed', 'failed', 'cancelled']
        if v not in allowed_statuses:
            raise ValueError(f'Status must be one of: {", ".join(allowed_statuses)}')
        return v


class AnalysisHistoryResponse(BaseModel):
    """Schema for analysis history response."""
    analyses: List[AnalysisResponse] = Field(..., description="List of analyses")
    total: int = Field(..., ge=0, description="Total number of analyses")
    hand_id: str = Field(..., description="Hand ID")
    providers_used: List[str] = Field(..., description="AI providers used for this hand")


class SessionAnalysisResponse(BaseModel):
    """Schema for session analysis response."""
    session_id: str = Field(..., description="Session analysis ID")
    hand_count: int = Field(..., ge=1, description="Number of hands analyzed")
    ai_provider: str = Field(..., description="AI provider used")
    analysis_type: str = Field(..., description="Type of analysis performed")
    
    # Session summary
    session_summary: Dict[str, Any] = Field(..., description="Overall session summary")
    key_insights: List[str] = Field(..., description="Key insights from the session")
    major_leaks: List[str] = Field(..., description="Major leaks identified")
    strengths: List[str] = Field(..., description="Strengths identified")
    recommendations: List[str] = Field(..., description="Improvement recommendations")
    
    # Statistical analysis
    session_stats: Dict[str, Any] = Field(..., description="Session statistics")
    trend_analysis: Optional[Dict[str, Any]] = Field(None, description="Trend analysis if requested")
    
    # Individual hand highlights
    best_hands: List[Dict[str, Any]] = Field(..., description="Best played hands")
    worst_hands: List[Dict[str, Any]] = Field(..., description="Worst played hands")
    learning_hands: List[Dict[str, Any]] = Field(..., description="Hands with learning opportunities")
    
    # Metadata
    analysis_metadata: Dict[str, Any] = Field(..., description="Analysis metadata")
    created_at: datetime = Field(..., description="Analysis creation time")


class AnalysisComparisonRequest(BaseModel):
    """Schema for comparing analyses from different providers."""
    hand_id: str = Field(..., description="Hand ID to compare analyses for")
    providers: List[str] = Field(..., min_length=2, max_length=2, description="Providers to compare")
    
    @field_validator('providers')
    @classmethod
    def validate_providers(cls, v):
        allowed_providers = ['gemini', 'groq']
        for provider in v:
            if provider not in allowed_providers:
                raise ValueError(f'Provider must be one of: {", ".join(allowed_providers)}')
        if len(set(v)) != len(v):
            raise ValueError('Providers must be unique')
        return v


class AnalysisComparisonResponse(BaseModel):
    """Schema for analysis comparison response."""
    hand_id: str = Field(..., description="Hand ID compared")
    analyses: Dict[str, AnalysisResponse] = Field(..., description="Analyses by provider")
    comparison: Dict[str, Any] = Field(..., description="Comparison analysis")
    consensus_points: List[str] = Field(..., description="Points where analyses agree")
    differences: List[Dict[str, Any]] = Field(..., description="Key differences between analyses")
    recommendation: str = Field(..., description="Which analysis to prioritize and why")


class AnalysisFeedbackRequest(BaseModel):
    """Schema for providing feedback on analysis quality."""
    analysis_id: str = Field(..., description="Analysis ID to provide feedback for")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5")
    feedback_text: Optional[str] = Field(None, max_length=1000, description="Detailed feedback")
    helpful_aspects: Optional[List[str]] = Field(None, description="What was helpful")
    improvement_suggestions: Optional[List[str]] = Field(None, description="Suggestions for improvement")


class AnalysisFeedbackResponse(BaseModel):
    """Schema for analysis feedback response."""
    message: str = Field(..., description="Feedback submission confirmation")
    analysis_id: str = Field(..., description="Analysis ID feedback was provided for")
    submitted_at: datetime = Field(..., description="Feedback submission time")