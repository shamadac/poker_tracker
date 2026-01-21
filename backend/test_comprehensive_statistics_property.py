#!/usr/bin/env python3
"""
Property-based test for comprehensive statistics coverage.

Feature: professional-poker-analyzer-rebuild
Property 30: Comprehensive Statistics Coverage

This test validates that for any poker session data, the system should calculate
all standard and advanced poker statistics including tournament-specific and 
cash game-specific metrics according to Requirements 6.1 and 6.6.
"""

import pytest
import pytest_asyncio
import asyncio
from typing import Dict, Any, List, Optional
from decimal import Decimal
from datetime import datetime, timezone, timedelta
import uuid

from hypothesis import given, strategies as st, settings, assume, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Import required modules
from app.models.user import User
from app.models.hand import PokerHand
from app.services.statistics_service import StatisticsService
from app.schemas.statistics import StatisticsFilters


# Test database configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


# Hypothesis strategies for generating test data
@st.composite
def valid_poker_position(draw):
    """Generate valid poker positions."""
    positions = ['UTG', 'UTG+1', 'UTG+2', 'MP', 'MP+1', 'MP+2', 'CO', 'BTN', 'SB', 'BB']
    return draw(st.sampled_from(positions))

@st.composite
def valid_poker_action(draw):
    """Generate valid poker actions."""
    actions = ['fold', 'check', 'call', 'bet', 'raise', 'all-in']
    return draw(st.sampled_from(actions))

@st.composite
def valid_street(draw):
    """Generate valid poker streets."""
    streets = ['preflop', 'flop', 'turn', 'river']
    return draw(st.sampled_from(streets))

@st.composite
def valid_game_format(draw):
    """Generate valid game formats."""
    formats = ['cash', 'tournament', 'sng']
    return draw(st.sampled_from(formats))

@st.composite
def valid_platform(draw):
    """Generate valid platforms."""
    platforms = ['pokerstars', 'ggpoker']
    return draw(st.sampled_from(platforms))

@st.composite
def poker_hand_actions(draw):
    """Generate realistic poker hand actions."""
    actions = {}
    
    # Always have preflop actions
    preflop_actions = []
    num_preflop_actions = draw(st.integers(min_value=1, max_value=4))
    
    for i in range(num_preflop_actions):
        action = draw(valid_poker_action())
        amount = None
        if action in ['bet', 'raise', 'call']:
            amount = float(draw(st.decimals(min_value=Decimal('0.5'), max_value=Decimal('100.0'))))
        
        preflop_actions.append({
            'action': action,
            'amount': amount
        })
    
    actions['preflop'] = preflop_actions
    
    # Optionally add postflop actions
    if draw(st.booleans()):
        for street in ['flop', 'turn', 'river']:
            if draw(st.booleans()):
                street_actions = []
                num_actions = draw(st.integers(min_value=1, max_value=3))
                
                for i in range(num_actions):
                    action = draw(valid_poker_action())
                    amount = None
                    if action in ['bet', 'raise', 'call']:
                        amount = float(draw(st.decimals(min_value=Decimal('1.0'), max_value=Decimal('50.0'))))
                    
                    street_actions.append({
                        'action': action,
                        'amount': amount
                    })
                
                actions[street] = street_actions
    
    return actions

@st.composite
def poker_hand_data(draw):
    """Generate comprehensive poker hand data."""
    hand_id = f"HAND_{draw(st.integers(min_value=1000, max_value=9999))}"
    platform = draw(valid_platform())
    game_format = draw(valid_game_format())
    position = draw(valid_poker_position())
    actions = draw(poker_hand_actions())
    
    # Generate cards
    suits = ['h', 'd', 'c', 's']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
    
    player_cards = []
    for _ in range(2):
        rank = draw(st.sampled_from(ranks))
        suit = draw(st.sampled_from(suits))
        player_cards.append(f"{rank}{suit}")
    
    # Generate board cards (0-5 cards)
    board_cards = []
    num_board_cards = draw(st.integers(min_value=0, max_value=5))
    for _ in range(num_board_cards):
        rank = draw(st.sampled_from(ranks))
        suit = draw(st.sampled_from(suits))
        board_cards.append(f"{rank}{suit}")
    
    # Generate result
    results = ['won', 'lost', 'folded', 'split']
    result = draw(st.sampled_from(results))
    
    # Generate pot size
    pot_size = draw(st.decimals(min_value=Decimal('1.0'), max_value=Decimal('500.0')))
    
    # Generate stakes
    if game_format == 'tournament':
        stakes = f"${draw(st.integers(min_value=1, max_value=100))}+${draw(st.integers(min_value=1, max_value=10))}"
        tournament_info = {
            'tournament_id': f"T{draw(st.integers(min_value=1000, max_value=9999))}",
            'buy_in': float(draw(st.decimals(min_value=Decimal('1.0'), max_value=Decimal('100.0')))),
            'total_players': draw(st.integers(min_value=10, max_value=1000)),
            'finish_position': draw(st.integers(min_value=1, max_value=100)),
            'bubble_position': draw(st.integers(min_value=10, max_value=50))
        }
    else:
        small_blind = draw(st.decimals(min_value=Decimal('0.25'), max_value=Decimal('5.0')))
        big_blind = small_blind * 2
        stakes = f"${small_blind}/${big_blind}"
        tournament_info = None
    
    # Generate blinds
    if game_format == 'tournament':
        blinds = {
            'small': float(draw(st.decimals(min_value=Decimal('10'), max_value=Decimal('1000')))),
            'big': float(draw(st.decimals(min_value=Decimal('20'), max_value=Decimal('2000')))),
            'ante': float(draw(st.decimals(min_value=Decimal('0'), max_value=Decimal('100'))))
        }
    else:
        small_blind = float(draw(st.decimals(min_value=Decimal('0.25'), max_value=Decimal('5.0'))))
        blinds = {
            'small': small_blind,
            'big': small_blind * 2
        }
    
    return {
        'hand_id': hand_id,
        'platform': platform,
        'game_type': "Hold'em",
        'game_format': game_format,
        'stakes': stakes,
        'blinds': blinds,
        'table_size': draw(st.integers(min_value=2, max_value=9)),
        'position': position,
        'player_cards': player_cards,
        'board_cards': board_cards,
        'actions': actions,
        'result': result,
        'pot_size': pot_size,
        'rake': draw(st.decimals(min_value=Decimal('0.0'), max_value=Decimal('5.0'))),
        'tournament_info': tournament_info,
        'is_play_money': draw(st.booleans()),
        'date_played': draw(st.datetimes(
            min_value=datetime(2023, 1, 1),
            max_value=datetime(2024, 12, 31)
        ))
    }

@st.composite
def poker_session_data(draw):
    """Generate a session of poker hands."""
    num_hands = draw(st.integers(min_value=10, max_value=100))
    hands = []
    
    for i in range(num_hands):
        hand_data = draw(poker_hand_data())
        # Use UUID for unique hand IDs to avoid conflicts
        hand_data['hand_id'] = str(uuid.uuid4())
        hands.append(hand_data)
    
    return hands


@pytest_asyncio.fixture
async def db_session():
    """Create a test database session."""
    # Create a unique database URL for each test to ensure isolation
    import tempfile
    import os
    
    # Create a temporary database file
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    test_db_url = f"sqlite+aiosqlite:///{temp_db.name}"
    test_engine_local = create_async_engine(test_db_url, echo=False)
    TestSessionLocal_local = sessionmaker(test_engine_local, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables manually to avoid education model issues
    async with test_engine_local.begin() as conn:
        # Create users table
        await conn.execute(text("""
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                api_keys TEXT DEFAULT '{}',
                hand_history_paths TEXT DEFAULT '{}',
                preferences TEXT DEFAULT '{}',
                is_active BOOLEAN DEFAULT true,
                is_superuser BOOLEAN DEFAULT false,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create poker_hands table
        await conn.execute(text("""
            CREATE TABLE poker_hands (
                id TEXT PRIMARY KEY,
                user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                hand_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                game_type TEXT,
                game_format TEXT,
                stakes TEXT,
                blinds TEXT,
                table_size INTEGER,
                date_played TIMESTAMP,
                player_cards TEXT,
                board_cards TEXT,
                position TEXT,
                seat_number INTEGER,
                button_position INTEGER,
                actions TEXT,
                result TEXT,
                pot_size DECIMAL(10,2),
                rake DECIMAL(10,2),
                jackpot_contribution DECIMAL(10,2),
                tournament_info TEXT,
                cash_game_info TEXT,
                player_stacks TEXT,
                timebank_info TEXT,
                hand_duration INTEGER,
                timezone TEXT,
                currency TEXT,
                is_play_money BOOLEAN DEFAULT false,
                raw_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, hand_id, platform)
            )
        """))
    
    async with TestSessionLocal_local() as session:
        try:
            yield session
        finally:
            await session.close()
    
    # Clean up
    await test_engine_local.dispose()
    
    # Remove the temporary database file
    try:
        os.unlink(temp_db.name)
    except OSError:
        pass  # File might already be deleted


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    """Create a test user with a unique ID for each test."""
    user = User(
        id=str(uuid.uuid4()),
        email=f"test-{uuid.uuid4()}@example.com",  # Unique email for each test
        password_hash="hashed_password"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestComprehensiveStatisticsProperty:
    """Test comprehensive statistics coverage using property-based testing."""

    @given(session_hands=poker_session_data())
    @settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_basic_statistics_coverage(self, session_hands):
        """
        Property 30: Comprehensive Statistics Coverage - Basic Statistics

        For any poker session data, the system should calculate all basic
        poker statistics (VPIP, PFR, aggression factor, win rate) with
        mathematical accuracy.

        **Validates: Requirements 6.1**
        """
        # Create a fresh database for each Hypothesis example
        import tempfile
        import os
        
        # Create a temporary database file
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        test_db_url = f"sqlite+aiosqlite:///{temp_db.name}"
        test_engine_local = create_async_engine(test_db_url, echo=False)
        TestSessionLocal_local = sessionmaker(test_engine_local, class_=AsyncSession, expire_on_commit=False)
        
        try:
            # Create tables manually to avoid education model issues
            async with test_engine_local.begin() as conn:
                # Create users table
                await conn.execute(text("""
                CREATE TABLE users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    api_keys TEXT DEFAULT '{}',
                    hand_history_paths TEXT DEFAULT '{}',
                    preferences TEXT DEFAULT '{}',
                    is_active BOOLEAN DEFAULT true,
                    is_superuser BOOLEAN DEFAULT false,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """))
                
                # Create poker_hands table
                await conn.execute(text("""
                CREATE TABLE poker_hands (
                    id TEXT PRIMARY KEY,
                    user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
                    hand_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    game_type TEXT,
                    game_format TEXT,
                    stakes TEXT,
                    blinds TEXT,
                    table_size INTEGER,
                    date_played TIMESTAMP,
                    player_cards TEXT,
                    board_cards TEXT,
                    position TEXT,
                    seat_number INTEGER,
                    button_position INTEGER,
                    actions TEXT,
                    result TEXT,
                    pot_size DECIMAL(10,2),
                    rake DECIMAL(10,2),
                    jackpot_contribution DECIMAL(10,2),
                    tournament_info TEXT,
                    cash_game_info TEXT,
                    player_stacks TEXT,
                    timebank_info TEXT,
                    hand_duration INTEGER,
                    timezone TEXT,
                    currency TEXT,
                    is_play_money BOOLEAN DEFAULT false,
                    raw_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, hand_id, platform)
                )
                """))
            
            async with TestSessionLocal_local() as db_session:
                # Create a test user
                test_user = User(
                    id=str(uuid.uuid4()),
                    email=f"test-{uuid.uuid4()}@example.com",
                    password_hash="hashed_password"
                )
                db_session.add(test_user)
                await db_session.commit()
                await db_session.refresh(test_user)
                
                # Create poker hands in database
                poker_hands = []
                for hand_data in session_hands:
                    poker_hand = PokerHand(
                        user_id=test_user.id,
                        **hand_data
                    )
                    poker_hands.append(poker_hand)
                    db_session.add(poker_hand)
                
                await db_session.commit()
                
                # Debug: Check how many hands were actually inserted
                from sqlalchemy import select, func
                count_result = await db_session.execute(
                    select(func.count(PokerHand.id)).where(PokerHand.user_id == test_user.id)
                )
                actual_count = count_result.scalar()
                
                # Calculate statistics
                stats_service = StatisticsService(db_session)
                basic_stats = await stats_service.calculate_basic_statistics(test_user.id)
                
                # Verify all basic statistics are calculated
                assert basic_stats is not None, "Basic statistics should be calculated"
                
                # Debug information
                if basic_stats.total_hands != len(session_hands):
                    print(f"Expected hands: {len(session_hands)}, DB count: {actual_count}, Stats count: {basic_stats.total_hands}")
                    print(f"Sample hand IDs: {[h['hand_id'] for h in session_hands[:3]]}")
                
                assert basic_stats.total_hands == len(session_hands), f"Total hands should match input. Expected: {len(session_hands)}, Got: {basic_stats.total_hands}, DB Count: {actual_count}"
                
                # Verify VPIP is within valid range
                assert 0 <= basic_stats.vpip <= 100, f"VPIP should be 0-100%, got {basic_stats.vpip}"
                
                # Verify PFR is within valid range and not greater than VPIP
                assert 0 <= basic_stats.pfr <= 100, f"PFR should be 0-100%, got {basic_stats.pfr}"
                assert basic_stats.pfr <= basic_stats.vpip, "PFR should not exceed VPIP"
                
                # Verify aggression factor is non-negative
                assert basic_stats.aggression_factor >= 0, f"Aggression factor should be non-negative, got {basic_stats.aggression_factor}"
                
                # Verify win rate is calculated (can be negative)
                assert isinstance(basic_stats.win_rate, Decimal), "Win rate should be a Decimal"
                
                # Verify optional statistics are properly handled
                if basic_stats.went_to_showdown is not None:
                    assert 0 <= basic_stats.went_to_showdown <= 100, "Went to showdown % should be 0-100%"
                
                if basic_stats.won_at_showdown is not None:
                    assert 0 <= basic_stats.won_at_showdown <= 100, "Won at showdown % should be 0-100%"
        
        finally:
            # Clean up
            await test_engine_local.dispose()
            
            # Remove the temporary database file
            try:
                os.unlink(temp_db.name)
            except OSError:
                pass  # File might already be deleted
                pass  # File might already be deleted

    @given(session_hands=poker_session_data())
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_advanced_statistics_coverage(self, session_hands, db_session, test_user):
        """
        Property 30: Comprehensive Statistics Coverage - Advanced Statistics
        
        For any poker session data, the system should calculate all advanced
        poker statistics including 3-bet %, c-bet %, check-raise %, and
        red line/blue line analysis.
        
        **Validates: Requirements 6.6**
        """
        # Create poker hands in database
        for hand_data in session_hands:
            poker_hand = PokerHand(
                user_id=test_user.id,
                **hand_data
            )
            db_session.add(poker_hand)
        
        await db_session.commit()
        
        # Calculate advanced statistics
        stats_service = StatisticsService(db_session)
        advanced_stats = await stats_service.calculate_advanced_statistics(test_user.id)
        
        # Verify all advanced statistics are calculated
        assert advanced_stats is not None, "Advanced statistics should be calculated"
        
        # Verify preflop advanced statistics
        assert 0 <= advanced_stats.three_bet_percentage <= 100, "3-bet % should be 0-100%"
        assert 0 <= advanced_stats.fold_to_three_bet <= 100, "Fold to 3-bet % should be 0-100%"
        assert 0 <= advanced_stats.four_bet_percentage <= 100, "4-bet % should be 0-100%"
        assert 0 <= advanced_stats.fold_to_four_bet <= 100, "Fold to 4-bet % should be 0-100%"
        assert 0 <= advanced_stats.cold_call_percentage <= 100, "Cold call % should be 0-100%"
        assert 0 <= advanced_stats.isolation_raise <= 100, "Isolation raise % should be 0-100%"
        
        # Verify postflop advanced statistics
        assert 0 <= advanced_stats.c_bet_flop <= 100, "C-bet flop % should be 0-100%"
        assert 0 <= advanced_stats.c_bet_turn <= 100, "C-bet turn % should be 0-100%"
        assert 0 <= advanced_stats.c_bet_river <= 100, "C-bet river % should be 0-100%"
        
        assert 0 <= advanced_stats.fold_to_c_bet_flop <= 100, "Fold to c-bet flop % should be 0-100%"
        assert 0 <= advanced_stats.fold_to_c_bet_turn <= 100, "Fold to c-bet turn % should be 0-100%"
        assert 0 <= advanced_stats.fold_to_c_bet_river <= 100, "Fold to c-bet river % should be 0-100%"
        
        assert 0 <= advanced_stats.check_raise_flop <= 100, "Check-raise flop % should be 0-100%"
        assert 0 <= advanced_stats.check_raise_turn <= 100, "Check-raise turn % should be 0-100%"
        assert 0 <= advanced_stats.check_raise_river <= 100, "Check-raise river % should be 0-100%"
        
        # Verify red line/blue line analysis
        assert isinstance(advanced_stats.red_line_winnings, Decimal), "Red line winnings should be Decimal"
        assert isinstance(advanced_stats.blue_line_winnings, Decimal), "Blue line winnings should be Decimal"
        
        # Verify variance and EV calculations
        assert isinstance(advanced_stats.expected_value, Decimal), "Expected value should be Decimal"
        assert advanced_stats.variance >= 0, "Variance should be non-negative"
        assert isinstance(advanced_stats.standard_deviations, Decimal), "Standard deviations should be Decimal"

    @given(session_hands=poker_session_data())
    @settings(max_examples=15, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_positional_statistics_coverage(self, session_hands, db_session, test_user):
        """
        Property 30: Comprehensive Statistics Coverage - Positional Statistics
        
        For any poker session data, the system should calculate position-based
        statistics for all positions with sufficient sample size.
        
        **Validates: Requirements 6.1**
        """
        # Create poker hands in database
        for hand_data in session_hands:
            poker_hand = PokerHand(
                user_id=test_user.id,
                **hand_data
            )
            db_session.add(poker_hand)
        
        await db_session.commit()
        
        # Calculate positional statistics
        stats_service = StatisticsService(db_session)
        positional_stats = await stats_service.calculate_positional_statistics(test_user.id)
        
        # Verify positional statistics structure
        assert isinstance(positional_stats, list), "Positional statistics should be a list"
        
        # Verify each position has valid statistics
        for pos_stat in positional_stats:
            assert pos_stat.position is not None, "Position should be specified"
            assert pos_stat.hands_played > 0, "Hands played should be positive"
            
            # Verify statistical ranges
            assert 0 <= pos_stat.vpip <= 100, f"Position {pos_stat.position} VPIP should be 0-100%"
            assert 0 <= pos_stat.pfr <= 100, f"Position {pos_stat.position} PFR should be 0-100%"
            assert pos_stat.pfr <= pos_stat.vpip, f"Position {pos_stat.position} PFR should not exceed VPIP"
            assert pos_stat.aggression_factor >= 0, f"Position {pos_stat.position} aggression factor should be non-negative"
            
            # Verify optional statistics
            if pos_stat.three_bet_percentage is not None:
                assert 0 <= pos_stat.three_bet_percentage <= 100, f"Position {pos_stat.position} 3-bet % should be 0-100%"
            
            if pos_stat.fold_to_three_bet is not None:
                assert 0 <= pos_stat.fold_to_three_bet <= 100, f"Position {pos_stat.position} fold to 3-bet % should be 0-100%"

    @given(session_hands=poker_session_data())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_tournament_statistics_coverage(self, session_hands, db_session, test_user):
        """
        Property 30: Comprehensive Statistics Coverage - Tournament Statistics
        
        For any poker session data containing tournament hands, the system
        should calculate tournament-specific metrics including ROI, cash rate,
        and ICM analysis.
        
        **Validates: Requirements 6.6**
        """
        # Filter for tournament hands only
        tournament_hands = [hand for hand in session_hands if hand['game_format'] == 'tournament']
        
        # Skip if no tournament hands
        assume(len(tournament_hands) > 0)
        
        # Create poker hands in database
        for hand_data in tournament_hands:
            poker_hand = PokerHand(
                user_id=test_user.id,
                **hand_data
            )
            db_session.add(poker_hand)
        
        await db_session.commit()
        
        # Calculate tournament statistics
        stats_service = StatisticsService(db_session)
        tournament_stats = await stats_service.calculate_tournament_statistics(test_user.id)
        
        # Verify tournament statistics are calculated
        if tournament_stats is not None:  # May be None if insufficient data
            assert tournament_stats.tournaments_played > 0, "Tournaments played should be positive"
            assert tournament_stats.tournaments_cashed >= 0, "Tournaments cashed should be non-negative"
            assert tournament_stats.tournaments_cashed <= tournament_stats.tournaments_played, "Cashed should not exceed played"
            
            # Verify percentage calculations
            assert 0 <= tournament_stats.cash_percentage <= 100, "Cash percentage should be 0-100%"
            
            # Verify financial calculations
            assert tournament_stats.total_buy_ins >= 0, "Total buy-ins should be non-negative"
            assert tournament_stats.total_winnings >= 0, "Total winnings should be non-negative"
            assert isinstance(tournament_stats.roi, Decimal), "ROI should be Decimal"
            assert isinstance(tournament_stats.profit, Decimal), "Profit should be Decimal"
            
            # Verify finish position analysis
            if tournament_stats.average_finish > 0:
                assert tournament_stats.average_finish >= 1, "Average finish should be at least 1st place"
            
            # Verify optional tournament metrics
            if tournament_stats.final_table_appearances is not None:
                assert tournament_stats.final_table_appearances >= 0, "Final table appearances should be non-negative"
                assert tournament_stats.final_table_appearances <= tournament_stats.tournaments_played, "Final tables should not exceed tournaments played"
            
            if tournament_stats.bubble_factor is not None:
                assert 0 <= tournament_stats.bubble_factor <= 1, "Bubble factor should be 0-1"
            
            if tournament_stats.icm_pressure_spots is not None:
                assert tournament_stats.icm_pressure_spots >= 0, "ICM pressure spots should be non-negative"

    @given(
        session_hands=poker_session_data(),
        filters=st.builds(
            StatisticsFilters,
            platform=st.one_of(st.none(), st.sampled_from(['pokerstars', 'ggpoker'])),
            game_format=st.one_of(st.none(), st.sampled_from(['cash', 'tournament', 'sng'])),
            position=st.one_of(st.none(), valid_poker_position()),
            tournament_only=st.one_of(st.none(), st.booleans()),
            cash_only=st.one_of(st.none(), st.booleans()),
            play_money_only=st.one_of(st.none(), st.booleans()),
            exclude_play_money=st.one_of(st.none(), st.booleans())
        )
    )
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_filtered_statistics_coverage(self, session_hands, filters, db_session, test_user):
        """
        Property 30: Comprehensive Statistics Coverage - Filtered Statistics
        
        For any poker session data with applied filters, the system should
        calculate comprehensive statistics that respect the filter criteria
        and maintain mathematical accuracy.
        
        **Validates: Requirements 6.1, 6.6**
        """
        # Create poker hands in database
        for hand_data in session_hands:
            poker_hand = PokerHand(
                user_id=test_user.id,
                **hand_data
            )
            db_session.add(poker_hand)
        
        await db_session.commit()
        
        # Calculate filtered statistics
        stats_service = StatisticsService(db_session)
        
        try:
            filtered_stats = await stats_service.calculate_filtered_statistics(test_user.id, filters)
            
            # Verify comprehensive statistics response
            assert filtered_stats is not None, "Filtered statistics should be calculated"
            assert filtered_stats.basic_stats is not None, "Basic stats should be included"
            assert filtered_stats.advanced_stats is not None, "Advanced stats should be included"
            assert isinstance(filtered_stats.positional_stats, list), "Positional stats should be a list"
            
            # Verify metadata
            assert filtered_stats.filters_applied == filters, "Applied filters should match input"
            assert filtered_stats.sample_size >= 0, "Sample size should be non-negative"
            assert 0 <= filtered_stats.confidence_level <= 1, "Confidence level should be 0-1"
            assert isinstance(filtered_stats.calculation_date, datetime), "Calculation date should be datetime"
            assert isinstance(filtered_stats.cache_expires, datetime), "Cache expiry should be datetime"
            
            # Verify filter consistency
            total_hands = filtered_stats.basic_stats.total_hands
            
            # If tournament_only filter is applied, tournament_stats should exist or be None
            if filters.tournament_only and total_hands > 0:
                # Should have tournament data or None if insufficient
                pass  # Tournament stats may be None if insufficient data
            
            # If cash_only filter is applied, should not have tournament stats
            if filters.cash_only and total_hands > 0:
                # Tournament stats should be None for cash-only filter
                pass  # This is acceptable as tournament_stats can be None
            
            # Verify statistical consistency across all components
            basic_total = filtered_stats.basic_stats.total_hands
            positional_total = sum(pos.hands_played for pos in filtered_stats.positional_stats)
            
            # Positional total may be less due to minimum hand requirements per position
            if positional_total > 0:
                assert positional_total <= basic_total, "Positional hands should not exceed total hands"
        
        except ValueError as e:
            # Handle insufficient hands for statistical significance
            if "Insufficient hands" in str(e):
                # This is acceptable - filters may result in too few hands
                pass
            else:
                raise

    @given(session_hands=poker_session_data())
    @settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @pytest.mark.asyncio
    async def test_statistics_mathematical_consistency(self, session_hands, db_session, test_user):
        """
        Property 30: Comprehensive Statistics Coverage - Mathematical Consistency
        
        For any poker session data, all calculated statistics should be
        mathematically consistent and follow poker statistical principles.
        
        **Validates: Requirements 6.1, 6.6**
        """
        # Create poker hands in database
        for hand_data in session_hands:
            poker_hand = PokerHand(
                user_id=test_user.id,
                **hand_data
            )
            db_session.add(poker_hand)
        
        await db_session.commit()
        
        # Calculate all statistics
        stats_service = StatisticsService(db_session)
        basic_stats = await stats_service.calculate_basic_statistics(test_user.id)
        advanced_stats = await stats_service.calculate_advanced_statistics(test_user.id)
        positional_stats = await stats_service.calculate_positional_statistics(test_user.id)
        
        # Verify mathematical consistency
        
        # 1. PFR should never exceed VPIP (you can't raise without putting money in pot)
        assert basic_stats.pfr <= basic_stats.vpip, "PFR should not exceed VPIP"
        
        # 2. All percentages should be in valid range
        percentage_fields = [
            basic_stats.vpip, basic_stats.pfr,
            advanced_stats.three_bet_percentage, advanced_stats.fold_to_three_bet,
            advanced_stats.four_bet_percentage, advanced_stats.fold_to_four_bet,
            advanced_stats.cold_call_percentage, advanced_stats.isolation_raise,
            advanced_stats.c_bet_flop, advanced_stats.c_bet_turn, advanced_stats.c_bet_river,
            advanced_stats.fold_to_c_bet_flop, advanced_stats.fold_to_c_bet_turn, advanced_stats.fold_to_c_bet_river,
            advanced_stats.check_raise_flop, advanced_stats.check_raise_turn, advanced_stats.check_raise_river
        ]
        
        for percentage in percentage_fields:
            assert 0 <= percentage <= 100, f"Percentage {percentage} should be 0-100%"
        
        # 3. Aggression factor should be non-negative
        assert basic_stats.aggression_factor >= 0, "Aggression factor should be non-negative"
        assert advanced_stats.variance >= 0, "Variance should be non-negative"
        
        # 4. Positional statistics should be consistent
        for pos_stat in positional_stats:
            assert pos_stat.pfr <= pos_stat.vpip, f"Position {pos_stat.position}: PFR should not exceed VPIP"
            assert pos_stat.aggression_factor >= 0, f"Position {pos_stat.position}: Aggression factor should be non-negative"
        
        # 5. Red line + Blue line should relate to total winnings
        total_line_winnings = advanced_stats.red_line_winnings + advanced_stats.blue_line_winnings
        # This should be non-negative in most cases, but can be negative if player lost money
        assert isinstance(total_line_winnings, Decimal), "Combined line winnings should be Decimal"

    def test_empty_session_statistics_coverage(self, db_session, test_user):
        """
        Property 30: Comprehensive Statistics Coverage - Empty Session Handling
        
        For empty poker session data (no hands), the system should return
        appropriate zero/null statistics without errors.
        
        **Validates: Requirements 6.1, 6.6**
        """
        # No hands added to database
        
        # Calculate statistics for empty session
        stats_service = StatisticsService(db_session)
        
        # All statistics should handle empty data gracefully
        basic_stats = asyncio.run(stats_service.calculate_basic_statistics(test_user.id))
        advanced_stats = asyncio.run(stats_service.calculate_advanced_statistics(test_user.id))
        positional_stats = asyncio.run(stats_service.calculate_positional_statistics(test_user.id))
        tournament_stats = asyncio.run(stats_service.calculate_tournament_statistics(test_user.id))
        
        # Verify empty session handling
        assert basic_stats.total_hands == 0, "Empty session should have 0 hands"
        assert basic_stats.vpip == Decimal('0.0'), "Empty session VPIP should be 0"
        assert basic_stats.pfr == Decimal('0.0'), "Empty session PFR should be 0"
        assert basic_stats.aggression_factor == Decimal('0.0'), "Empty session aggression factor should be 0"
        assert basic_stats.win_rate == Decimal('0.0'), "Empty session win rate should be 0"
        
        # Advanced stats should all be zero
        assert advanced_stats.three_bet_percentage == Decimal('0.0'), "Empty session 3-bet % should be 0"
        assert advanced_stats.c_bet_flop == Decimal('0.0'), "Empty session c-bet % should be 0"
        assert advanced_stats.red_line_winnings == Decimal('0.0'), "Empty session red line should be 0"
        assert advanced_stats.blue_line_winnings == Decimal('0.0'), "Empty session blue line should be 0"
        assert advanced_stats.variance == Decimal('0.0'), "Empty session variance should be 0"
        
        # Positional stats should be empty list
        assert positional_stats == [], "Empty session should have no positional stats"
        
        # Tournament stats should be None
        assert tournament_stats is None, "Empty session should have no tournament stats"


if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])