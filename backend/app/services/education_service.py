"""
Education service for managing poker education content.
"""
from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, Integer
from sqlalchemy.orm import selectinload

from ..models.education import EducationContent, EducationProgress, DifficultyLevel, ContentCategory
from ..schemas.education import (
    EducationContentCreate,
    EducationContentUpdate,
    EducationProgressCreate,
    EducationProgressUpdate,
    EducationSearchFilters,
    EducationSearchResponse,
    EducationContentWithProgress,
    EducationCategoryStats,
    EducationOverview
)
from .exceptions import NotFoundError, ValidationError


class EducationService:
    """Service for managing education content and user progress."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_content(self, content_data: EducationContentCreate) -> EducationContent:
        """Create new education content."""
        # Check if slug already exists
        existing = await self.db.execute(
            select(EducationContent).where(EducationContent.slug == content_data.slug)
        )
        if existing.scalar_one_or_none():
            raise ValidationError(f"Content with slug '{content_data.slug}' already exists")

        content = EducationContent(**content_data.model_dump())
        self.db.add(content)
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def get_content_by_id(self, content_id: UUID) -> EducationContent:
        """Get education content by ID."""
        result = await self.db.execute(
            select(EducationContent).where(EducationContent.id == content_id)
        )
        content = result.scalar_one_or_none()
        if not content:
            raise NotFoundError(f"Education content with ID {content_id} not found")
        return content

    async def get_content_by_slug(self, slug: str) -> EducationContent:
        """Get education content by slug."""
        result = await self.db.execute(
            select(EducationContent).where(EducationContent.slug == slug)
        )
        content = result.scalar_one_or_none()
        if not content:
            raise NotFoundError(f"Education content with slug '{slug}' not found")
        return content

    async def update_content(self, content_id: UUID, update_data: EducationContentUpdate) -> EducationContent:
        """Update education content."""
        content = await self.get_content_by_id(content_id)
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(content, field, value)
        
        await self.db.commit()
        await self.db.refresh(content)
        return content

    async def delete_content(self, content_id: UUID) -> bool:
        """Delete education content."""
        content = await self.get_content_by_id(content_id)
        await self.db.delete(content)
        await self.db.commit()
        return True

    async def search_content(
        self, 
        filters: EducationSearchFilters, 
        user_id: Optional[UUID] = None
    ) -> EducationSearchResponse:
        """Search education content with advanced filters."""
        # Base query for content
        if filters.favorites_only or filters.bookmarks_only:
            # Need to join with progress table for user-specific filters
            if not user_id:
                # Return empty results if user-specific filters requested without user
                return EducationSearchResponse(
                    items=[],
                    total=0,
                    limit=filters.limit,
                    offset=filters.offset,
                    has_more=False
                )
            
            query = select(EducationContent).join(
                EducationProgress, 
                EducationContent.id == EducationProgress.content_id
            ).where(EducationProgress.user_id == user_id)
        else:
            query = select(EducationContent)
        
        # Apply filters
        conditions = []
        
        if filters.is_published:
            conditions.append(EducationContent.is_published == True)
        
        if filters.category:
            conditions.append(EducationContent.category == filters.category)
        
        if filters.difficulty:
            conditions.append(EducationContent.difficulty == filters.difficulty)
        
        if filters.tags:
            # Content must have at least one of the specified tags
            tag_conditions = [EducationContent.tags.contains([tag]) for tag in filters.tags]
            conditions.append(or_(*tag_conditions))
        
        if filters.has_interactive_demo is not None:
            conditions.append(EducationContent.interactive_demo == filters.has_interactive_demo)
        
        if filters.has_video is not None:
            if filters.has_video:
                conditions.append(EducationContent.video_url.isnot(None))
            else:
                conditions.append(EducationContent.video_url.is_(None))
        
        if filters.search_query:
            search_term = f"%{filters.search_query}%"
            search_conditions = [
                EducationContent.title.ilike(search_term),
                EducationContent.definition.ilike(search_term),
                EducationContent.explanation.ilike(search_term)
            ]
            conditions.append(or_(*search_conditions))
        
        # User-specific filters
        if filters.favorites_only and user_id:
            conditions.append(EducationProgress.is_favorite == True)
        
        if filters.bookmarks_only and user_id:
            conditions.append(EducationProgress.is_bookmarked == True)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply sorting
        sort_column = getattr(EducationContent, filters.sort_by, EducationContent.title)
        if filters.sort_order == 'desc':
            sort_column = sort_column.desc()
        
        query = query.order_by(sort_column)
        
        # Apply pagination
        query = query.offset(filters.offset).limit(filters.limit)
        
        result = await self.db.execute(query)
        content_items = result.scalars().all()
        
        # Get user progress if user_id provided
        items_with_progress = []
        for content in content_items:
            progress = None
            if user_id:
                progress = await self.get_user_progress(user_id, content.id)
            
            items_with_progress.append(EducationContentWithProgress(
                **content.__dict__,
                progress=progress
            ))
        
        return EducationSearchResponse(
            items=items_with_progress,
            total=total,
            limit=filters.limit,
            offset=filters.offset,
            has_more=filters.offset + len(content_items) < total
        )

    async def get_available_tags(self) -> List[str]:
        """Get all unique tags from published education content."""
        result = await self.db.execute(
            select(EducationContent.tags)
            .where(EducationContent.is_published == True)
        )
        
        all_tags = set()
        for row in result.scalars().all():
            if row:  # tags field might be None or empty
                all_tags.update(row)
        
        return sorted(list(all_tags))

    async def get_user_progress(self, user_id: UUID, content_id: UUID) -> Optional[EducationProgress]:
        """Get user progress for specific content."""
        result = await self.db.execute(
            select(EducationProgress).where(
                and_(
                    EducationProgress.user_id == user_id,
                    EducationProgress.content_id == content_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_or_update_progress(
        self, 
        user_id: UUID, 
        content_id: UUID, 
        progress_data: EducationProgressCreate
    ) -> EducationProgress:
        """Create or update user progress for content."""
        # Verify content exists
        await self.get_content_by_id(content_id)
        
        existing_progress = await self.get_user_progress(user_id, content_id)
        
        if existing_progress:
            # Update existing progress
            update_dict = progress_data.model_dump(exclude_unset=True, exclude={'content_id'})
            for field, value in update_dict.items():
                setattr(existing_progress, field, value)
            
            # Update last_accessed if content was accessed
            if progress_data.is_read or progress_data.time_spent_seconds > 0:
                existing_progress.last_accessed = func.now()
            
            await self.db.commit()
            await self.db.refresh(existing_progress)
            return existing_progress
        else:
            # Create new progress
            progress = EducationProgress(
                user_id=user_id,
                content_id=content_id,
                **progress_data.model_dump(exclude={'content_id'})
            )
            
            if progress_data.is_read or progress_data.time_spent_seconds > 0:
                progress.last_accessed = func.now()
            
            self.db.add(progress)
            await self.db.commit()
            await self.db.refresh(progress)
            return progress

    async def get_user_bookmarks(self, user_id: UUID) -> List[EducationContentWithProgress]:
        """Get user's bookmarked content."""
        result = await self.db.execute(
            select(EducationContent, EducationProgress)
            .join(EducationProgress, EducationContent.id == EducationProgress.content_id)
            .where(
                and_(
                    EducationProgress.user_id == user_id,
                    EducationProgress.is_bookmarked == True
                )
            )
            .order_by(EducationProgress.updated_at.desc())
        )
        
        items = []
        for content, progress in result.all():
            items.append(EducationContentWithProgress(
                **content.__dict__,
                progress=progress
            ))
        
        return items

    async def get_user_favorites(self, user_id: UUID) -> List[EducationContentWithProgress]:
        """Get user's favorite content."""
        result = await self.db.execute(
            select(EducationContent, EducationProgress)
            .join(EducationProgress, EducationContent.id == EducationProgress.content_id)
            .where(
                and_(
                    EducationProgress.user_id == user_id,
                    EducationProgress.is_favorite == True
                )
            )
            .order_by(EducationProgress.updated_at.desc())
        )
        
        items = []
        for content, progress in result.all():
            items.append(EducationContentWithProgress(
                **content.__dict__,
                progress=progress
            ))
        
        return items

    async def get_category_stats(self, user_id: Optional[UUID] = None) -> List[EducationCategoryStats]:
        """Get statistics for each content category."""
        stats = []
        
        for category in ContentCategory:
            # Get total content count for category
            total_result = await self.db.execute(
                select(func.count())
                .select_from(EducationContent)
                .where(
                    and_(
                        EducationContent.category == category,
                        EducationContent.is_published == True
                    )
                )
            )
            total_content = total_result.scalar()
            
            # Get content count by difficulty
            difficulty_result = await self.db.execute(
                select(EducationContent.difficulty, func.count())
                .where(
                    and_(
                        EducationContent.category == category,
                        EducationContent.is_published == True
                    )
                )
                .group_by(EducationContent.difficulty)
            )
            
            by_difficulty = {}
            for difficulty, count in difficulty_result.all():
                by_difficulty[difficulty.value] = count
            
            # Get user progress if user_id provided
            user_progress = None
            if user_id:
                progress_result = await self.db.execute(
                    select(
                        func.count().label('total'),
                        func.sum(func.cast(EducationProgress.is_read, Integer)).label('read'),
                        func.sum(func.cast(EducationProgress.is_bookmarked, Integer)).label('bookmarked'),
                        func.sum(func.cast(EducationProgress.is_favorite, Integer)).label('favorited')
                    )
                    .select_from(
                        EducationProgress.__table__.join(
                            EducationContent.__table__,
                            EducationProgress.content_id == EducationContent.id
                        )
                    )
                    .where(
                        and_(
                            EducationProgress.user_id == user_id,
                            EducationContent.category == category,
                            EducationContent.is_published == True
                        )
                    )
                )
                
                progress_data = progress_result.first()
                if progress_data and progress_data.total:
                    user_progress = {
                        'total_engaged': progress_data.total,
                        'read': progress_data.read or 0,
                        'bookmarked': progress_data.bookmarked or 0,
                        'favorited': progress_data.favorited or 0,
                        'completion_rate': (progress_data.read or 0) / total_content if total_content > 0 else 0
                    }
            
            stats.append(EducationCategoryStats(
                category=category,
                total_content=total_content,
                by_difficulty=by_difficulty,
                user_progress=user_progress
            ))
        
        return stats

    async def get_education_overview(self, user_id: Optional[UUID] = None) -> EducationOverview:
        """Get overview of education system."""
        # Get total content count
        total_result = await self.db.execute(
            select(func.count())
            .select_from(EducationContent)
            .where(EducationContent.is_published == True)
        )
        total_content = total_result.scalar()
        
        # Get category stats
        categories = await self.get_category_stats(user_id)
        
        # Get user-specific stats if user_id provided
        user_stats = None
        if user_id:
            user_result = await self.db.execute(
                select(
                    func.count().label('total_engaged'),
                    func.sum(func.cast(EducationProgress.is_read, Integer)).label('total_read'),
                    func.sum(func.cast(EducationProgress.is_bookmarked, Integer)).label('total_bookmarked'),
                    func.sum(func.cast(EducationProgress.is_favorite, Integer)).label('total_favorited'),
                    func.sum(EducationProgress.time_spent_seconds).label('total_time_spent')
                )
                .select_from(EducationProgress)
                .where(EducationProgress.user_id == user_id)
            )
            
            user_data = user_result.first()
            if user_data and user_data.total_engaged:
                user_stats = {
                    'total_engaged': user_data.total_engaged,
                    'total_read': user_data.total_read or 0,
                    'total_bookmarked': user_data.total_bookmarked or 0,
                    'total_favorited': user_data.total_favorited or 0,
                    'total_time_spent_seconds': user_data.total_time_spent or 0,
                    'overall_completion_rate': (user_data.total_read or 0) / total_content if total_content > 0 else 0
                }
        
        return EducationOverview(
            total_content=total_content,
            categories=categories,
            user_stats=user_stats
        )

    async def get_content_recommendations(
        self, 
        user_id: UUID, 
        limit: int = 10
    ) -> List[EducationContentWithProgress]:
        """Get personalized content recommendations for user."""
        # Get user's reading history to understand preferences
        user_progress_result = await self.db.execute(
            select(EducationProgress, EducationContent)
            .join(EducationContent, EducationProgress.content_id == EducationContent.id)
            .where(EducationProgress.user_id == user_id)
            .order_by(EducationProgress.last_accessed.desc())
        )
        
        user_history = user_progress_result.all()
        
        # Analyze user preferences
        preferred_categories = {}
        preferred_difficulties = {}
        
        for progress, content in user_history:
            if progress.is_read or progress.is_favorite:
                preferred_categories[content.category] = preferred_categories.get(content.category, 0) + 1
                preferred_difficulties[content.difficulty] = preferred_difficulties.get(content.difficulty, 0) + 1
        
        # Get content user hasn't engaged with yet
        engaged_content_ids = [progress.content_id for progress, _ in user_history]
        
        query = select(EducationContent).where(
            and_(
                EducationContent.is_published == True,
                ~EducationContent.id.in_(engaged_content_ids) if engaged_content_ids else True
            )
        )
        
        # Prioritize based on user preferences
        if preferred_categories:
            most_preferred_category = max(preferred_categories, key=preferred_categories.get)
            query = query.order_by(
                func.case(
                    (EducationContent.category == most_preferred_category, 1),
                    else_=2
                ),
                EducationContent.created_at.desc()
            )
        else:
            # For new users, start with basic content
            query = query.order_by(
                func.case(
                    (EducationContent.difficulty == DifficultyLevel.BEGINNER, 1),
                    (EducationContent.difficulty == DifficultyLevel.INTERMEDIATE, 2),
                    else_=3
                ),
                EducationContent.created_at.desc()
            )
        
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        recommended_content = result.scalars().all()
        
        # Convert to response format
        recommendations = []
        for content in recommended_content:
            recommendations.append(EducationContentWithProgress(
                **content.__dict__,
                progress=None  # No progress since user hasn't engaged with these
            ))
        
        return recommendations