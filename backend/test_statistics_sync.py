"""
Synchronous tests for statistics service (alternative approach).
"""
import pytest
from decimal import Decimal
from datetime import datetime, timezone
from unittest.mock import Mock, AsyncMock

from app.services.statistics_service import StatisticsService
from app.schemas.statistics import StatisticsFilters, BasicStatistics


def test_percentage_calculation():
    """Test the percentage calculation helper method."""
    # Create a mock database session
    mock_db = Mock()
    stats_service = StatisticsService(mock_db)
    
    # Test percentage calculation
    result = stats_service._calculate_percentage(25, 100)
    assert result == Decimal('25.0')
    
    result = stats_service._calculate_percentage(0, 100)
    assert result == Decimal('0.0')
    
    result = stats_service._calculate_percentage(10, 0)
    assert result == Decimal('0.0')


def test_vpip_detection():
    """Test VPIP detection logic."""
    mock_db = Mock()
    stats_service = StatisticsService(mock_db)
    
    # Test VPIP hand (voluntary call)
    actions = {"preflop": [{"action": "call", "amount": 1.0}]}
    assert stats_service._is_vpip_hand(actions, "BTN") == True
    
    # Test non-VPIP hand (fold)
    actions = {"preflop": [{"action": "fold"}]}
    assert stats_service._is_vpip_hand(actions, "BTN") == False
    
    # Test BB check (not VPIP)
    actions = {"preflop": [{"action": "check"}]}
    assert stats_service._is_vpip_hand(actions, "BB") == False


def test_pfr_detection():
    """Test PFR detection logic."""
    mock_db = Mock()
    stats_service = StatisticsService(mock_db)
    
    # Test PFR hand
    actions = {"preflop": [{"action": "raise", "amount": 3.0}]}
    assert stats_service._is_pfr_hand(actions) == True
    
    # Test non-PFR hand
    actions = {"preflop": [{"action": "call", "amount": 1.0}]}
    assert stats_service._is_pfr_hand(actions) == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])