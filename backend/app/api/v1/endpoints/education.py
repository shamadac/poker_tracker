"""
Education API endpoints for poker statistics encyclopedia.
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ....core.database import get_db
from ....api.deps import get_current_user
from ....models.user import User
from ....schemas.education import (
    EducationContentCreate,
    EducationContentUpdate,
    EducationContentResponse,
    EducationProgressCreate,
    EducationProgressUpdate,
    EducationProgressResponse,
    EducationContentWithProgress,
    EducationSearchFilters,
    EducationSearchResponse,
    EducationCategoryStats,
    EducationOverview,
    DifficultyLevel,
    ContentCategory
)
from ....schemas.common import SuccessResponse
from ....services.education_service import EducationService
from ....services.exceptions import NotFoundError, ValidationError

router = APIRouter()


@router.get("/overview", response_model=EducationOverview)
async def get_education_overview(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get overview of education system with user progress."""
    service = EducationService(db)
    return await service.get_education_overview(current_user.id)


@router.get("/categories/stats", response_model=List[EducationCategoryStats])
async def get_category_statistics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics for each education category."""
    service = EducationService(db)
    return await service.get_category_stats(current_user.id)


@router.get("/search", response_model=EducationSearchResponse)
async def search_education_content(
    category: Optional[ContentCategory] = Query(None, description="Filter by category"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty"),
    search_query: Optional[str] = Query(None, description="Search in title/content"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    favorites_only: bool = Query(False, description="Show only favorited content"),
    bookmarks_only: bool = Query(False, description="Show only bookmarked content"),
    has_interactive_demo: Optional[bool] = Query(None, description="Filter by interactive demo availability"),
    has_video: Optional[bool] = Query(None, description="Filter by video availability"),
    sort_by: str = Query("title", description="Sort by: title, difficulty, created_at, updated_at"),
    sort_order: str = Query("asc", description="Sort order: asc, desc"),
    limit: int = Query(50, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Results offset"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search education content with advanced filters."""
    filters = EducationSearchFilters(
        category=category,
        difficulty=difficulty,
        search_query=search_query,
        tags=tags,
        favorites_only=favorites_only,
        bookmarks_only=bookmarks_only,
        has_interactive_demo=has_interactive_demo,
        has_video=has_video,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit,
        offset=offset
    )
    
    service = EducationService(db)
    return await service.search_content(filters, current_user.id)


@router.get("/tags", response_model=List[str])
async def get_available_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all available tags from education content."""
    service = EducationService(db)
    return await service.get_available_tags()


@router.get("/content/{content_id}", response_model=EducationContentWithProgress)
async def get_education_content(
    content_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get specific education content with user progress."""
    service = EducationService(db)
    
    try:
        content = await service.get_content_by_id(content_id)
        progress = await service.get_user_progress(current_user.id, content_id)
        
        return EducationContentWithProgress(
            **content.__dict__,
            progress=progress
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/content/slug/{slug}", response_model=EducationContentWithProgress)
async def get_education_content_by_slug(
    slug: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get education content by slug with user progress."""
    service = EducationService(db)
    
    try:
        content = await service.get_content_by_slug(slug)
        progress = await service.get_user_progress(current_user.id, content.id)
        
        return EducationContentWithProgress(
            **content.__dict__,
            progress=progress
        )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/content/{content_id}/progress", response_model=EducationProgressResponse)
async def update_content_progress(
    content_id: UUID,
    progress_data: EducationProgressCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or update user progress for education content."""
    service = EducationService(db)
    
    try:
        # Override content_id from URL
        progress_data.content_id = str(content_id)
        progress = await service.create_or_update_progress(
            current_user.id, 
            content_id, 
            progress_data
        )
        return progress
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/content/{content_id}/progress", response_model=EducationProgressResponse)
async def patch_content_progress(
    content_id: UUID,
    progress_data: EducationProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update specific fields of user progress for education content."""
    service = EducationService(db)
    
    try:
        # Get existing progress or create new one
        existing_progress = await service.get_user_progress(current_user.id, content_id)
        
        if existing_progress:
            # Update existing progress
            update_dict = progress_data.model_dump(exclude_unset=True)
            for field, value in update_dict.items():
                setattr(existing_progress, field, value)
            
            await service.db.commit()
            await service.db.refresh(existing_progress)
            return existing_progress
        else:
            # Create new progress with provided fields
            create_data = EducationProgressCreate(
                content_id=str(content_id),
                **progress_data.model_dump(exclude_unset=True)
            )
            return await service.create_or_update_progress(
                current_user.id, 
                content_id, 
                create_data
            )
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/bookmarks", response_model=List[EducationContentWithProgress])
async def get_user_bookmarks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's bookmarked education content."""
    service = EducationService(db)
    return await service.get_user_bookmarks(current_user.id)


@router.get("/favorites", response_model=List[EducationContentWithProgress])
async def get_user_favorites(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's favorite education content."""
    service = EducationService(db)
    return await service.get_user_favorites(current_user.id)


@router.get("/recommendations", response_model=List[EducationContentWithProgress])
async def get_content_recommendations(
    limit: int = Query(10, ge=1, le=50, description="Number of recommendations"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get personalized content recommendations for user."""
    service = EducationService(db)
    return await service.get_content_recommendations(current_user.id, limit)


# Admin endpoints for content management
@router.post("/admin/content", response_model=EducationContentResponse)
async def create_education_content(
    content_data: EducationContentCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create new education content. (Admin only)"""
    # TODO: Add admin role check when RBAC is fully implemented
    service = EducationService(db)
    
    try:
        content = await service.create_content(content_data)
        return content
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/admin/content/{content_id}", response_model=EducationContentResponse)
async def update_education_content(
    content_id: UUID,
    update_data: EducationContentUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update education content. (Admin only)"""
    # TODO: Add admin role check when RBAC is fully implemented
    service = EducationService(db)
    
    try:
        content = await service.update_content(content_id, update_data)
        return content
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/admin/content/{content_id}", response_model=SuccessResponse)
async def delete_education_content(
    content_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete education content. (Admin only)"""
    # TODO: Add admin role check when RBAC is fully implemented
    service = EducationService(db)
    
    try:
        await service.delete_content(content_id)
        return SuccessResponse(message="Education content deleted successfully")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))