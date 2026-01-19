"""
Test statistics service functionality.
"""
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.user import User
from app.models.hand import PokerHand
from app.services.statistics_service import StatisticsService
from app.schemas.statistics import StatisticsFilters


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


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user."""
    user = User(
        id="550e8400-e29b-41d4-a716-446655440000",  # Valid UUID format
        email="test@example.com",
        password_hash="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def sample_hands(db_session: AsyncSession, test_user: User):
    """Create sample poker hands for testing."""
    hands = []
    
    # Hand 1: VPIP hand (called preflop), won
    hand1 = PokerHand(
        user_id=test_user.id,
        hand_id="HAND001",
        platform="pokerstars",
        game_type="Hold'em",
        game_format="cash",
        stakes="$0.50/$1.00",
        position="BTN",
        player_cards=["As", "Kh"],
        actions={
            "preflop": [{"action": "call", "amount": 1.0}],
            "flop": [{"action": "bet", "amount": 2.0}]
        },
        result="won",
        pot_size=Decimal("10.00"),
        date_played=datetime.now(timezone.utc)
    )
    hands.append(hand1)
    
    # Hand 2: PFR hand (raised preflop), lost
    hand2 = PokerHand(
        user_id=test_user.id,
        hand_id="HAND002",
        platform="pokerstars",
        game_type="Hold'em",
        game_format="cash",
        stakes="$0.50/$1.00",
        position="CO",
        player_cards=["Qd", "Qc"],
        actions={
            "preflop": [{"action": "raise", "amount": 3.0}],
            "flop": [{"action": "bet", "amount": 5.0}],
            "turn": [{"action": "call", "amount": 10.0}]
        },
        result="lost",
        pot_size=Decimal("25.00"),
        date_played=datetime.now(timezone.utc)
    )
    hands.append(hand2)
    
    # Hand 3: Folded preflop (not VPIP)
    hand3 = PokerHand(
        user_id=test_user.id,
        hand_id="HAND003",
        platform="pokerstars",
        game_type="Hold'em",
        game_format="cash",
        stakes="$0.50/$1.00",
        position="UTG",
        player_cards=["7c", "2h"],
        actions={
            "preflop": [{"action": "fold"}]
        },
        result="folded",
        pot_size=Decimal("0.00"),
        date_played=datetime.now(timezone.utc)
    )
    hands.append(hand3)
    
    # Hand 4: Big blind, no raise (not VPIP)
    hand4 = PokerHand(
        user_id=test_user.id,
        hand_id="HAND004",
        platform="pokerstars",
        game_type="Hold'em",
        game_format="cash",
        stakes="$0.50/$1.00",
        position="BB",
        player_cards=["Jh", "9s"],
        actions={
            "preflop": [{"action": "check"}],
            "flop": [{"action": "check"}],
            "turn": [{"action": "fold"}]
        },
        result="folded",
        pot_size=Decimal("2.00"),
        date_played=datetime.now(timezone.utc)
    )
    hands.append(hand4)
    
    # Hand 5: Tournament hand
    hand5 = PokerHand(
        user_id=test_user.id,
        hand_id="HAND005",
        platform="pokerstars",
        game_type="Hold'em",
        game_format="tournament",
        stakes="$10+$1",
        position="SB",
        player_cards=["Ah", "Ad"],
        actions={
            "preflop": [{"action": "raise", "amount": 100}],
            "flop": [{"action": "bet", "amount": 200}]
        },
        result="won",
        pot_size=Decimal("500.00"),
        tournament_info={"tournament_id": "T123", "level": 3},
        date_played=datetime.now(timezone.utc)
    )
    hands.append(hand5)
    
    # Add all hands to database
    for hand in hands:
        db_session.add(hand)
    
    await db_session.commit()
    return hands


@pytest.mark.asyncio
async def test_calculate_basic_statistics(db_session: AsyncSession, test_user: User, sample_hands):
    """Test basic statistics calculation."""
    stats_service = StatisticsService(db_session)
    
    # Calculate statistics
    basic_stats = await stats_service.calculate_basic_statistics(test_user.id)
    
    # Verify results
    assert basic_stats.total_hands == 5
    
    # VPIP: Hands 1, 2, and 5 are VPIP (3 out of 5 = 60%)
    assert basic_stats.vpip == Decimal('60.0')
    
    # PFR: Hands 2 and 5 are PFR (2 out of 5 = 40%)
    assert basic_stats.pfr == Decimal('40.0')
    
    # Aggression factor should be calculated
    assert basic_stats.aggression_factor >= Decimal('0.0')
    
    # Win rate should be calculated
    assert isinstance(basic_stats.win_rate, Decimal)


@pytest.mark.asyncio
async def test_calculate_basic_statistics_with_filters(db_session: AsyncSession, test_user: User, sample_hands):
    """Test basic statistics calculation with filters."""
    stats_service = StatisticsService(db_session)
    
    # Filter for cash games only
    filters = StatisticsFilters(cash_only=True)
    basic_stats = await stats_service.calculate_basic_statistics(test_user.id, filters)
    
    # Should exclude tournament hand (hand 5)
    assert basic_stats.total_hands == 4
    
    # Filter for specific position
    filters = StatisticsFilters(position="BTN")
    basic_stats = await stats_service.calculate_basic_statistics(test_user.id, filters)
    
    # Should only include BTN hand (hand 1)
    assert basic_stats.total_hands == 1
    assert basic_stats.vpip == Decimal('100.0')  # 1 out of 1


@pytest.mark.asyncio
async def test_calculate_positional_statistics(db_session: AsyncSession, test_user: User, sample_hands):
    """Test positional statistics calculation."""
    stats_service = StatisticsService(db_session)
    
    # Calculate positional statistics
    positional_stats = await stats_service.calculate_positional_statistics(test_user.id)
    
    # Should have statistics for positions with enough hands
    # Note: The service filters out positions with < 5 hands, so we might not get all positions
    assert isinstance(positional_stats, list)
    
    # Each position should have valid statistics
    for pos_stat in positional_stats:
        assert pos_stat.hands_played > 0
        assert 0 <= pos_stat.vpip <= 100
        assert 0 <= pos_stat.pfr <= 100
        assert pos_stat.aggression_factor >= 0


@pytest.mark.asyncio
async def test_empty_database(db_session: AsyncSession, test_user: User):
    """Test statistics calculation with no hands."""
    stats_service = StatisticsService(db_session)
    
    # Calculate statistics with no hands
    basic_stats = await stats_service.calculate_basic_statistics(test_user.id)
    
    # Should return zero statistics
    assert basic_stats.total_hands == 0
    assert basic_stats.vpip == Decimal('0.0')
    assert basic_stats.pfr == Decimal('0.0')
    assert basic_stats.aggression_factor == Decimal('0.0')
    assert basic_stats.win_rate == Decimal('0.0')


@pytest.mark.asyncio
async def test_vpip_calculation_edge_cases(db_session: AsyncSession, test_user: User):
    """Test VPIP calculation edge cases."""
    stats_service = StatisticsService(db_session)
    
    # Create edge case hands
    # BB with raise (should be VPIP)
    bb_raise_hand = PokerHand(
        user_id=test_user.id,
        hand_id="BB_RAISE",
        platform="pokerstars",
        position="BB",
        actions={
            "preflop": [{"action": "raise", "amount": 3.0}]
        },
        result="won",
        pot_size=Decimal("5.00"),
        date_played=datetime.now(timezone.utc)
    )
    
    # BB call raise (should be VPIP)
    bb_call_hand = PokerHand(
        user_id=test_user.id,
        hand_id="BB_CALL",
        platform="pokerstars",
        position="BB",
        actions={
            "preflop": [{"action": "call", "amount": 2.0}]
        },
        result="lost",
        pot_size=Decimal("4.00"),
        date_played=datetime.now(timezone.utc)
    )
    
    db_session.add(bb_raise_hand)
    db_session.add(bb_call_hand)
    await db_session.commit()
    
    # Calculate statistics
    basic_stats = await stats_service.calculate_basic_statistics(test_user.id)
    
    # Both BB hands should count as VPIP
    assert basic_stats.total_hands == 2
    assert basic_stats.vpip == Decimal('100.0')  # Both hands are VPIP


@pytest.mark.asyncio
async def test_aggression_factor_calculation(db_session: AsyncSession, test_user: User):
    """Test aggression factor calculation."""
    stats_service = StatisticsService(db_session)
    
    # Create hands with known aggressive/passive actions
    aggressive_hand = PokerHand(
        user_id=test_user.id,
        hand_id="AGG_HAND",
        platform="pokerstars",
        position="BTN",
        actions={
            "preflop": [{"action": "raise", "amount": 3.0}],
            "flop": [{"action": "bet", "amount": 5.0}],
            "turn": [{"action": "raise", "amount": 15.0}]
        },
        result="won",
        pot_size=Decimal("30.00"),
        date_played=datetime.now(timezone.utc)
    )
    
    passive_hand = PokerHand(
        user_id=test_user.id,
        hand_id="PASS_HAND",
        platform="pokerstars",
        position="CO",
        actions={
            "preflop": [{"action": "call", "amount": 1.0}],
            "flop": [{"action": "check"}],
            "turn": [{"action": "call", "amount": 5.0}]
        },
        result="lost",
        pot_size=Decimal("10.00"),
        date_played=datetime.now(timezone.utc)
    )
    
    db_session.add(aggressive_hand)
    db_session.add(passive_hand)
    await db_session.commit()
    
    # Calculate statistics
    basic_stats = await stats_service.calculate_basic_statistics(test_user.id)
    
    # Aggression factor = (bets + raises) / (calls + checks)
    # Aggressive hand: 3 aggressive actions (raise, bet, raise)
    # Passive hand: 3 passive actions (call, check, call)
    # AF = 3 / 3 = 1.0
    assert basic_stats.aggression_factor == Decimal('1.00')


@pytest.mark.asyncio
async def test_calculate_advanced_statistics(db_session: AsyncSession, test_user: User):
    """Test advanced statistics calculation."""
    stats_service = StatisticsService(db_session)
    
    # Create hands with advanced statistics scenarios
    # 3-bet hand
    three_bet_hand = PokerHand(
        user_id=test_user.id,
        hand_id="3BET_HAND",
        platform="pokerstars",
        position="CO",
        actions={
            "preflop": [
                {"action": "raise", "amount": 3.0},  # Initial raise
                {"action": "raise", "amount": 9.0}   # 3-bet
            ]
        },
        result="won",
        pot_size=Decimal("20.00"),
        date_played=datetime.now(timezone.utc)
    )
    
    # C-bet hand
    c_bet_hand = PokerHand(
        user_id=test_user.id,
        hand_id="CBET_HAND",
        platform="pokerstars",
        position="BTN",
        actions={
            "preflop": [{"action": "raise", "amount": 3.0}],
            "flop": [{"action": "bet", "amount": 5.0}]  # C-bet
        },
        result="won",
        pot_size=Decimal("15.00"),
        date_played=datetime.now(timezone.utc)
    )
    
    # Check-raise hand
    check_raise_hand = PokerHand(
        user_id=test_user.id,
        hand_id="CR_HAND",
        platform="pokerstars",
        position="BB",
        actions={
            "flop": [
                {"action": "check"},
                {"action": "raise", "amount": 10.0}  # Check-raise after opponent bet
            ]
        },
        result="won",
        pot_size=Decimal("25.00"),
        date_played=datetime.now(timezone.utc)
    )
    
    db_session.add(three_bet_hand)
    db_session.add(c_bet_hand)
    db_session.add(check_raise_hand)
    await db_session.commit()
    
    # Calculate advanced statistics
    advanced_stats = await stats_service.calculate_advanced_statistics(test_user.id)
    
    # Verify results
    assert isinstance(advanced_stats.three_bet_percentage, Decimal)
    assert isinstance(advanced_stats.c_bet_flop, Decimal)
    assert isinstance(advanced_stats.check_raise_flop, Decimal)
    assert isinstance(advanced_stats.red_line_winnings, Decimal)
    assert isinstance(advanced_stats.blue_line_winnings, Decimal)
    assert isinstance(advanced_stats.expected_value, Decimal)
    assert isinstance(advanced_stats.variance, Decimal)


@pytest.mark.asyncio
async def test_calculate_tournament_statistics(db_session: AsyncSession, test_user: User):
    """Test tournament statistics calculation."""
    stats_service = StatisticsService(db_session)
    
    # Create tournament hands
    tournament_hand1 = PokerHand(
        user_id=test_user.id,
        hand_id="TOURNEY1",
        platform="pokerstars",
        game_format="tournament",
        position="BTN",
        actions={
            "preflop": [{"action": "raise", "amount": 100}]
        },
        result="won",
        pot_size=Decimal("500.00"),
        tournament_info={
            "tournament_id": "T001",
            "buy_in": 10.00,  # Use float instead of Decimal
            "total_players": 100,
            "finish_position": 15,
            "bubble_position": 18
        },
        date_played=datetime.now(timezone.utc)
    )
    
    tournament_hand2 = PokerHand(
        user_id=test_user.id,
        hand_id="TOURNEY2",
        platform="pokerstars",
        game_format="tournament",
        position="CO",
        actions={
            "preflop": [{"action": "fold"}]
        },
        result="folded",
        pot_size=Decimal("0.00"),
        tournament_info={
            "tournament_id": "T002",
            "buy_in": 20.00,  # Use float instead of Decimal
            "total_players": 50,
            "finish_position": 5,  # Final table
            "bubble_position": 9
        },
        date_played=datetime.now(timezone.utc)
    )
    
    db_session.add(tournament_hand1)
    db_session.add(tournament_hand2)
    await db_session.commit()
    
    # Calculate tournament statistics
    tournament_stats = await stats_service.calculate_tournament_statistics(test_user.id)
    
    # Verify results
    assert tournament_stats is not None
    assert tournament_stats.tournaments_played == 2
    assert tournament_stats.final_table_appearances == 1  # Tournament 2 finished 5th
    assert tournament_stats.total_buy_ins == Decimal('30.00')  # 10 + 20
    assert isinstance(tournament_stats.roi, Decimal)
    assert isinstance(tournament_stats.cash_percentage, Decimal)


@pytest.mark.asyncio
async def test_advanced_statistics_empty_database(db_session: AsyncSession, test_user: User):
    """Test advanced statistics calculation with no hands."""
    stats_service = StatisticsService(db_session)
    
    # Calculate advanced statistics with no hands
    advanced_stats = await stats_service.calculate_advanced_statistics(test_user.id)
    
    # Should return zero statistics
    assert advanced_stats.three_bet_percentage == Decimal('0.0')
    assert advanced_stats.c_bet_flop == Decimal('0.0')
    assert advanced_stats.check_raise_flop == Decimal('0.0')
    assert advanced_stats.red_line_winnings == Decimal('0.0')
    assert advanced_stats.blue_line_winnings == Decimal('0.0')
    assert advanced_stats.expected_value == Decimal('0.0')
    assert advanced_stats.variance == Decimal('0.0')


@pytest.mark.asyncio
async def test_tournament_statistics_empty_database(db_session: AsyncSession, test_user: User):
    """Test tournament statistics calculation with no tournament hands."""
    stats_service = StatisticsService(db_session)
    
    # Calculate tournament statistics with no tournament hands
    tournament_stats = await stats_service.calculate_tournament_statistics(test_user.id)
    
    # Should return None
    assert tournament_stats is None


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])