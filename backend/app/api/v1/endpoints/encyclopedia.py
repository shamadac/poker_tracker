"""
Encyclopedia API endpoints for AI-powered content management.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.deps import get_db, get_current_user
from ....models.user import User
from ....models.encyclopedia import EncyclopediaStatus, AIProvider
from ....services.encyclopedia_service import EncyclopediaService
from ....schemas.encyclopedia import (
    EncyclopediaEntryCreate,
    EncyclopediaEntryRefine,
    EncyclopediaEntryApprove,
    EncyclopediaEntryResponse,
    EncyclopediaEntryListResponse,
    TopicSuggestionResponse,
    TopicSuggestionsRequest,
    GenerateLinksRequest,
    EncyclopediaSearchRequest,
    EncyclopediaSearchResponse,
    EncyclopediaStatsResponse,
    EncyclopediaErrorResponse,
    BulkApprovalRequest,
    BulkApprovalResponse,
    EncyclopediaAdminStatsResponse
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/entries",
    response_model=EncyclopediaEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create encyclopedia entry",
    description="Create a new encyclopedia entry with AI-generated content"
)
async def create_encyclopedia_entry(
    entry_data: EncyclopediaEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new encyclopedia entry with AI-generated content."""
    try:
        # Check if user has permission to create encyclopedia entries
        if not current_user.has_resource_permission("encyclopedia", "create"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to create encyclopedia entries"
            )
        
        # Get user's API key for the specified provider
        encyclopedia_service = EncyclopediaService(db)
        api_key = await encyclopedia_service.get_api_key(current_user.id, entry_data.ai_provider.value)
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No API key configured for {entry_data.ai_provider.value}"
            )
        
        # Create the encyclopedia entry
        entry, content = await encyclopedia_service.create_entry(
            title=entry_data.title,
            initial_prompt=entry_data.initial_prompt,
            ai_provider=entry_data.ai_provider,
            created_by=current_user.id,
            api_key=api_key
        )
        
        return EncyclopediaEntryResponse.model_validate(entry)
        
    except ValueError as e:
        logger.error(f"Failed to create encyclopedia entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error creating encyclopedia entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create encyclopedia entry"
        )


@router.put(
    "/entries/{entry_id}/refine",
    response_model=EncyclopediaEntryResponse,
    summary="Refine encyclopedia entry",
    description="Refine existing encyclopedia content using AI conversation"
)
async def refine_encyclopedia_entry(
    entry_id: str,
    refinement_data: EncyclopediaEntryRefine,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Refine existing encyclopedia content using AI conversation."""
    try:
        # Check permissions
        if not current_user.has_resource_permission("encyclopedia", "edit"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to edit encyclopedia entries"
            )
        
        # Get API key
        encyclopedia_service = EncyclopediaService(db)
        api_key = await encyclopedia_service.get_api_key(current_user.id, refinement_data.ai_provider.value)
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No API key configured for {refinement_data.ai_provider.value}"
            )
        
        # Refine the content
        content, conversation = await encyclopedia_service.refine_content(
            entry_id=entry_id,
            refinement_prompt=refinement_data.refinement_prompt,
            ai_provider=refinement_data.ai_provider,
            api_key=api_key
        )
        
        # Get updated entry
        entry = await encyclopedia_service.get_entry_with_links(entry_id)
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Encyclopedia entry not found"
            )
        
        return EncyclopediaEntryResponse.model_validate(entry)
        
    except ValueError as e:
        logger.error(f"Failed to refine encyclopedia entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error refining encyclopedia entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to refine encyclopedia entry"
        )


@router.put(
    "/entries/{entry_id}/approve",
    response_model=EncyclopediaEntryResponse,
    summary="Approve encyclopedia entry",
    description="Approve an encyclopedia entry for publication"
)
async def approve_encyclopedia_entry(
    entry_id: str,
    approval_data: EncyclopediaEntryApprove,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve an encyclopedia entry for publication."""
    try:
        # Check permissions
        if not current_user.has_resource_permission("encyclopedia", "approve"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to approve encyclopedia entries"
            )
        
        # Approve the entry
        encyclopedia_service = EncyclopediaService(db)
        entry = await encyclopedia_service.approve_entry(
            entry_id=entry_id,
            approved_by=current_user.id
        )
        
        return EncyclopediaEntryResponse.model_validate(entry)
        
    except ValueError as e:
        logger.error(f"Failed to approve encyclopedia entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error approving encyclopedia entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve encyclopedia entry"
        )


@router.get(
    "/entries/{entry_id}",
    response_model=EncyclopediaEntryResponse,
    summary="Get encyclopedia entry",
    description="Get a specific encyclopedia entry with its links and conversations"
)
async def get_encyclopedia_entry(
    entry_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific encyclopedia entry with its links and conversations."""
    try:
        encyclopedia_service = EncyclopediaService(db)
        entry = await encyclopedia_service.get_entry_with_links(entry_id)
        
        if not entry:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Encyclopedia entry not found"
            )
        
        # Check if user can view this entry
        if entry.status != EncyclopediaStatus.PUBLISHED:
            if not current_user.has_resource_permission("encyclopedia", "view_drafts"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view draft entries"
                )
        
        return EncyclopediaEntryResponse.model_validate(entry)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting encyclopedia entry: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get encyclopedia entry"
        )


@router.get(
    "/entries",
    response_model=List[EncyclopediaEntryListResponse],
    summary="List encyclopedia entries",
    description="List encyclopedia entries with optional filtering"
)
async def list_encyclopedia_entries(
    status_filter: Optional[EncyclopediaStatus] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of entries"),
    offset: int = Query(0, ge=0, description="Number of entries to skip"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List encyclopedia entries with optional filtering."""
    try:
        encyclopedia_service = EncyclopediaService(db)
        
        # If no status filter and user can't view drafts, only show published
        if status_filter is None and not current_user.has_resource_permission("encyclopedia", "view_drafts"):
            status_filter = EncyclopediaStatus.PUBLISHED
        
        # For now, use search with empty query to get all entries
        # In a full implementation, would add a dedicated list method
        entries = await encyclopedia_service.search_entries(
            query="",
            status_filter=status_filter,
            limit=limit
        )
        
        return [EncyclopediaEntryListResponse.model_validate(entry) for entry in entries]
        
    except Exception as e:
        logger.error(f"Unexpected error listing encyclopedia entries: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list encyclopedia entries"
        )


@router.post(
    "/suggestions",
    response_model=List[TopicSuggestionResponse],
    summary="Generate topic suggestions",
    description="Generate topic suggestions based on content gaps"
)
async def generate_topic_suggestions(
    request: TopicSuggestionsRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate topic suggestions based on content gaps in the encyclopedia."""
    try:
        # Check permissions
        if not current_user.has_resource_permission("encyclopedia", "suggest_topics"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to generate topic suggestions"
            )
        
        # Get API key
        encyclopedia_service = EncyclopediaService(db)
        api_key = await encyclopedia_service.get_api_key(current_user.id, request.ai_provider.value)
        
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No API key configured for {request.ai_provider.value}"
            )
        
        # Generate suggestions
        suggestions = await encyclopedia_service.generate_topic_suggestions(
            ai_provider=request.ai_provider,
            api_key=api_key,
            limit=request.limit
        )
        
        return [TopicSuggestionResponse(**suggestion) for suggestion in suggestions]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error generating topic suggestions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate topic suggestions"
        )


@router.post(
    "/entries/{entry_id}/links",
    response_model=List[dict],
    summary="Generate entry links (DEPRECATED)",
    description="Manual link generation deprecated - use automatic term linking instead"
)
async def generate_entry_links(
    entry_id: str,
    request: GenerateLinksRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    DEPRECATED: Manual link generation replaced by automatic term linking.
    
    This endpoint is kept for backward compatibility but returns an empty list.
    Inter-entry links are now handled automatically by the TermLinkingService.
    """
    logger.info(f"Deprecated manual link generation called for entry {entry_id}")
    return []


@router.post(
    "/search",
    response_model=EncyclopediaSearchResponse,
    summary="Search encyclopedia",
    description="Search encyclopedia entries by title and content"
)
async def search_encyclopedia(
    request: EncyclopediaSearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search encyclopedia entries by title and content."""
    try:
        encyclopedia_service = EncyclopediaService(db)
        
        # If user can't view drafts, only search published entries
        status_filter = request.status_filter
        if status_filter is None and not current_user.has_resource_permission("encyclopedia", "view_drafts"):
            status_filter = EncyclopediaStatus.PUBLISHED
        
        entries = await encyclopedia_service.search_entries(
            query=request.query,
            status_filter=status_filter,
            limit=request.limit
        )
        
        return EncyclopediaSearchResponse(
            entries=[EncyclopediaEntryListResponse.model_validate(entry) for entry in entries],
            total_count=len(entries),
            query=request.query
        )
        
    except Exception as e:
        logger.error(f"Unexpected error searching encyclopedia: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search encyclopedia"
        )


@router.get(
    "/stats",
    response_model=EncyclopediaStatsResponse,
    summary="Get encyclopedia statistics",
    description="Get basic encyclopedia statistics"
)
async def get_encyclopedia_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get basic encyclopedia statistics."""
    try:
        # For now, return basic stats
        # In a full implementation, would add a dedicated stats method to the service
        return EncyclopediaStatsResponse(
            total_entries=0,
            published_entries=0,
            draft_entries=0,
            archived_entries=0,
            total_conversations=0,
            total_links=0,
            recent_activity=[]
        )
        
    except Exception as e:
        logger.error(f"Unexpected error getting encyclopedia stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get encyclopedia statistics"
        )