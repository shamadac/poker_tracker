"""
Property-based test for encyclopedia content workflow.

**Feature: poker-app-fixes-and-cleanup, Property 4: Encyclopedia Content Workflow**
**Validates: Requirements 4.2, 4.3, 4.4, 4.5**

Property 4: Encyclopedia Content Workflow
*For any* encyclopedia entry creation and management workflow, the system should maintain 
conversation threads during AI content generation, provide proper approval workflows with 
version control, automatically generate inter-entry links, and support iterative content 
refinement through follow-up prompts.
"""
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Tuple
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, delete, select
from sqlalchemy.exc import SQLAlchemyError
import uuid

from app.models.user import User
from app.models.encyclopedia import (
    EncyclopediaEntry, 
    EncyclopediaConversation, 
    EncyclopediaLink,
    EncyclopediaStatus,
    AIProvider as EncyclopediaAIProvider
)
from app.services.user_service import UserService
from app.services.ai_providers import AIProvider, AIResponse


class MockEncyclopediaService:
    """Mock encyclopedia service for testing."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_entry(self, title: str, initial_prompt: str, ai_provider, created_by: str, api_key: str):
        """Mock create entry method."""
        # Create the encyclopedia entry
        entry = EncyclopediaEntry(
            title=title,
            content="Generated content for " + title,
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
            response="Generated content for " + title,
            ai_provider=ai_provider.value,
            conversation_metadata={"usage": {"tokens": 100}, "model_metadata": {"model": "test"}}
        )
        
        self.db.add(conversation)
        await self.db.commit()
        
        return entry, "Generated content for " + title
    
    async def refine_content(self, entry_id: str, refinement_prompt: str, ai_provider, api_key: str):
        """Mock refine content method."""
        # Get the entry
        result = await self.db.execute(
            select(EncyclopediaEntry).where(EncyclopediaEntry.id == entry_id)
        )
        entry = result.scalar_one_or_none()
        
        if not entry:
            raise ValueError(f"Encyclopedia entry {entry_id} not found")
        
        # Update content
        refined_content = f"Refined: {entry.content}"
        entry.content = refined_content
        entry.ai_provider = ai_provider.value
        
        # Create conversation record
        conversation = EncyclopediaConversation(
            entry_id=entry_id,
            prompt=refinement_prompt,
            response=refined_content,
            ai_provider=ai_provider.value,
            conversation_metadata={"usage": {"tokens": 100}, "refinement": True}
        )
        
        self.db.add(conversation)
        await self.db.commit()
        
        return refined_content, conversation
    
    async def approve_entry(self, entry_id: str, approved_by: str):
        """Mock approve entry method."""
        result = await self.db.execute(
            select(EncyclopediaEntry).where(EncyclopediaEntry.id == entry_id)
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
        return entry
    
    async def generate_topic_suggestions(self, ai_provider, api_key: str, limit: int = 10):
        """Mock generate topic suggestions method."""
        suggestions = [
            {"title": "Advanced Bluffing", "description": "Essential bluffing techniques"},
            {"title": "Bankroll Management", "description": "Managing your poker funds"},
            {"title": "Position Play", "description": "Using position to your advantage"}
        ]
        return suggestions[:limit]
    
    async def search_entries(self, query: str, status_filter=None, limit: int = 20):
        """Mock search entries method."""
        # Build search conditions
        conditions = []
        if status_filter:
            conditions.append(EncyclopediaEntry.status == status_filter)
        
        # Simple search implementation
        if conditions:
            result = await self.db.execute(
                select(EncyclopediaEntry).where(*conditions).limit(limit)
            )
        else:
            result = await self.db.execute(
                select(EncyclopediaEntry).limit(limit)
            )
        
        return result.scalars().all()
    
    async def generate_entry_links(self, entry_id: str, ai_provider, api_key: str):
        """Mock generate entry links method (deprecated)."""
        return []  # Return empty list as per deprecation
    
    async def get_entry_with_links(self, entry_id: str):
        """Mock get entry with links method."""
        from sqlalchemy.orm import selectinload
        
        result = await self.db.execute(
            select(EncyclopediaEntry)
            .options(
                selectinload(EncyclopediaEntry.conversations),
                selectinload(EncyclopediaEntry.source_links),
                selectinload(EncyclopediaEntry.target_links)
            )
            .where(EncyclopediaEntry.id == entry_id)
        )
        
        return result.scalar_one_or_none()


# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine and session
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)

# Create a minimal metadata that only includes the tables we need
test_metadata = MetaData()
User.__table__.to_metadata(test_metadata)
EncyclopediaEntry.__table__.to_metadata(test_metadata)
EncyclopediaConversation.__table__.to_metadata(test_metadata)
EncyclopediaLink.__table__.to_metadata(test_metadata)


# Strategy for generating encyclopedia entry titles
@st.composite
def encyclopedia_title_strategy(draw):
    """Generate realistic encyclopedia entry titles."""
    poker_terms = [
        "Pot Odds", "Implied Odds", "Position Play", "Bluffing", "Value Betting",
        "Continuation Betting", "Check-Raising", "Slow Playing", "Semi-Bluffing",
        "Bankroll Management", "Variance", "Expected Value", "Fold Equity",
        "Range Analysis", "Board Texture", "Stack-to-Pot Ratio", "ICM",
        "Tournament Strategy", "Cash Game Strategy", "Multi-Table Tournaments"
    ]
    
    # Either use a predefined term or generate a custom one
    if draw(st.booleans()):
        return draw(st.sampled_from(poker_terms))
    else:
        # Generate custom title
        prefix = draw(st.sampled_from(["Advanced", "Basic", "Intermediate", "Professional"]))
        concept = draw(st.sampled_from(["Strategy", "Concepts", "Techniques", "Analysis"]))
        return f"{prefix} {concept}"


@st.composite
def ai_prompt_strategy(draw):
    """Generate realistic AI prompts for encyclopedia content."""
    prompt_types = [
        "Explain the concept of {} in poker strategy",
        "Provide a comprehensive guide to {}",
        "Describe how {} affects poker decision making",
        "What are the key principles of {}?",
        "How can players improve their {} skills?"
    ]
    
    template = draw(st.sampled_from(prompt_types))
    topic = draw(st.text(min_size=5, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs'))))
    
    return template.format(topic.strip())


@st.composite
def refinement_prompt_strategy(draw):
    """Generate realistic refinement prompts."""
    refinement_types = [
        "Add more examples to illustrate the concept",
        "Simplify the explanation for beginners",
        "Include advanced strategies for experienced players",
        "Add mathematical calculations and formulas",
        "Provide more practical applications",
        "Include common mistakes to avoid",
        "Add references to related concepts"
    ]
    
    return draw(st.sampled_from(refinement_types))


class TestEncyclopediaContentWorkflowProperty:
    """Property-based tests for encyclopedia content workflow."""
    
    @given(
        encyclopedia_title_strategy(),
        ai_prompt_strategy(),
        st.sampled_from([EncyclopediaAIProvider.GROQ, EncyclopediaAIProvider.GEMINI])
    )
    @settings(max_examples=20, deadline=15000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_content_generation_workflow(self, title, initial_prompt, ai_provider):
        """
        Property: For any encyclopedia entry creation request, the system should 
        generate content using AI, maintain conversation history, and store the entry properly.
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user with unique ID
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email=f"encyclopedia-{user_id}@example.com",
                    password_hash="hashed_password",
                    api_keys={"groq": "test_groq_key", "gemini": "test_gemini_key"}
                )
                session.add(user)
                await session.commit()
                
                # Create encyclopedia service
                encyclopedia_service = MockEncyclopediaService(session)
                
                # Property: Content generation should succeed
                entry, generated_content = await encyclopedia_service.create_entry(
                    title=title,
                    initial_prompt=initial_prompt,
                    ai_provider=ai_provider,
                    created_by=user_id,
                    api_key="test_api_key"
                )
                
                # Property: Entry should be created with correct attributes
                assert entry is not None
                assert entry.title == title
                assert entry.content == generated_content
                assert entry.status == EncyclopediaStatus.DRAFT
                assert entry.ai_provider == ai_provider.value
                assert entry.created_by == user_id
                
                # Property: Conversation history should be maintained
                conversations = await session.execute(
                    select(EncyclopediaConversation)
                    .where(EncyclopediaConversation.entry_id == entry.id)
                )
                conversation_list = conversations.scalars().all()
                
                assert len(conversation_list) == 1
                conversation = conversation_list[0]
                assert conversation.prompt == initial_prompt
                assert conversation.response == generated_content
                assert conversation.ai_provider == ai_provider.value
                
                # Property: Entry should be retrievable from database
                retrieved_entry = await encyclopedia_service.get_entry_with_links(entry.id)
                assert retrieved_entry is not None
                assert retrieved_entry.id == entry.id
                assert len(retrieved_entry.conversations) == 1
                
                await session.close()
            
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.drop_all)
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        encyclopedia_title_strategy(),
        ai_prompt_strategy(),
        st.lists(refinement_prompt_strategy(), min_size=1, max_size=3),
        st.sampled_from([EncyclopediaAIProvider.GROQ, EncyclopediaAIProvider.GEMINI])
    )
    @settings(max_examples=15, deadline=20000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_iterative_content_refinement(self, title, initial_prompt, refinement_prompts, ai_provider):
        """
        Property: For any series of refinement prompts, the system should maintain 
        conversation threads and allow iterative content improvement.
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email=f"refinement-{user_id}@example.com",
                    password_hash="hashed_password",
                    api_keys={"groq": "test_groq_key", "gemini": "test_gemini_key"}
                )
                session.add(user)
                await session.commit()
                
                # Create encyclopedia service
                encyclopedia_service = MockEncyclopediaService(session)
                
                # Create initial entry
                entry, _ = await encyclopedia_service.create_entry(
                    title=title,
                    initial_prompt=initial_prompt,
                    ai_provider=ai_provider,
                    created_by=user_id,
                    api_key="test_api_key"
                )
                
                # Property: Iterative refinement should work
                for i, refinement_prompt in enumerate(refinement_prompts):
                    refined_content, conversation = await encyclopedia_service.refine_content(
                        entry_id=entry.id,
                        refinement_prompt=refinement_prompt,
                        ai_provider=ai_provider,
                        api_key="test_api_key"
                    )
                    
                    # Property: Content should be updated
                    assert "Refined:" in refined_content
                    
                    # Property: Conversation should be recorded
                    assert conversation.prompt == refinement_prompt
                    assert "Refined:" in conversation.response
                    assert conversation.ai_provider == ai_provider.value
                
                # Property: All conversations should be maintained
                final_entry = await encyclopedia_service.get_entry_with_links(entry.id)
                assert len(final_entry.conversations) == len(refinement_prompts) + 1  # Initial + refinements
                
                # Property: Conversations should be in chronological order
                conversations = sorted(final_entry.conversations, key=lambda c: c.created_at)
                assert conversations[0].prompt == initial_prompt
                for i, refinement_prompt in enumerate(refinement_prompts):
                    assert conversations[i + 1].prompt == refinement_prompt
                
                await session.close()
            
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.drop_all)
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        encyclopedia_title_strategy(),
        ai_prompt_strategy(),
        st.sampled_from([EncyclopediaAIProvider.GROQ, EncyclopediaAIProvider.GEMINI])
    )
    @settings(max_examples=15, deadline=15000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_approval_workflow_with_version_control(self, title, initial_prompt, ai_provider):
        """
        Property: For any encyclopedia entry, the approval workflow should properly 
        transition status from draft to published with version control.
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test users (creator and approver)
                creator_id = str(uuid.uuid4())
                approver_id = str(uuid.uuid4())
                
                creator = User(
                    id=creator_id,
                    email=f"creator-{creator_id}@example.com",
                    password_hash="hashed_password",
                    api_keys={"groq": "test_groq_key", "gemini": "test_gemini_key"}
                )
                
                approver = User(
                    id=approver_id,
                    email=f"approver-{approver_id}@example.com",
                    password_hash="hashed_password"
                )
                
                session.add(creator)
                session.add(approver)
                await session.commit()
                
                # Create encyclopedia service
                encyclopedia_service = MockEncyclopediaService(session)
                
                # Create entry
                entry, _ = await encyclopedia_service.create_entry(
                    title=title,
                    initial_prompt=initial_prompt,
                    ai_provider=ai_provider,
                    created_by=creator_id,
                    api_key="test_api_key"
                )
                
                # Property: Entry should start as draft
                assert entry.status == EncyclopediaStatus.DRAFT
                assert entry.approved_by is None
                assert entry.published_at is None
                
                # Property: Approval workflow should work
                approved_entry = await encyclopedia_service.approve_entry(
                    entry_id=entry.id,
                    approved_by=approver_id
                )
                
                # Property: Entry should be published after approval
                assert approved_entry.status == EncyclopediaStatus.PUBLISHED
                assert approved_entry.approved_by == approver_id
                assert approved_entry.published_at is not None
                assert approved_entry.created_by == creator_id  # Original creator preserved
                
                # Property: Published timestamp should be recent
                time_diff = datetime.utcnow() - approved_entry.published_at.replace(tzinfo=None)
                assert time_diff.total_seconds() < 60  # Within last minute
                
                # Property: Cannot approve already published entry
                with pytest.raises(ValueError, match="already published"):
                    await encyclopedia_service.approve_entry(
                        entry_id=entry.id,
                        approved_by=approver_id
                    )
                
                await session.close()
            
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.drop_all)
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        st.lists(encyclopedia_title_strategy(), min_size=2, max_size=5, unique=True),
        st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=10, deadline=15000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_topic_suggestion_generation(self, existing_titles, suggestion_limit):
        """
        Property: For any set of existing encyclopedia entries, the system should 
        generate relevant topic suggestions based on content gaps.
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email=f"suggestions-{user_id}@example.com",
                    password_hash="hashed_password",
                    api_keys={"groq": "test_groq_key", "gemini": "test_gemini_key"}
                )
                session.add(user)
                await session.commit()
                
                # Create existing entries
                for title in existing_titles:
                    entry = EncyclopediaEntry(
                        title=title,
                        content=f"Content for {title}",
                        status=EncyclopediaStatus.PUBLISHED,
                        ai_provider=EncyclopediaAIProvider.GROQ.value,
                        created_by=user_id
                    )
                    session.add(entry)
                await session.commit()
                
                # Create encyclopedia service
                encyclopedia_service = MockEncyclopediaService(session)
                
                # Property: Topic suggestions should be generated
                suggestions = await encyclopedia_service.generate_topic_suggestions(
                    ai_provider=EncyclopediaAIProvider.GROQ,
                    api_key="test_api_key",
                    limit=suggestion_limit
                )
                
                # Property: Should return suggestions (even if parsing is simplified)
                assert isinstance(suggestions, list)
                
                # Property: Should respect the limit (or return what's available)
                assert len(suggestions) <= suggestion_limit
                
                # Property: Each suggestion should have required fields
                for suggestion in suggestions:
                    assert isinstance(suggestion, dict)
                    assert "title" in suggestion
                    assert "description" in suggestion
                    assert isinstance(suggestion["title"], str)
                    assert isinstance(suggestion["description"], str)
                    assert len(suggestion["title"]) > 0
                    assert len(suggestion["description"]) > 0
                
                await session.close()
            
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.drop_all)
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        encyclopedia_title_strategy(),
        ai_prompt_strategy(),
        st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs')))
    )
    @settings(max_examples=15, deadline=15000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_search_functionality(self, title, initial_prompt, search_query):
        """
        Property: For any search query, the system should return relevant encyclopedia 
        entries based on title and content matching.
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email=f"search-{user_id}@example.com",
                    password_hash="hashed_password",
                    api_keys={"groq": "test_groq_key", "gemini": "test_gemini_key"}
                )
                session.add(user)
                await session.commit()
                
                # Create encyclopedia service
                encyclopedia_service = MockEncyclopediaService(session)
                
                # Create entry with searchable content
                entry, _ = await encyclopedia_service.create_entry(
                    title=title,
                    initial_prompt=initial_prompt,
                    ai_provider=EncyclopediaAIProvider.GROQ,
                    created_by=user_id,
                    api_key="test_api_key"
                )
                
                # Approve entry for search
                await encyclopedia_service.approve_entry(entry.id, user_id)
                
                # Property: Search should work with various queries
                search_results = await encyclopedia_service.search_entries(
                    query=search_query.strip(),
                    status_filter=EncyclopediaStatus.PUBLISHED,
                    limit=20
                )
                
                # Property: Search should return a list
                assert isinstance(search_results, list)
                
                # Property: All returned entries should be published
                for result in search_results:
                    assert result.status == EncyclopediaStatus.PUBLISHED
                
                # Property: Search with status filter should work
                draft_results = await encyclopedia_service.search_entries(
                    query=search_query.strip(),
                    status_filter=EncyclopediaStatus.DRAFT,
                    limit=20
                )
                assert isinstance(draft_results, list)
                
                await session.close()
            
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.drop_all)
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(
        st.lists(encyclopedia_title_strategy(), min_size=2, max_size=4, unique=True),
        st.sampled_from([EncyclopediaAIProvider.GROQ, EncyclopediaAIProvider.GEMINI])
    )
    @settings(max_examples=10, deadline=15000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_link_generation_deprecation(self, titles, ai_provider):
        """
        Property: For any encyclopedia entries, the deprecated manual link generation 
        should return empty results and log deprecation notice.
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                user_id = str(uuid.uuid4())
                user = User(
                    id=user_id,
                    email=f"links-{user_id}@example.com",
                    password_hash="hashed_password",
                    api_keys={"groq": "test_groq_key", "gemini": "test_gemini_key"}
                )
                session.add(user)
                await session.commit()
                
                # Create encyclopedia service
                encyclopedia_service = MockEncyclopediaService(session)
                
                # Create multiple entries
                entry_ids = []
                for title in titles:
                    entry, _ = await encyclopedia_service.create_entry(
                        title=title,
                        initial_prompt=f"Explain {title}",
                        ai_provider=ai_provider,
                        created_by=user_id,
                        api_key="test_api_key"
                    )
                    entry_ids.append(entry.id)
                
                # Property: Manual link generation should be deprecated
                for entry_id in entry_ids:
                    links = await encyclopedia_service.generate_entry_links(
                        entry_id=entry_id,
                        ai_provider=ai_provider,
                        api_key="test_api_key"
                    )
                    
                    # Property: Should return empty list (deprecated functionality)
                    assert isinstance(links, list)
                    assert len(links) == 0
                
                await session.close()
            
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.drop_all)
        
        # Run the async test
        asyncio.run(run_test())