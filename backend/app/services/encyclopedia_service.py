"""
Encyclopedia Service for AI-powered content generation and management.

This service handles the creation, refinement, and management of encyclopedia
entries using AI providers (Groq and Gemini) with conversation threading
and automatic link generation.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from ..models.encyclopedia import (
    EncyclopediaEntry, 
    EncyclopediaConversation, 
    EncyclopediaLink,
    EncyclopediaStatus,
    AIProvider as EncyclopediaAIProvider
)
from ..models.user import User
from .ai_providers import AIProviderFactory, AIProvider, AIResponse
from ..core.config import settings

logger = logging.getLogger(__name__)


class EncyclopediaService:
    """Service for managing encyclopedia entries with AI-powered content generation."""
    
    def __init__(self, db: AsyncSession):
        """Initialize the encyclopedia service."""
        self.db = db
    
    async def get_api_key(self, user_id: str, provider: str) -> Optional[str]:
        """Get API key for a specific provider."""
        user_service = UserService()
        return await user_service.get_api_key(self.db, user_id, provider)
    
    async def create_entry(
        self,
        title: str,
        initial_prompt: str,
        ai_provider: EncyclopediaAIProvider,
        created_by: str,
        api_key: str
    ) -> Tuple[EncyclopediaEntry, str]:
        """
        Create a new encyclopedia entry with AI-generated content.
        
        Args:
            title: Title for the encyclopedia entry
            initial_prompt: Initial prompt for content generation
            ai_provider: AI provider to use (groq or gemini)
            created_by: User ID of the creator
            api_key: API key for the AI provider
            
        Returns:
            Tuple of (created entry, generated content)
            
        Raises:
            ValueError: If content generation fails
        """
        try:
            # Generate initial content using AI
            content_response = await self._generate_content(
                prompt=initial_prompt,
                ai_provider=ai_provider,
                api_key=api_key,
                context=f"Creating encyclopedia entry for: {title}"
            )
            
            if not content_response.success:
                raise ValueError(f"Failed to generate content: {content_response.error}")
            
            # Create the encyclopedia entry
            entry = EncyclopediaEntry(
                title=title,
                content=content_response.content,
                status=EncyclopediaStatus.DRAFT,
                ai_provider=ai_provider.value,
                created_by=created_by
            )
            
            self.db.add(entry)
            await self.db.flush()  # Get the entry ID
            
            # Create the initial conversation record
            conversation = EncyclopediaConversation(
                entry_id=entry.id,
                prompt=initial_prompt,
                response=content_response.content,
                ai_provider=ai_provider.value,
                conversation_metadata={
                    "usage": content_response.usage,
                    "model_metadata": content_response.metadata
                }
            )
            
            self.db.add(conversation)
            await self.db.commit()
            
            logger.info(f"Created encyclopedia entry '{title}' with ID {entry.id}")
            return entry, content_response.content
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create encyclopedia entry '{title}': {e}")
            raise
    
    async def refine_content(
        self,
        entry_id: str,
        refinement_prompt: str,
        ai_provider: EncyclopediaAIProvider,
        api_key: str
    ) -> Tuple[str, EncyclopediaConversation]:
        """
        Refine existing encyclopedia content using AI conversation.
        
        Args:
            entry_id: ID of the encyclopedia entry to refine
            refinement_prompt: Prompt for content refinement
            ai_provider: AI provider to use
            api_key: API key for the AI provider
            
        Returns:
            Tuple of (refined content, conversation record)
            
        Raises:
            ValueError: If entry not found or refinement fails
        """
        try:
            # Get the entry with conversation history
            result = await self.db.execute(
                select(EncyclopediaEntry)
                .options(selectinload(EncyclopediaEntry.conversations))
                .where(EncyclopediaEntry.id == entry_id)
            )
            entry = result.scalar_one_or_none()
            
            if not entry:
                raise ValueError(f"Encyclopedia entry {entry_id} not found")
            
            # Build conversation context
            conversation_context = self._build_conversation_context(entry)
            
            # Generate refined content
            full_prompt = f"""
            Current content:
            {entry.content}
            
            Previous conversation:
            {conversation_context}
            
            Refinement request:
            {refinement_prompt}
            
            Please provide the refined content based on the request above.
            """
            
            content_response = await self._generate_content(
                prompt=full_prompt,
                ai_provider=ai_provider,
                api_key=api_key,
                context=f"Refining encyclopedia entry: {entry.title}"
            )
            
            if not content_response.success:
                raise ValueError(f"Failed to refine content: {content_response.error}")
            
            # Update the entry content
            entry.content = content_response.content
            entry.ai_provider = ai_provider.value
            
            # Create conversation record
            conversation = EncyclopediaConversation(
                entry_id=entry_id,
                prompt=refinement_prompt,
                response=content_response.content,
                ai_provider=ai_provider.value,
                conversation_metadata={
                    "usage": content_response.usage,
                    "model_metadata": content_response.metadata,
                    "refinement": True
                }
            )
            
            self.db.add(conversation)
            await self.db.commit()
            
            logger.info(f"Refined content for encyclopedia entry {entry_id}")
            return content_response.content, conversation
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to refine encyclopedia entry {entry_id}: {e}")
            raise
    
    async def approve_entry(
        self,
        entry_id: str,
        approved_by: str
    ) -> EncyclopediaEntry:
        """
        Approve an encyclopedia entry for publication.
        
        Args:
            entry_id: ID of the entry to approve
            approved_by: User ID of the approver
            
        Returns:
            The approved entry
            
        Raises:
            ValueError: If entry not found or already published
        """
        try:
            result = await self.db.execute(
                select(EncyclopediaEntry)
                .where(EncyclopediaEntry.id == entry_id)
            )
            entry = result.scalar_one_or_none()
            
            if not entry:
                raise ValueError(f"Encyclopedia entry {entry_id} not found")
            
            if entry.status == EncyclopediaStatus.PUBLISHED:
                raise ValueError(f"Entry {entry_id} is already published")
            
            # Update entry status
            entry.status = EncyclopediaStatus.PUBLISHED
            entry.approved_by = approved_by
            entry.published_at = datetime.utcnow()
            
            await self.db.commit()
            
            logger.info(f"Approved encyclopedia entry {entry_id} for publication")
            return entry
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to approve encyclopedia entry {entry_id}: {e}")
            raise
    
    async def generate_topic_suggestions(
        self,
        ai_provider: EncyclopediaAIProvider,
        api_key: str,
        limit: int = 10
    ) -> List[Dict[str, str]]:
        """
        Generate topic suggestions based on content gaps in the encyclopedia.
        
        Args:
            ai_provider: AI provider to use
            api_key: API key for the AI provider
            limit: Maximum number of suggestions to return
            
        Returns:
            List of topic suggestions with titles and descriptions
        """
        try:
            # Get existing entry titles
            result = await self.db.execute(
                select(EncyclopediaEntry.title)
                .where(EncyclopediaEntry.status.in_([
                    EncyclopediaStatus.DRAFT,
                    EncyclopediaStatus.PUBLISHED
                ]))
            )
            existing_titles = [row[0] for row in result.fetchall()]
            
            # Create prompt for topic suggestions
            existing_topics_text = "\n".join([f"- {title}" for title in existing_titles])
            
            suggestion_prompt = f"""
            You are helping to build a comprehensive poker encyclopedia. 
            
            Current topics covered:
            {existing_topics_text if existing_titles else "No topics covered yet"}
            
            Please suggest {limit} important poker topics that would be valuable additions to this encyclopedia. 
            Focus on concepts that are fundamental to poker strategy, statistics, or gameplay.
            
            For each suggestion, provide:
            1. A clear, concise title
            2. A brief description of why this topic is important
            
            Format your response as a JSON array with objects containing "title" and "description" fields.
            """
            
            response = await self._generate_content(
                prompt=suggestion_prompt,
                ai_provider=ai_provider,
                api_key=api_key,
                context="Generating topic suggestions for encyclopedia"
            )
            
            if not response.success:
                logger.error(f"Failed to generate topic suggestions: {response.error}")
                return []
            
            # Parse the response (simplified - in production, would use proper JSON parsing)
            # For now, return a basic structure
            suggestions = []
            lines = response.content.split('\n')
            current_title = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('"title"') or line.startswith('title'):
                    # Extract title
                    if ':' in line:
                        current_title = line.split(':', 1)[1].strip().strip('"').strip(',')
                elif line.startswith('"description"') or line.startswith('description'):
                    # Extract description
                    if ':' in line and current_title:
                        description = line.split(':', 1)[1].strip().strip('"').strip(',')
                        suggestions.append({
                            "title": current_title,
                            "description": description
                        })
                        current_title = None
            
            logger.info(f"Generated {len(suggestions)} topic suggestions")
            return suggestions[:limit]
            
        except Exception as e:
            logger.error(f"Failed to generate topic suggestions: {e}")
            return []
    
    async def generate_entry_links(
        self,
        entry_id: str,
        ai_provider: EncyclopediaAIProvider,
        api_key: str
    ) -> List[EncyclopediaLink]:
        """
        DEPRECATED: Manual link generation replaced by automatic term linking.
        
        This method is kept for backward compatibility but now returns an empty list.
        Inter-entry links are now handled automatically by the TermLinkingService
        throughout the frontend interface.
        
        Args:
            entry_id: ID of the entry (unused)
            ai_provider: AI provider (unused)
            api_key: API key (unused)
            
        Returns:
            Empty list - links are now handled automatically
        """
        logger.info(f"Manual link generation deprecated for entry {entry_id}. Using automatic term linking instead.")
        return []
    
    async def search_entries(
        self,
        query: str,
        status_filter: Optional[EncyclopediaStatus] = None,
        limit: int = 20
    ) -> List[EncyclopediaEntry]:
        """
        Search encyclopedia entries by title and content.
        
        Args:
            query: Search query
            status_filter: Optional status filter
            limit: Maximum number of results
            
        Returns:
            List of matching encyclopedia entries
        """
        try:
            # Build search query
            search_conditions = [
                or_(
                    EncyclopediaEntry.title.ilike(f"%{query}%"),
                    EncyclopediaEntry.content.ilike(f"%{query}%")
                )
            ]
            
            if status_filter:
                search_conditions.append(EncyclopediaEntry.status == status_filter)
            
            result = await self.db.execute(
                select(EncyclopediaEntry)
                .where(and_(*search_conditions))
                .order_by(EncyclopediaEntry.created_at.desc())
                .limit(limit)
            )
            
            entries = result.scalars().all()
            logger.info(f"Found {len(entries)} entries matching query: {query}")
            return entries
            
        except Exception as e:
            logger.error(f"Failed to search encyclopedia entries: {e}")
            return []
    
    async def get_entry_with_links(self, entry_id: str) -> Optional[EncyclopediaEntry]:
        """
        Get an encyclopedia entry with its related links.
        
        Args:
            entry_id: ID of the entry to retrieve
            
        Returns:
            Encyclopedia entry with links, or None if not found
        """
        try:
            result = await self.db.execute(
                select(EncyclopediaEntry)
                .options(
                    selectinload(EncyclopediaEntry.source_links),
                    selectinload(EncyclopediaEntry.target_links),
                    selectinload(EncyclopediaEntry.conversations)
                )
                .where(EncyclopediaEntry.id == entry_id)
            )
            
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Failed to get encyclopedia entry {entry_id}: {e}")
            return None
    
    def _build_conversation_context(self, entry: EncyclopediaEntry) -> str:
        """Build conversation context from entry's conversation history."""
        if not entry.conversations:
            return "No previous conversation."
        
        context_parts = []
        for conv in entry.conversations[-3:]:  # Last 3 conversations
            context_parts.append(f"User: {conv.prompt}")
            context_parts.append(f"AI: {conv.response[:200]}...")  # Truncate for context
        
        return "\n".join(context_parts)
    
    async def _generate_content(
        self,
        prompt: str,
        ai_provider: EncyclopediaAIProvider,
        api_key: str,
        context: str = ""
    ) -> AIResponse:
        """
        Generate content using the specified AI provider.
        
        Args:
            prompt: The prompt for content generation
            ai_provider: AI provider to use
            api_key: API key for the provider
            context: Additional context for logging
            
        Returns:
            AI response with generated content
        """
        try:
            # Convert encyclopedia AI provider to service AI provider
            service_provider = AIProvider.GROQ if ai_provider == EncyclopediaAIProvider.GROQ else AIProvider.GEMINI
            
            # Create AI client
            client = AIProviderFactory.create_client(service_provider, api_key)
            
            # System prompt for encyclopedia content
            system_prompt = """
            You are an expert poker encyclopedia writer. Create comprehensive, accurate, and educational content about poker concepts, strategies, and statistics.
            
            Guidelines:
            - Write in a clear, encyclopedic style
            - Include specific examples where helpful
            - Focus on accuracy and educational value
            - Use proper poker terminology
            - Structure content with clear sections when appropriate
            - Aim for content that is both informative for beginners and valuable for experienced players
            """
            
            # Generate response
            response = await client.generate_response(
                system_prompt=system_prompt,
                user_prompt=prompt,
                temperature=0.7,
                max_tokens=2048
            )
            
            if context:
                logger.info(f"Generated content for: {context}")
            
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            return AIResponse(
                success=False,
                error=str(e),
                provider=service_provider
            )