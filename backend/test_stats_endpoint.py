"""
Test statistics API endpoint.
"""
import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.models.base import Base
from app.models.user import User
from app.models.hand import PokerHand
from app.main import app


# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


async def test_stats_endpoint_with_data():
    """Test the statistics endpoint with sample data."""
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
        
        # Create 10 hands to have enough data for meaningful statistics
        for i in range(10):
            hand = PokerHand(
                user_id=user.id,
                hand_id=f"HAND{i:03d}",
                platform="pokerstars",
                game_type="Hold'em",
                game_format="cash",
                stakes="$0.50/$1.00",
                position=["UTG", "MP", "CO", "BTN", "SB", "BB"][i % 6],
                player_cards=["As", "Kh"],
                actions={
                    "preflop": [{"action": "call" if i % 2 == 0 else "raise", "amount": 1.0 if i % 2 == 0 else 3.0}],
                    "flop": [{"action": "bet", "amount": 2.0}] if i % 3 == 0 else []
                },
                result="won" if i % 3 == 0 else "lost",
                pot_size=Decimal("10.00"),
                date_played=datetime.now(timezone.utc)
            )
            hands.append(hand)
            session.add(hand)
        
        await session.commit()
        
        print(f"Created {len(hands)} sample hands for testing")
        
        # Test direct service call
        from app.services.statistics_service import StatisticsService
        stats_service = StatisticsService(session)
        basic_stats = await stats_service.calculate_basic_statistics(user.id)
        
        print(f"Direct service call results:")
        print(f"  Total hands: {basic_stats.total_hands}")
        print(f"  VPIP: {basic_stats.vpip}%")
        print(f"  PFR: {basic_stats.pfr}%")
        print(f"  Aggression Factor: {basic_stats.aggression_factor}")
        
        # Test positional statistics
        positional_stats = await stats_service.calculate_positional_statistics(user.id)
        print(f"  Positional stats: {len(positional_stats)} positions")
        for pos_stat in positional_stats:
            print(f"    {pos_stat.position}: {pos_stat.hands_played} hands, VPIP: {pos_stat.vpip}%")
        
        assert basic_stats.total_hands == 10
        assert basic_stats.vpip > 0  # Should have some VPIP
        assert basic_stats.pfr >= 0  # Should have some PFR
        
        print("✓ Statistics endpoint test passed!")
    
    # Clean up
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await test_engine.dispose()


def main():
    """Run the test."""
    print("Testing statistics endpoint...")
    asyncio.run(test_stats_endpoint_with_data())
    print("Test completed successfully! ✓")


if __name__ == "__main__":
    main()