"""
Simple test for statistics service functionality.
"""
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.user import User
from app.models.hand import PokerHand
from app.services.statistics_service import StatisticsService


# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


async def test_basic_statistics():
    """Test basic statistics calculation."""
    # Create test engine and session
    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    TestSessionLocal = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create database tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        # Create test user
        user = User(
            id="test-user-id",
            email="test@example.com",
            password_hash="hashed_password"
        )
        session.add(user)
        await session.commit()
        
        # Create sample hands
        hands = []
        
        # Hand 1: VPIP hand (called preflop), won
        hand1 = PokerHand(
            user_id=user.id,
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
            user_id=user.id,
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
            user_id=user.id,
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
        
        # Add hands to database
        for hand in hands:
            session.add(hand)
        await session.commit()
        
        # Test statistics calculation
        stats_service = StatisticsService(session)
        basic_stats = await stats_service.calculate_basic_statistics(user.id)
        
        # Verify results
        print(f"Total hands: {basic_stats.total_hands}")
        print(f"VPIP: {basic_stats.vpip}%")
        print(f"PFR: {basic_stats.pfr}%")
        print(f"Aggression Factor: {basic_stats.aggression_factor}")
        print(f"Win Rate: {basic_stats.win_rate}")
        
        # Assertions
        assert basic_stats.total_hands == 3
        # VPIP: Hands 1 and 2 are VPIP (2 out of 3 = 66.7%)
        assert basic_stats.vpip == Decimal('66.7')
        # PFR: Hand 2 is PFR (1 out of 3 = 33.3%)
        assert basic_stats.pfr == Decimal('33.3')
        # Aggression factor should be calculated
        assert basic_stats.aggression_factor >= Decimal('0.0')
        
        print("✓ Basic statistics test passed!")
        
        # Test positional statistics
        positional_stats = await stats_service.calculate_positional_statistics(user.id)
        print(f"Positional stats count: {len(positional_stats)}")
        
        # Should have no positional stats since we need at least 5 hands per position
        assert len(positional_stats) == 0
        
        print("✓ Positional statistics test passed!")
    
    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()


async def test_empty_database():
    """Test statistics calculation with no hands."""
    # Create test engine and session
    test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    TestSessionLocal = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Create database tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with TestSessionLocal() as session:
        # Create test user
        user = User(
            id="test-user-id-2",
            email="test2@example.com",
            password_hash="hashed_password"
        )
        session.add(user)
        await session.commit()
        
        # Test statistics calculation with no hands
        stats_service = StatisticsService(session)
        basic_stats = await stats_service.calculate_basic_statistics(user.id)
        
        # Verify results
        assert basic_stats.total_hands == 0
        assert basic_stats.vpip == Decimal('0.0')
        assert basic_stats.pfr == Decimal('0.0')
        assert basic_stats.aggression_factor == Decimal('0.0')
        assert basic_stats.win_rate == Decimal('0.0')
        
        print("✓ Empty database test passed!")
    
    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()


def main():
    """Run all tests."""
    print("Running statistics service tests...")
    
    # Run tests
    asyncio.run(test_basic_statistics())
    asyncio.run(test_empty_database())
    
    print("All tests passed! ✓")


if __name__ == "__main__":
    main()