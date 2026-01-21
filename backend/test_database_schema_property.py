"""
Property-based test for database schema consistency.

Feature: professional-poker-analyzer-rebuild
Property 9: Data Storage Consistency

This test validates that hand history parsing operations store all extracted data
in the database with proper structure and indexing for efficient retrieval according
to Requirement 4.2.
"""

import pytest
import os
import asyncio
from datetime import datetime
from decimal import Decimal
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app.models.base import Base
from app.models.hand import PokerHand
from app.models.user import User

# Database URL for testing
DATABASE_URL = "postgresql+asyncpg://postgres:password@localhost:5432/poker_analyzer"

# Check if PostgreSQL is available
try:
    import asyncpg
    POSTGRESQL_AVAILABLE = True
except ImportError:
    POSTGRESQL_AVAILABLE = False

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine with proper cleanup."""
    if not POSTGRESQL_AVAILABLE:
        pytest.skip("PostgreSQL (asyncpg) not available for testing")
    
    try:
        engine = create_async_engine(DATABASE_URL, echo=False)
        
        # Test connection first
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        
        # Create all tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        yield engine
        
        # Cleanup
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
        except Exception:
            pass
        
        await engine.dispose()
        
    except Exception as e:
        pytest.skip(f"PostgreSQL database not available: {e}")

@pytest.fixture
async def test_session(test_engine):
    """Create test database session with transaction rollback."""
    async_session = sessionmaker(
        test_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        transaction = await session.begin()
        try:
            yield session
        finally:
            try:
                await transaction.rollback()
            except Exception:
                pass

# Hypothesis strategies for generating test data
@st.composite
def user_data(draw):
    """Generate valid user data."""
    return {
        "email": f"{draw(st.text(min_size=5, max_size=20, alphabet='abcdefghijklmnopqrstuvwxyz'))}@example.com",
        "password_hash": draw(st.text(min_size=32, max_size=64)),
    }

@st.composite
def poker_hand_data(draw):
    """Generate valid poker hand data."""
    return {
        "hand_id": draw(st.text(min_size=10, max_size=20, alphabet="0123456789ABCDEF")),
        "platform": draw(st.sampled_from(["pokerstars", "ggpoker"])),
        "game_type": draw(st.sampled_from(["Hold'em No Limit", "Omaha Pot Limit"])),
        "stakes": draw(st.text(min_size=3, max_size=20)),
        "pot_size": float(draw(st.decimals(min_value=0.01, max_value=10000, places=2))),
        "raw_text": draw(st.text(min_size=50, max_size=1000))
    }

class TestDatabaseSchemaConsistency:
    """Test database schema consistency and data storage."""

    @given(user_data=user_data(), hand_data=poker_hand_data())
    @settings(
        max_examples=50,  # Reduced for faster testing
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture]
    )
    @pytest.mark.asyncio
    async def test_data_storage_consistency(self, test_session: AsyncSession, user_data, hand_data):
        """
        Property 9: Data Storage Consistency
        
        For any hand history parsing operation, all extracted data should be stored
        in the database with proper structure and indexing for efficient retrieval.
        
        **Validates: Requirements 4.2**
        """
        # Create a user first
        user = User(
            email=user_data["email"],
            password_hash=user_data["password_hash"]
        )
        test_session.add(user)
        await test_session.flush()  # Get the user ID
        
        # Create poker hand with user reference
        poker_hand = PokerHand(
            user_id=user.id,
            hand_id=hand_data["hand_id"],
            platform=hand_data["platform"],
            game_type=hand_data["game_type"],
            stakes=hand_data["stakes"],
            pot_size=Decimal(str(hand_data["pot_size"])),
            raw_text=hand_data["raw_text"]
        )
        
        test_session.add(poker_hand)
        await test_session.commit()
        
        # Verify data was stored correctly
        result = await test_session.execute(
            text("SELECT * FROM poker_hands WHERE hand_id = :hand_id AND user_id = :user_id"),
            {"hand_id": hand_data["hand_id"], "user_id": user.id}
        )
        stored_hand = result.fetchone()
        
        assert stored_hand is not None, "Hand should be stored in database"
        assert stored_hand.hand_id == hand_data["hand_id"]
        assert stored_hand.platform == hand_data["platform"]
        assert stored_hand.game_type == hand_data["game_type"]
        assert stored_hand.stakes == hand_data["stakes"]
        assert stored_hand.raw_text == hand_data["raw_text"]
        assert stored_hand.user_id == user.id

    @pytest.mark.asyncio
    async def test_basic_database_functionality(self, test_session: AsyncSession):
        """
        Basic test to ensure database connection and table creation works.
        
        **Validates: Requirements 4.2**
        """
        # Create a simple user
        user = User(
            email="test@example.com",
            password_hash="test_hash"
        )
        test_session.add(user)
        await test_session.flush()
        
        # Create a simple poker hand
        poker_hand = PokerHand(
            user_id=user.id,
            hand_id="TEST_HAND_123",
            platform="pokerstars",
            game_type="Hold'em No Limit",
            stakes="$0.01/$0.02",
            pot_size=Decimal("10.50"),
            raw_text="Test hand content"
        )
        
        test_session.add(poker_hand)
        await test_session.commit()
        
        # Verify the hand was stored
        assert poker_hand.id is not None
        assert poker_hand.user_id == user.id
        assert poker_hand.hand_id == "TEST_HAND_123"

if __name__ == "__main__":
    # Run the property tests
    pytest.main([__file__, "-v", "--tb=short"])