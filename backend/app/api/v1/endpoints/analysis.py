"""
AI analysis endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.schemas.analysis import (
    HandAnalysisRequest,
    SessionAnalysisRequest,
    AnalysisJobResponse,
    AnalysisResponse,
    AnalysisHistoryResponse,
    AnalysisStatusResponse,
    AnalysisComparisonRequest,
    AnalysisComparisonResponse,
    AnalysisFeedbackRequest,
    AnalysisFeedbackResponse,
    SessionAnalysisResponse
)
from app.schemas.common import ErrorResponse, SuccessResponse
from app.models.user import User

router = APIRouter()


@router.post("/hand", response_model=AnalysisJobResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def analyze_hand(
    request: HandAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AnalysisJobResponse:
    """
    Analyze a single poker hand using AI.
    
    - **hand_id**: ID of the hand to analyze
    - **ai_provider**: AI provider to use (gemini or groq)
    - **analysis_depth**: Depth of analysis (basic, standard, advanced)
    - **include_coaching**: Whether to include coaching recommendations
    - **focus_areas**: Specific areas to focus the analysis on
    """
    # TODO: Implement hand analysis
    return AnalysisJobResponse(
        analysis_id="placeholder",
        status="processing",
        progress=0,
        message="Analysis job created successfully"
    )


@router.post("/session", response_model=AnalysisJobResponse, responses={400: {"model": ErrorResponse}})
async def analyze_session(
    request: SessionAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AnalysisJobResponse:
    """
    Analyze multiple hands for session insights.
    
    - **hand_ids**: List of hand IDs to analyze (1-1000 hands)
    - **ai_provider**: AI provider to use (gemini or groq)
    - **analysis_type**: Type of analysis (summary, detailed, coaching)
    - **include_trends**: Whether to include trend analysis
    - **focus_on_leaks**: Whether to focus on identifying leaks
    """
    # TODO: Implement session analysis
    return AnalysisJobResponse(
        analysis_id="placeholder",
        status="processing",
        progress=0,
        message=f"Session analysis job created for {len(request.hand_ids)} hands"
    )


@router.get("/status/{analysis_id}", response_model=AnalysisStatusResponse, responses={404: {"model": ErrorResponse}})
async def get_analysis_status(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AnalysisStatusResponse:
    """
    Get analysis job status and progress.
    
    - **analysis_id**: ID of the analysis job
    """
    # TODO: Implement analysis status retrieval
    return AnalysisStatusResponse(
        analysis_id=analysis_id,
        status="completed",
        progress=100,
        result_available=True
    )


@router.get("/result/{analysis_id}", response_model=AnalysisResponse, responses={404: {"model": ErrorResponse}})
async def get_analysis_result(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AnalysisResponse:
    """
    Get completed analysis result.
    
    - **analysis_id**: ID of the completed analysis
    """
    # TODO: Implement analysis result retrieval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Analysis not found"
    )


@router.get("/session/result/{analysis_id}", response_model=SessionAnalysisResponse, responses={404: {"model": ErrorResponse}})
async def get_session_analysis_result(
    analysis_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> SessionAnalysisResponse:
    """
    Get completed session analysis result.
    
    - **analysis_id**: ID of the completed session analysis
    """
    # TODO: Implement session analysis result retrieval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Session analysis not found"
    )


@router.get("/hand/{hand_id}/history", response_model=AnalysisHistoryResponse, responses={404: {"model": ErrorResponse}})
async def get_hand_analysis_history(
    hand_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AnalysisHistoryResponse:
    """
    Get all analysis history for a specific hand.
    
    - **hand_id**: ID of the hand to get analysis history for
    """
    # TODO: Implement analysis history retrieval
    return AnalysisHistoryResponse(
        analyses=[],
        total=0,
        hand_id=hand_id,
        providers_used=[]
    )


@router.post("/compare", response_model=AnalysisComparisonResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def compare_analyses(
    request: AnalysisComparisonRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AnalysisComparisonResponse:
    """
    Compare analyses from different AI providers for the same hand.
    
    - **hand_id**: Hand ID to compare analyses for
    - **providers**: List of exactly 2 providers to compare
    """
    # TODO: Implement analysis comparison
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Analyses not found for comparison"
    )


@router.post("/feedback", response_model=AnalysisFeedbackResponse, responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}})
async def submit_analysis_feedback(
    request: AnalysisFeedbackRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> AnalysisFeedbackResponse:
    """
    Submit feedback on analysis quality.
    
    - **analysis_id**: ID of the analysis to provide feedback for
    - **rating**: Rating from 1-5
    - **feedback_text**: Optional detailed feedback
    - **helpful_aspects**: What aspects were helpful
    - **improvement_suggestions**: Suggestions for improvement
    """
    # TODO: Implement feedback submission
    from datetime import datetime
    return AnalysisFeedbackResponse(
        message="Feedback submitted successfully",
        analysis_id=request.analysis_id,
        submitted_at=datetime.utcnow()
    )