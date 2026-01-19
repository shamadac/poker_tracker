"""
Test filtering and trends functionality.
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.services.statistics_service import StatisticsService
from app.schemas.statistics import StatisticsFilters
from app.models.hand import PokerHand
from app.models.user import User


# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine and session
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    test_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    # Ensure engine is properly disposed
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_calculate_filtered_statistics(db_session: AsyncSession):
    """Test comprehensive statistics calculation with filtering."""
    # Create test user
    user = User(
        id="test-user-id",
        email="test@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Create test hands with different dates and platforms
    base_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    hands = []
    for i in range(20):
        hand = PokerHand(
            user_id=user.id,
            hand_id=f"test_hand_{i}",
            platform="pokerstars" if i < 10 else "ggpoker",
            game_type="Hold'em No Limit",
            game_format="cash",
            stakes="$0.50/$1.00",
            date_played=base_date + timedelta(days=i),
            position="BTN" if i % 2 == 0 else "CO",
            player_cards=["As", "Kh"],
            actions={
                "preflop": [{"action": "raise" if i % 3 == 0 else "call", "amount": 3.0}]
            },
            result="won" if i % 2 == 0 else "lost",
            pot_size=Decimal("10.0"),
            is_play_money=False
        )
        hands.append(hand)
    
    db_session.add_all(hands)
    await db_session.commit()
    
    # Test filtering by platform
    stats_service = StatisticsService(db_session)
    
    filters = StatisticsFilters(platform="pokerstars")
    response = await stats_service.calculate_filtered_statistics(user.id, filters)
    
    # Should only include PokerStars hands (first 10)
    assert response.basic_stats.total_hands == 10
    assert response.filters_applied.platform == "pokerstars"
    assert response.sample_size == 10
    
    # Test filtering by date range
    filters = StatisticsFilters(
        start_date=base_date + timedelta(days=10),
        end_date=base_date + timedelta(days=15)
    )
    response = await stats_service.calculate_filtered_statistics(user.id, filters)
    
    # Should include hands from days 10-15 (6 hands)
    assert response.basic_stats.total_hands == 6


@pytest.mark.asyncio
async def test_calculate_performance_trends(db_session: AsyncSession):
    """Test performance trends calculation."""
    # Create test user
    user = User(
        id="test-user-trends",
        email="trends@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Create hands over time with improving VPIP
    base_date = datetime.now(timezone.utc) - timedelta(days=30)
    
    hands = []
    for i in range(30):
        # Create multiple hands per day to ensure sufficient sample size
        for hand_num in range(10):  # 10 hands per day
            # Create hands with gradually improving VPIP (more selective play)
            vpip_action = "call" if i < 20 else "fold"  # Improve over time
            
            hand = PokerHand(
                user_id=user.id,
                hand_id=f"trend_hand_{i}_{hand_num}",
                platform="pokerstars",
                game_type="Hold'em No Limit",
                game_format="cash",
                stakes="$0.50/$1.00",
                date_played=base_date + timedelta(days=i, hours=hand_num),
                position="BTN",
                player_cards=["As", "Kh"],
                actions={
                    "preflop": [{"action": vpip_action, "amount": 2.0 if vpip_action == "call" else 0}]
                },
                result="won",
                pot_size=Decimal("5.0"),
                is_play_money=False
            )
            hands.append(hand)
    
    db_session.add_all(hands)
    await db_session.commit()
    
    # Calculate trends
    stats_service = StatisticsService(db_session)
    trends = await stats_service.calculate_performance_trends(
        user.id,
        period="30d",
        metrics=["vpip"]
    )
    
    assert len(trends) == 1
    vpip_trend = trends[0]
    assert vpip_trend.metric_name == "vpip"
    assert vpip_trend.time_period == "30d"
    assert len(vpip_trend.data_points) > 0
    
    # Should detect downward trend in VPIP (improvement)
    assert vpip_trend.trend_direction in ["down", "stable"]


@pytest.mark.asyncio
async def test_calculate_session_statistics(db_session: AsyncSession):
    """Test session statistics calculation."""
    # Create test user
    user = User(
        id="test-user-sessions",
        email="sessions@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Create hands on different days (sessions)
    base_date = datetime.now(timezone.utc) - timedelta(days=5)
    
    hands = []
    for day in range(3):  # 3 different sessions
        for hand_num in range(10):  # 10 hands per session
            hand = PokerHand(
                user_id=user.id,
                hand_id=f"session_hand_{day}_{hand_num}",
                platform="pokerstars",
                game_type="Hold'em No Limit",
                game_format="cash",
                stakes="$0.50/$1.00",
                date_played=base_date + timedelta(days=day, minutes=hand_num * 10),  # Use minutes instead of hours
                position="BTN",
                player_cards=["As", "Kh"],
                actions={
                    "preflop": [{"action": "call", "amount": 2.0}]
                },
                result="won" if hand_num % 2 == 0 else "lost",
                pot_size=Decimal("8.0"),
                is_play_money=False
            )
            hands.append(hand)
    
    db_session.add_all(hands)
    await db_session.commit()
    
    # Calculate session statistics
    stats_service = StatisticsService(db_session)
    sessions = await stats_service.calculate_session_statistics(user.id)
    
    # Should have 3 sessions
    assert len(sessions) == 3
    
    # Each session should have 10 hands
    for session in sessions:
        assert session.hands_played == 10
        assert session.vpip > 0  # All hands had VPIP action
        assert session.duration_minutes >= 0


@pytest.mark.asyncio
async def test_minimum_hands_filter(db_session: AsyncSession):
    """Test minimum hands filtering."""
    # Create test user
    user = User(
        id="test-user-min-hands",
        email="minhands@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Create only 5 hands
    hands = []
    for i in range(5):
        hand = PokerHand(
            user_id=user.id,
            hand_id=f"min_hand_{i}",
            platform="pokerstars",
            game_type="Hold'em No Limit",
            game_format="cash",
            stakes="$0.50/$1.00",
            date_played=datetime.now(timezone.utc),
            position="BTN",
            player_cards=["As", "Kh"],
            actions={"preflop": [{"action": "call", "amount": 2.0}]},
            result="won",
            pot_size=Decimal("5.0"),
            is_play_money=False
        )
        hands.append(hand)
    
    db_session.add_all(hands)
    await db_session.commit()
    
    # Test with minimum hands requirement
    stats_service = StatisticsService(db_session)
    
    # Should work with min_hands=5
    filters = StatisticsFilters(min_hands=5)
    response = await stats_service.calculate_filtered_statistics(user.id, filters)
    assert response.basic_stats.total_hands == 5
    
    # Should raise error with min_hands=10
    filters = StatisticsFilters(min_hands=10)
    with pytest.raises(ValueError, match="Insufficient hands"):
        await stats_service.calculate_filtered_statistics(user.id, filters)