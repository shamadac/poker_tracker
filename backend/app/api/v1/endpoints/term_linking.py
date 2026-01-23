"""
Term Linking API endpoints for educational content integration.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from ....core.deps import get_db, get_current_user
from ....models.user import User
from ....services.term_linking_service import TermLinkingService, TermDefinition, LinkedContent

logger = logging.getLogger(__name__)
router = APIRouter()


class TermDefinitionResponse(BaseModel):
    """Response model for term definitions."""
    term: str
    definition: str
    explanation: Optional[str] = None
    source_type: str
    source_id: str
    context_appropriate: bool = True
    difficulty_level: Optional[str] = None
    category: Optional[str] = None


class TermLinkResponse(BaseModel):
    """Response model for term links."""
    term: str
    start_position: int
    end_position: int
    definition: TermDefinitionResponse
    confidence: float


class LinkedContentResponse(BaseModel):
    """Response model for linked content."""
    original_content: str
    linked_content: str
    detected_terms: List[TermLinkResponse]
    link_count: int


class LinkContentRequest(BaseModel):
    """Request model for linking content."""
    content: str = Field(..., description="Content to analyze for term links")
    context: Optional[str] = Field(None, description="Context for term selection (e.g., 'analysis', 'dashboard')")
    max_links: int = Field(10, ge=1, le=50, description="Maximum number of terms to link")


class TermLookupRequest(BaseModel):
    """Request model for term lookup."""
    term: str = Field(..., description="Term to look up")
    context: Optional[str] = Field(None, description="Context for definition selection")


@router.post(
    "/link-content",
    response_model=LinkedContentResponse,
    summary="Link terms in content",
    description="Detect and link poker terms in provided content"
)
async def link_terms_in_content(
    request: LinkContentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Detect and link poker terms in provided content."""
    try:
        term_service = TermLinkingService(db)
        
        linked_content = await term_service.detect_terms_in_content(
            content=request.content,
            context=request.context,
            max_links=request.max_links
        )
        
        # Convert to response format
        detected_terms = [
            TermLinkResponse(
                term=term_link.term,
                start_position=term_link.start_position,
                end_position=term_link.end_position,
                definition=TermDefinitionResponse(
                    term=term_link.definition.term,
                    definition=term_link.definition.definition,
                    explanation=term_link.definition.explanation,
                    source_type=term_link.definition.source_type,
                    source_id=term_link.definition.source_id,
                    context_appropriate=term_link.definition.context_appropriate,
                    difficulty_level=term_link.definition.difficulty_level,
                    category=term_link.definition.category
                ),
                confidence=term_link.confidence
            )
            for term_link in linked_content.detected_terms
        ]
        
        return LinkedContentResponse(
            original_content=linked_content.original_content,
            linked_content=linked_content.linked_content,
            detected_terms=detected_terms,
            link_count=linked_content.link_count
        )
        
    except Exception as e:
        logger.error(f"Failed to link terms in content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process content for term linking"
        )


@router.post(
    "/lookup-term",
    response_model=Optional[TermDefinitionResponse],
    summary="Look up term definition",
    description="Get definition for a specific poker term"
)
async def lookup_term_definition(
    request: TermLookupRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get definition for a specific poker term."""
    try:
        term_service = TermLinkingService(db)
        
        definition = await term_service.get_term_definition(
            term=request.term,
            context=request.context
        )
        
        if not definition:
            return None
        
        return TermDefinitionResponse(
            term=definition.term,
            definition=definition.definition,
            explanation=definition.explanation,
            source_type=definition.source_type,
            source_id=definition.source_id,
            context_appropriate=definition.context_appropriate,
            difficulty_level=definition.difficulty_level,
            category=definition.category
        )
        
    except Exception as e:
        logger.error(f"Failed to lookup term definition: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to lookup term definition"
        )


@router.get(
    "/related-terms/{term}",
    response_model=List[TermDefinitionResponse],
    summary="Get related terms",
    description="Get terms related to the specified term"
)
async def get_related_terms(
    term: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of related terms"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get terms related to the specified term."""
    try:
        term_service = TermLinkingService(db)
        
        related_terms = await term_service.get_related_terms(
            term=term,
            limit=limit
        )
        
        return [
            TermDefinitionResponse(
                term=definition.term,
                definition=definition.definition,
                explanation=definition.explanation,
                source_type=definition.source_type,
                source_id=definition.source_id,
                context_appropriate=definition.context_appropriate,
                difficulty_level=definition.difficulty_level,
                category=definition.category
            )
            for definition in related_terms
        ]
        
    except Exception as e:
        logger.error(f"Failed to get related terms: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get related terms"
        )


@router.get(
    "/suggestions",
    response_model=List[str],
    summary="Get term suggestions",
    description="Get term suggestions based on partial input"
)
async def get_term_suggestions(
    partial_term: str = Query(..., min_length=2, description="Partial term to match"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get term suggestions based on partial input."""
    try:
        term_service = TermLinkingService(db)
        
        suggestions = await term_service.get_term_suggestions(
            partial_term=partial_term,
            limit=limit
        )
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Failed to get term suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get term suggestions"
        )


@router.post(
    "/refresh-cache",
    summary="Refresh term cache",
    description="Refresh the term linking cache with latest data"
)
async def refresh_term_cache(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Refresh the term linking cache with latest data."""
    try:
        # Check if user has admin permissions
        if not current_user.has_resource_permission("encyclopedia", "admin"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to refresh term cache"
            )
        
        term_service = TermLinkingService(db)
        await term_service.refresh_cache()
        
        return {"message": "Term cache refreshed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to refresh term cache: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refresh term cache"
        )