"""
Property-based test for statistics loading reliability.

**Feature: poker-app-fixes-and-cleanup, Property 1: Statistics Loading Reliability**
**Validates: Requirements 1.1, 1.2, 1.3, 1.4, 1.5**

Property 1: Statistics Loading Reliability
*For any* user with valid credentials, when accessing the statistics page, the system should 
successfully load and display statistics within reasonable time bounds, implement proper retry 
logic with exponential backoff on failures, validate data integrity before display, and 
gracefully degrade to cached data when real-time calculation fails.
"""
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import MetaData, delete
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, TimeoutError as SQLTimeoutError

from app.models.user import User
from app.models.hand import PokerHand
from app.services.statistics_service import StatisticsService, StatisticsReliabilityError, DataIntegrityError
from app.services.cache_service import StatisticsCacheService
from app.schemas.statistics import StatisticsFilters, BasicStatistics, StatisticsResponse


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
PokerHand.__table__.to_metadata(test_metadata)


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(test_metadata.create_all)
    
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
    
    async with test_engine.begin() as conn:
        await conn.run_sync(test_metadata.drop_all)
    
    # Ensure engine is properly disposed
    await test_engine.dispose()


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    user = User(
        id="550e8400-e29b-41d4-a716-446655440000",  # Valid UUID format
        email="reliability@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def mock_cache_service():
    """Create a mock cache service for testing."""
    cache_service = Mock(spec=StatisticsCacheService)
    cache_service.get_user_statistics = AsyncMock(return_value=None)
    cache_service.set_user_statistics = AsyncMock(return_value=True)
    cache_service.get_trend_data = AsyncMock(return_value=None)
    cache_service.set_trend_data = AsyncMock(return_value=True)
    return cache_service


# Strategy for generating poker hand data
@st.composite
def poker_hand_strategy(draw, user_id: str):
    """Generate realistic poker hand data for property testing."""
    platforms = ["pokerstars", "ggpoker"]
    game_types = ["Hold'em No Limit", "Hold'em Limit", "Omaha"]
    game_formats = ["cash", "tournament"]
    positions = ["UTG", "UTG+1", "MP", "CO", "BTN", "SB", "BB"]
    stakes_options = ["$0.25/$0.50", "$0.50/$1.00", "$1.00/$2.00"]
    results = ["won", "lost", "folded"]
    
    # Generate base date within last 30 days
    days_ago = draw(st.integers(min_value=0, max_value=30))
    base_date = datetime.now(timezone.utc) - timedelta(days=days_ago)
    
    # Generate hand data
    platform = draw(st.sampled_from(platforms))
    game_type = draw(st.sampled_from(game_types))
    game_format = draw(st.sampled_from(game_formats))
    position = draw(st.sampled_from(positions))
    stakes = draw(st.sampled_from(stakes_options))
    result = draw(st.sampled_from(results))
    
    # Generate actions based on result
    if result == "folded":
        actions = {"preflop": [{"action": "fold"}]}
    elif result == "won":
        actions = {
            "preflop": [{"action": "call", "amount": 2.0}],
            "flop": [{"action": "bet", "amount": 5.0}]
        }
    else:  # lost
        actions = {
            "preflop": [{"action": "call", "amount": 2.0}],
            "flop": [{"action": "call", "amount": 5.0}]
        }
    
    pot_size = draw(st.decimals(min_value=Decimal('1.0'), max_value=Decimal('100.0'), places=2))
    
    # Generate unique hand ID
    hand_id = f"hand_{draw(st.integers(min_value=1, max_value=999999))}"
    
    return PokerHand(
        id=hand_id,  # Will be overridden in tests for uniqueness
        user_id=user_id,
        hand_id=hand_id,  # Platform-specific hand ID (required field)
        platform=platform,
        game_type=game_type,
        game_format=game_format,
        stakes=stakes,
        position=position,
        date_played=base_date,
        pot_size=pot_size,
        result=result,
        actions=actions,
        is_play_money=draw(st.booleans())
    )


@st.composite
def statistics_filters_strategy(draw):
    """Generate StatisticsFilters for property testing."""
    # Generate optional date range
    start_date = None
    end_date = None
    if draw(st.booleans()):  # 50% chance of having date filters
        days_back = draw(st.integers(min_value=1, max_value=30))
        start_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        end_date = datetime.now(timezone.utc)
    
    return StatisticsFilters(
        start_date=start_date,
        end_date=end_date,
        platform=draw(st.one_of(st.none(), st.sampled_from(["pokerstars", "ggpoker"]))),
        game_type=draw(st.one_of(st.none(), st.sampled_from(["Hold'em No Limit", "Omaha"]))),
        game_format=draw(st.one_of(st.none(), st.sampled_from(["cash", "tournament"]))),
        position=draw(st.one_of(st.none(), st.sampled_from(["UTG", "BTN", "BB"]))),
        min_hands=draw(st.one_of(st.none(), st.integers(min_value=1, max_value=50)))
    )


class TestStatisticsLoadingReliabilityProperty:
    """Property-based tests for statistics loading reliability."""
    
    @pytest_asyncio.fixture
    async def setup_test_data(self):
        """Setup test data for each test."""
        # Create test database session
        async with test_engine.begin() as conn:
            await conn.run_sync(test_metadata.create_all)
        
        async with TestSessionLocal() as session:
            # Create test user
            user = User(
                id="550e8400-e29b-41d4-a716-446655440000",
                email="reliability@example.com",
                password_hash="hashed_password"
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            
            # Create mock cache service
            mock_cache_service = Mock(spec=StatisticsCacheService)
            mock_cache_service.get_user_statistics = AsyncMock(return_value=None)
            mock_cache_service.set_user_statistics = AsyncMock(return_value=True)
            mock_cache_service.get_trend_data = AsyncMock(return_value=None)
            mock_cache_service.set_trend_data = AsyncMock(return_value=True)
            
            yield session, user, mock_cache_service
            
            await session.close()
        
        async with test_engine.begin() as conn:
            await conn.run_sync(test_metadata.drop_all)
        
        await test_engine.dispose()
    
    @given(st.lists(poker_hand_strategy("550e8400-e29b-41d4-a716-446655440000"), min_size=5, max_size=50))
    @settings(max_examples=30, deadline=10000)
    def test_property_statistics_loading_success(self, hands_data):
        """
        Property: For any valid user with hand data, statistics should load successfully 
        within reasonable time bounds and return valid data.
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user with unique email
                import uuid
                unique_id = str(uuid.uuid4())
                user = User(
                    id=unique_id,
                    email=f"reliability-{unique_id}@example.com",
                    password_hash="hashed_password"
                )
                session.add(user)
                await session.commit()
                
                # Add hands to database with unique IDs
                for i, hand in enumerate(hands_data):
                    import uuid
                    hand_uuid = str(uuid.uuid4())
                    hand.id = hand_uuid
                    hand.hand_id = f"hand_{unique_id}_{i}"  # Platform-specific hand ID
                    hand.user_id = unique_id
                    session.add(hand)
                await session.commit()
                
                # Create mock cache service
                mock_cache_service = Mock(spec=StatisticsCacheService)
                mock_cache_service.get_user_statistics = AsyncMock(return_value=None)
                mock_cache_service.set_user_statistics = AsyncMock(return_value=True)
                
                # Create statistics service
                stats_service = StatisticsService(session, mock_cache_service)
                
                # Property: Statistics should load successfully
                start_time = asyncio.get_event_loop().time()
                result = await stats_service.calculate_basic_statistics(user.id)
                end_time = asyncio.get_event_loop().time()
                
                # Property: Response time should be reasonable (under 5 seconds)
                response_time = end_time - start_time
                assert response_time < 5.0, f"Statistics loading took too long: {response_time}s"
                
                # Property: Result should be valid BasicStatistics
                assert isinstance(result, BasicStatistics)
                assert result.total_hands == len(hands_data)
                
                # Property: Data integrity should be maintained
                assert 0 <= result.vpip <= 100
                assert 0 <= result.pfr <= 100
                assert result.pfr <= result.vpip  # PFR cannot exceed VPIP
                assert result.aggression_factor >= 0
                
                await session.close()
            
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.drop_all)
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(st.lists(poker_hand_strategy("550e8400-e29b-41d4-a716-446655440000"), min_size=10, max_size=30),
           statistics_filters_strategy())
    @settings(max_examples=20, deadline=10000)
    def test_property_retry_logic_with_database_failures(self, hands_data, filters):
        """
        Property: For any database failure scenario, the system should implement 
        exponential backoff retry logic (1s, 2s, 4s delays) and eventually succeed or fail gracefully.
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                user = User(
                    id="550e8400-e29b-41d4-a716-446655440000",
                    email="reliability@example.com",
                    password_hash="hashed_password"
                )
                session.add(user)
                await session.commit()
                
                # Add hands to database
                for hand in hands_data:
                    session.add(hand)
                await session.commit()
                
                # Create mock cache service
                mock_cache_service = Mock(spec=StatisticsCacheService)
                mock_cache_service.get_user_statistics = AsyncMock(return_value=None)
                mock_cache_service.set_user_statistics = AsyncMock(return_value=True)
                
                # Create statistics service
                stats_service = StatisticsService(session, mock_cache_service)
                
                # Mock database to fail first 2 attempts, succeed on 3rd
                original_execute = session.execute
                call_count = 0
                
                async def failing_execute(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    if call_count <= 2:
                        raise DisconnectionError("Connection lost", None, None)
                    return await original_execute(*args, **kwargs)
                
                # Property: Retry logic should handle temporary failures
                with patch.object(session, 'execute', side_effect=failing_execute):
                    start_time = asyncio.get_event_loop().time()
                    result = await stats_service.calculate_basic_statistics(user.id, filters)
                    end_time = asyncio.get_event_loop().time()
                    
                    # Property: Should succeed after retries
                    assert isinstance(result, BasicStatistics)
                    
                    # Property: Should have taken time for retries (at least 3 seconds for 1s + 2s delays)
                    response_time = end_time - start_time
                    assert response_time >= 3.0, f"Retry logic didn't add expected delay: {response_time}s"
                    
                    # Property: Should have attempted 3 times
                    assert call_count == 3
                
                await session.close()
            
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.drop_all)
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(st.lists(poker_hand_strategy("550e8400-e29b-41d4-a716-446655440000"), min_size=5, max_size=20))
    @settings(max_examples=20, deadline=10000)
    def test_property_cache_fallback_on_failure(self, hands_data):
        """
        Property: For any calculation failure, the system should gracefully degrade 
        to cached data when available.
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                user = User(
                    id="550e8400-e29b-41d4-a716-446655440000",
                    email="reliability@example.com",
                    password_hash="hashed_password"
                )
                session.add(user)
                await session.commit()
                
                # Create mock cache service with cached data
                mock_cache_service = Mock(spec=StatisticsCacheService)
                cached_stats = {
                    'total_hands': len(hands_data),
                    'vpip': Decimal('25.0'),
                    'pfr': Decimal('18.0'),
                    'aggression_factor': Decimal('2.5'),
                    'win_rate': Decimal('5.2')
                }
                mock_cache_service.get_user_statistics = AsyncMock(return_value=cached_stats)
                mock_cache_service.set_user_statistics = AsyncMock(return_value=True)
                
                # Create statistics service
                stats_service = StatisticsService(session, mock_cache_service)
                
                # Mock database to always fail
                with patch.object(session, 'execute', side_effect=SQLAlchemyError("Database error")):
                    # Property: Should fallback to cached data
                    result = await stats_service.calculate_basic_statistics(user.id)
                    
                    # Property: Should return cached data
                    assert result == cached_stats
                    
                    # Property: Cache should have been queried
                    mock_cache_service.get_user_statistics.assert_called()
                
                await session.close()
            
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.drop_all)
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(st.lists(poker_hand_strategy("550e8400-e29b-41d4-a716-446655440000"), min_size=1, max_size=10))
    @settings(max_examples=20, deadline=10000)
    def test_property_data_integrity_validation(self, hands_data):
        """
        Property: For any calculated statistics, data integrity validation should 
        catch and correct invalid values before display.
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                user = User(
                    id="550e8400-e29b-41d4-a716-446655440000",
                    email="reliability@example.com",
                    password_hash="hashed_password"
                )
                session.add(user)
                await session.commit()
                
                # Add hands to database
                for hand in hands_data:
                    session.add(hand)
                await session.commit()
                
                # Create mock cache service
                mock_cache_service = Mock(spec=StatisticsCacheService)
                mock_cache_service.get_user_statistics = AsyncMock(return_value=None)
                mock_cache_service.set_user_statistics = AsyncMock(return_value=True)
                
                # Create statistics service
                stats_service = StatisticsService(session, mock_cache_service)
                
                # Property: Data integrity validation should work
                result = await stats_service.calculate_basic_statistics(user.id)
                
                # Property: All values should be within valid ranges
                assert 0 <= result.vpip <= 100, f"VPIP {result.vpip} is out of valid range"
                assert 0 <= result.pfr <= 100, f"PFR {result.pfr} is out of valid range"
                assert result.pfr <= result.vpip, f"PFR {result.pfr} exceeds VPIP {result.vpip}"
                assert result.aggression_factor >= 0, f"Aggression factor {result.aggression_factor} is negative"
                assert result.aggression_factor <= 999, f"Aggression factor {result.aggression_factor} is too high"
                assert result.total_hands >= 0, f"Total hands {result.total_hands} is negative"
                
                await session.close()
            
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.drop_all)
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(statistics_filters_strategy())
    @settings(max_examples=20, deadline=10000)
    def test_property_empty_dataset_handling(self, filters):
        """
        Property: For any user with no hand data, the system should return 
        appropriate empty statistics without errors.
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                user = User(
                    id="550e8400-e29b-41d4-a716-446655440000",
                    email="reliability@example.com",
                    password_hash="hashed_password"
                )
                session.add(user)
                await session.commit()
                
                # Create mock cache service
                mock_cache_service = Mock(spec=StatisticsCacheService)
                mock_cache_service.get_user_statistics = AsyncMock(return_value=None)
                mock_cache_service.set_user_statistics = AsyncMock(return_value=True)
                
                # Create statistics service (no hands in database)
                stats_service = StatisticsService(session, mock_cache_service)
                
                # Property: Should handle empty dataset gracefully
                result = await stats_service.calculate_basic_statistics(user.id, filters)
                
                # Property: Should return valid empty statistics
                assert isinstance(result, BasicStatistics)
                assert result.total_hands == 0
                assert result.vpip == Decimal('0.0')
                assert result.pfr == Decimal('0.0')
                assert result.aggression_factor == Decimal('0.0')
                assert result.win_rate == Decimal('0.0')
                
                await session.close()
            
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.drop_all)
        
        # Run the async test
        asyncio.run(run_test())
    
    @given(st.integers(min_value=1, max_value=3))
    @settings(max_examples=10, deadline=10000)
    def test_property_retry_exhaustion_handling(self, failure_count):
        """
        Property: For any number of consecutive failures exceeding retry limit, 
        the system should raise StatisticsReliabilityError after exhausting retries.
        """
        async def run_test():
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.create_all)
            
            async with TestSessionLocal() as session:
                # Create test user
                user = User(
                    id="550e8400-e29b-41d4-a716-446655440000",
                    email="reliability@example.com",
                    password_hash="hashed_password"
                )
                session.add(user)
                await session.commit()
                
                # Create mock cache service
                mock_cache_service = Mock(spec=StatisticsCacheService)
                mock_cache_service.get_user_statistics = AsyncMock(return_value=None)
                mock_cache_service.set_user_statistics = AsyncMock(return_value=True)
                
                # Create statistics service
                stats_service = StatisticsService(session, mock_cache_service)
                
                # Mock database to fail more times than retry limit
                call_count = 0
                
                async def always_failing_execute(*args, **kwargs):
                    nonlocal call_count
                    call_count += 1
                    raise DisconnectionError("Persistent connection error", None, None)
                
                # Property: Should raise StatisticsReliabilityError after retry exhaustion
                with patch.object(session, 'execute', side_effect=always_failing_execute):
                    with pytest.raises(StatisticsReliabilityError) as exc_info:
                        await stats_service.calculate_basic_statistics(user.id)
                    
                    # Property: Should have attempted maximum retries (3 attempts)
                    assert call_count == 3
                    
                    # Property: Error message should be descriptive
                    assert "failed after 3 attempts" in str(exc_info.value)
                
                await session.close()
            
            async with test_engine.begin() as conn:
                await conn.run_sync(test_metadata.drop_all)
        
        # Run the async test
        asyncio.run(run_test())