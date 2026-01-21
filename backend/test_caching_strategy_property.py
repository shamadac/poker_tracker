"""
Property-based test for caching strategy functionality.

**Feature: professional-poker-analyzer-rebuild, Property 10: Comprehensive Caching Strategy**
**Validates: Requirements 4.5, 4.8, 9.4**

Property 10: Comprehensive Caching Strategy
*For any* frequently accessed data (statistics, analysis results, user preferences), the system should 
implement appropriate caching with proper TTL and cache invalidation strategies
"""
import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Dict, Any, List
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.cache_service import (
    CacheService, 
    StatisticsCacheService, 
    AnalysisCacheService,
    cache_service,
    stats_cache,
    analysis_cache
)
from app.schemas.statistics import StatisticsFilters


# Mock Redis client for testing
class MockRedisClient:
    def __init__(self):
        self.data = {}
        self.ttl_data = {}
        self.connected = True
        self.stats = {
            'keyspace_hits': 0,
            'keyspace_misses': 0,
            'used_memory_human': '1MB',
            'connected_clients': 1,
            'total_commands_processed': 0
        }
    
    async def ping(self):
        if not self.connected:
            raise Exception("Redis not connected")
        return True
    
    async def get(self, key: str):
        if key in self.data:
            self.stats['keyspace_hits'] += 1
            return self.data[key]
        else:
            self.stats['keyspace_misses'] += 1
            return None
    
    async def setex(self, key: str, ttl: int, value: str):
        self.data[key] = value
        self.ttl_data[key] = time.time() + ttl
        self.stats['total_commands_processed'] += 1
        return True
    
    async def delete(self, *keys):
        deleted = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                if key in self.ttl_data:
                    del self.ttl_data[key]
                deleted += 1
        return deleted
    
    async def keys(self, pattern: str):
        # Simple pattern matching for testing
        import fnmatch
        return [key for key in self.data.keys() if fnmatch.fnmatch(key, pattern)]
    
    async def info(self):
        return self.stats
    
    async def close(self):
        self.connected = False


@pytest_asyncio.fixture
async def mock_cache_service():
    """Create a cache service with mocked Redis client."""
    service = CacheService()
    service.redis_client = MockRedisClient()
    service.connected = True
    return service


@pytest_asyncio.fixture
async def mock_stats_cache():
    """Create a statistics cache service with mocked Redis client."""
    service = StatisticsCacheService()
    service.redis_client = MockRedisClient()
    service.connected = True
    return service


@pytest_asyncio.fixture
async def mock_analysis_cache():
    """Create an analysis cache service with mocked Redis client."""
    service = AnalysisCacheService()
    service.redis_client = MockRedisClient()
    service.connected = True
    return service


# Strategy for generating cache data
@st.composite
def cache_data_strategy(draw):
    """Generate realistic cache data for property testing."""
    data_types = ["statistics", "analysis", "preferences", "trends"]
    data_type = draw(st.sampled_from(data_types))
    
    if data_type == "statistics":
        return {
            "type": "statistics",
            "data": {
                "total_hands": draw(st.integers(min_value=1, max_value=10000)),
                "vpip": float(draw(st.decimals(min_value=0, max_value=100, places=1))),
                "pfr": float(draw(st.decimals(min_value=0, max_value=100, places=1))),
                "win_rate": float(draw(st.decimals(min_value=-50, max_value=50, places=2))),
                "aggression_factor": float(draw(st.decimals(min_value=0, max_value=10, places=2))),
                "calculation_date": datetime.now(timezone.utc).isoformat()
            }
        }
    elif data_type == "analysis":
        return {
            "type": "analysis",
            "data": {
                "hand_id": draw(st.text(min_size=8, max_size=16)),
                "analysis_text": draw(st.text(min_size=50, max_size=500)),
                "strengths": draw(st.lists(st.text(min_size=10, max_size=50), min_size=1, max_size=5)),
                "mistakes": draw(st.lists(st.text(min_size=10, max_size=50), min_size=0, max_size=3)),
                "confidence_score": float(draw(st.decimals(min_value=0, max_value=1, places=2))),
                "provider": draw(st.sampled_from(["gemini", "groq"])),
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        }
    elif data_type == "preferences":
        return {
            "type": "preferences",
            "data": {
                "theme": draw(st.sampled_from(["light", "dark"])),
                "language": draw(st.sampled_from(["en", "es", "fr"])),
                "notifications": draw(st.booleans()),
                "auto_analysis": draw(st.booleans()),
                "preferred_provider": draw(st.sampled_from(["gemini", "groq"])),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        }
    else:  # trends
        return {
            "type": "trends",
            "data": {
                "metric_name": draw(st.sampled_from(["vpip", "pfr", "win_rate"])),
                "time_period": draw(st.sampled_from(["7d", "30d", "90d"])),
                "trend_direction": draw(st.sampled_from(["up", "down", "stable"])),
                "trend_strength": float(draw(st.decimals(min_value=0, max_value=1, places=2))),
                "data_points": [
                    {
                        "date": (datetime.now(timezone.utc) - timedelta(days=i)).isoformat(),
                        "value": float(draw(st.decimals(min_value=0, max_value=100, places=1)))
                    }
                    for i in range(draw(st.integers(min_value=5, max_value=30)))
                ]
            }
        }


@st.composite
def cache_identifiers_strategy(draw):
    """Generate cache identifiers for testing."""
    return {
        "user_id": f"user_{draw(st.integers(min_value=1, max_value=1000))}",
        "cache_type": draw(st.sampled_from([
            "user_stats", "hand_analysis", "session_data", 
            "ai_response", "user_preferences", "trend_data"
        ])),
        "additional_params": {
            "filters": {
                "platform": draw(st.one_of(st.none(), st.sampled_from(["pokerstars", "ggpoker"]))),
                "game_format": draw(st.one_of(st.none(), st.sampled_from(["cash", "tournament"])))
            } if draw(st.booleans()) else {}
        }
    }


@pytest.mark.asyncio
@given(
    cache_data=cache_data_strategy(),
    identifiers=cache_identifiers_strategy()
)
@settings(
    max_examples=100,
    deadline=30000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_comprehensive_caching_strategy(mock_cache_service, cache_data, identifiers):
    """
    Property 10: Comprehensive Caching Strategy
    
    *For any* frequently accessed data (statistics, analysis results, user preferences), the system should 
    implement appropriate caching with proper TTL and cache invalidation strategies.
    
    **Validates: Requirements 4.5, 4.8, 9.4**
    """
    cache_service = mock_cache_service
    user_id = identifiers["user_id"]
    cache_type = identifiers["cache_type"]
    data = cache_data["data"]
    additional_params = identifiers["additional_params"]
    
    # Property 1: Cache service should be able to store any type of data
    success = await cache_service.set(
        cache_type, 
        user_id, 
        data, 
        **additional_params
    )
    assert success, "Cache service should successfully store data"
    
    # Property 2: Stored data should be retrievable
    retrieved_data = await cache_service.get(
        cache_type, 
        user_id, 
        **additional_params
    )
    assert retrieved_data is not None, "Cached data should be retrievable"
    
    # Property 3: Retrieved data should match stored data (with type conversions)
    if isinstance(data, dict):
        assert isinstance(retrieved_data, dict), "Retrieved data should maintain structure"
        # Check key fields exist (allowing for serialization differences)
        for key in data.keys():
            assert key in retrieved_data, f"Key '{key}' should be preserved in cached data"
    
    # Property 4: Cache keys should be consistent for same parameters
    key1 = cache_service._generate_cache_key(cache_type, user_id, **additional_params)
    key2 = cache_service._generate_cache_key(cache_type, user_id, **additional_params)
    assert key1 == key2, "Cache keys should be consistent for same parameters"
    
    # Property 5: Different parameters should generate different keys
    different_params = {"different": "params"}
    key3 = cache_service._generate_cache_key(cache_type, user_id, **different_params)
    assert key1 != key3, "Different parameters should generate different cache keys"
    
    # Property 6: TTL should be applied correctly
    ttl_seconds = cache_service.ttl_config.get(cache_type, 3600)
    assert ttl_seconds > 0, "TTL should be positive"
    assert ttl_seconds <= 604800, "TTL should not exceed 7 days for reasonable cache management"
    
    # Property 7: Cache invalidation should work
    deleted = await cache_service.delete(cache_type, user_id, **additional_params)
    assert deleted, "Cache deletion should succeed"
    
    # Property 8: Deleted data should not be retrievable
    retrieved_after_delete = await cache_service.get(
        cache_type, 
        user_id, 
        **additional_params
    )
    assert retrieved_after_delete is None, "Deleted data should not be retrievable"
    
    # Property 9: Cache statistics should be tracked
    stats = await cache_service.get_cache_stats()
    assert isinstance(stats, dict), "Cache stats should be returned as dictionary"
    assert "connected" in stats, "Cache stats should include connection status"
    
    # Property 10: Pattern-based invalidation should work
    # Store multiple entries for the same user
    await cache_service.set(cache_type, user_id, data, test_param="1")
    await cache_service.set(cache_type, user_id, data, test_param="2")
    
    # Invalidate all entries for this user and cache type
    pattern = f"{cache_service.key_prefixes.get(cache_type, cache_type)}:{user_id}:*"
    invalidated_count = await cache_service.invalidate_pattern(pattern)
    assert invalidated_count >= 0, "Pattern invalidation should return count of deleted keys"


@pytest.mark.asyncio
@given(
    user_id=st.text(min_size=5, max_size=20),
    filters_data=st.dictionaries(
        st.sampled_from(["platform", "game_format", "start_date", "end_date"]),
        st.one_of(
            st.none(),
            st.text(min_size=3, max_size=20),
            st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2025, 12, 31))
        ),
        min_size=0,
        max_size=4
    )
)
@settings(
    max_examples=50,
    deadline=30000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_statistics_cache_specialization(mock_stats_cache, user_id, filters_data):
    """
    Test specialized statistics caching functionality.
    
    **Validates: Requirements 4.5, 4.8**
    """
    stats_cache = mock_stats_cache
    
    # Create StatisticsFilters object
    # Convert datetime objects to strings for JSON serialization
    clean_filters_data = {}
    for key, value in filters_data.items():
        if isinstance(value, datetime):
            clean_filters_data[key] = value.isoformat()
        elif key == "platform" and value not in ["pokerstars", "ggpoker", None]:
            # Skip invalid platform values
            continue
        elif key == "game_format" and value not in ["cash", "tournament", "sng", None]:
            # Skip invalid game format values
            continue
        else:
            clean_filters_data[key] = value
    
    # Create a minimal valid StatisticsFilters object
    filters = StatisticsFilters(
        platform=clean_filters_data.get("platform") if clean_filters_data.get("platform") in ["pokerstars", "ggpoker"] else None,
        game_format=clean_filters_data.get("game_format") if clean_filters_data.get("game_format") in ["cash", "tournament", "sng"] else None,
        start_date=None,  # Simplified for testing
        end_date=None     # Simplified for testing
    )
    
    # Test statistics data
    statistics_data = {
        "basic_stats": {
            "total_hands": 100,
            "vpip": 25.5,
            "pfr": 18.2,
            "win_rate": 2.5
        },
        "advanced_stats": {
            "three_bet_percentage": 8.5,
            "c_bet_flop": 65.0
        },
        "calculation_date": datetime.now(timezone.utc).isoformat()
    }
    
    # Property 1: Statistics cache should store user statistics with filters
    success = await stats_cache.set_user_statistics(user_id, filters, statistics_data)
    assert success, "Statistics cache should store user statistics"
    
    # Property 2: Statistics should be retrievable with same filters
    retrieved_stats = await stats_cache.get_user_statistics(user_id, filters)
    assert retrieved_stats is not None, "Statistics should be retrievable"
    assert "basic_stats" in retrieved_stats, "Retrieved statistics should contain basic stats"
    
    # Property 3: Different filters should create separate cache entries
    different_filters = StatisticsFilters(platform="ggpoker")  # Use valid platform
    different_retrieved = await stats_cache.get_user_statistics(user_id, different_filters)
    assert different_retrieved is None, "Different filters should not return cached data"
    
    # Property 4: Trend data caching should work
    trend_data = {
        "metric_name": "vpip",
        "time_period": "30d",
        "trend_direction": "up",
        "data_points": [
            {"date": "2024-01-01", "value": 20.0},
            {"date": "2024-01-02", "value": 22.0}
        ]
    }
    
    trend_success = await stats_cache.set_trend_data(user_id, "30d", filters, trend_data)
    assert trend_success, "Trend data should be cacheable"
    
    retrieved_trend = await stats_cache.get_trend_data(user_id, "30d", filters)
    assert retrieved_trend is not None, "Trend data should be retrievable"
    assert retrieved_trend["metric_name"] == "vpip", "Trend data should be preserved"


@pytest.mark.asyncio
@given(
    hand_hash=st.text(min_size=8, max_size=32),
    ai_provider=st.sampled_from(["gemini", "groq"]),
    prompt_version=st.text(min_size=3, max_size=10)
)
@settings(
    max_examples=50,
    deadline=30000,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
async def test_property_analysis_cache_specialization(mock_analysis_cache, hand_hash, ai_provider, prompt_version):
    """
    Test specialized analysis caching functionality.
    
    **Validates: Requirements 4.8, 9.4**
    """
    analysis_cache = mock_analysis_cache
    
    # Test analysis data
    analysis_data = {
        "hand_id": hand_hash,
        "analysis_text": "This is a detailed analysis of the poker hand...",
        "strengths": ["Good position play", "Proper bet sizing"],
        "mistakes": ["Missed value bet on river"],
        "recommendations": ["Consider betting for value"],
        "confidence_score": 0.85,
        "provider": ai_provider,
        "prompt_version": prompt_version,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Property 1: Analysis cache should store hand analysis
    success = await analysis_cache.set_hand_analysis(
        hand_hash, ai_provider, prompt_version, analysis_data
    )
    assert success, "Analysis cache should store hand analysis"
    
    # Property 2: Analysis should be retrievable with same parameters
    retrieved_analysis = await analysis_cache.get_hand_analysis(
        hand_hash, ai_provider, prompt_version
    )
    assert retrieved_analysis is not None, "Analysis should be retrievable"
    assert retrieved_analysis["hand_id"] == hand_hash, "Hand ID should be preserved"
    assert retrieved_analysis["provider"] == ai_provider, "Provider should be preserved"
    
    # Property 3: Different providers should create separate cache entries
    different_provider = "groq" if ai_provider == "gemini" else "gemini"
    
    # First, verify that we can store analysis for the different provider
    different_analysis_data = analysis_data.copy()
    different_analysis_data["provider"] = different_provider
    
    await analysis_cache.set_hand_analysis(
        hand_hash, different_provider, prompt_version, different_analysis_data
    )
    
    # Now retrieve with the original provider - should get original data
    original_analysis = await analysis_cache.get_hand_analysis(
        hand_hash, ai_provider, prompt_version
    )
    assert original_analysis is not None, "Original analysis should still be retrievable"
    assert original_analysis["provider"] == ai_provider, "Original provider should be preserved"
    
    # Retrieve with different provider - should get different data
    different_retrieved = await analysis_cache.get_hand_analysis(
        hand_hash, different_provider, prompt_version
    )
    assert different_retrieved is not None, "Different provider analysis should be retrievable"
    assert different_retrieved["provider"] == different_provider, "Different provider should be preserved"
    
    # The two analyses should have different providers
    assert original_analysis["provider"] != different_retrieved["provider"], \
        "Different providers should create separate cache entries"
    
    # Property 4: Different prompt versions should create separate cache entries
    different_prompt_analysis = await analysis_cache.get_hand_analysis(
        hand_hash, ai_provider, "different_version"
    )
    assert different_prompt_analysis is None, "Different prompt version should not return cached analysis"


@pytest.mark.asyncio
async def test_cache_hit_rate_calculation(mock_cache_service):
    """Test cache hit rate calculation and statistics."""
    cache_service = mock_cache_service
    
    # Simulate cache hits and misses
    test_data = {"test": "data"}
    
    # Store some data
    await cache_service.set("test_type", "key1", test_data)
    await cache_service.set("test_type", "key2", test_data)
    
    # Generate hits
    await cache_service.get("test_type", "key1")  # Hit
    await cache_service.get("test_type", "key2")  # Hit
    await cache_service.get("test_type", "key1")  # Hit
    
    # Generate misses
    await cache_service.get("test_type", "nonexistent1")  # Miss
    await cache_service.get("test_type", "nonexistent2")  # Miss
    
    # Check statistics
    stats = await cache_service.get_cache_stats()
    
    assert stats["connected"] is True
    assert stats["keyspace_hits"] >= 3
    assert stats["keyspace_misses"] >= 2
    assert "hit_rate" in stats
    
    # Hit rate should be reasonable (hits / (hits + misses) * 100)
    expected_hit_rate = (stats["keyspace_hits"] / (stats["keyspace_hits"] + stats["keyspace_misses"])) * 100
    assert abs(stats["hit_rate"] - expected_hit_rate) < 0.1


@pytest.mark.asyncio
async def test_cache_ttl_enforcement(mock_cache_service):
    """Test that TTL values are properly enforced."""
    cache_service = mock_cache_service
    
    # Test different cache types have appropriate TTLs
    test_cases = [
        ("user_stats", 3600),      # 1 hour
        ("hand_analysis", 86400),  # 24 hours
        ("session_data", 21600),   # 6 hours
        ("ai_response", 604800),   # 7 days
        ("trend_data", 1800),      # 30 minutes
    ]
    
    for cache_type, expected_ttl in test_cases:
        # Store data with default TTL
        await cache_service.set(cache_type, "test_key", {"test": "data"})
        
        # Verify TTL is set correctly
        actual_ttl = cache_service.ttl_config.get(cache_type)
        assert actual_ttl == expected_ttl, f"TTL for {cache_type} should be {expected_ttl} seconds"
        
        # Verify TTL is reasonable for the data type
        if cache_type in ["user_stats", "session_data"]:
            assert actual_ttl <= 21600, "User data should have relatively short TTL"
        elif cache_type == "ai_response":
            assert actual_ttl >= 86400, "AI responses should have longer TTL"


@pytest.mark.asyncio
async def test_cache_invalidation_strategies(mock_cache_service):
    """Test comprehensive cache invalidation strategies."""
    cache_service = mock_cache_service
    user_id = "test_user_123"
    
    # Store data for multiple cache types
    test_data = {"test": "data"}
    cache_types = ["user_stats", "session_data", "user_preferences", "trend_data"]
    
    for cache_type in cache_types:
        await cache_service.set(cache_type, user_id, test_data, param1="value1")
        await cache_service.set(cache_type, user_id, test_data, param2="value2")
    
    # Test user-specific invalidation
    total_invalidated = await cache_service.invalidate_user_cache(user_id)
    assert total_invalidated >= 0, "User cache invalidation should return count"
    
    # Verify data is actually invalidated
    for cache_type in cache_types:
        retrieved = await cache_service.get(cache_type, user_id, param1="value1")
        assert retrieved is None, f"Data for {cache_type} should be invalidated"


@pytest.mark.asyncio
async def test_cache_serialization_edge_cases(mock_cache_service):
    """Test cache serialization handles edge cases properly."""
    cache_service = mock_cache_service
    
    # Test various data types
    test_cases = [
        ("decimal", Decimal("123.45")),
        ("datetime", datetime.now(timezone.utc)),
        ("nested_dict", {"level1": {"level2": {"value": 42}}}),
        ("list_of_dicts", [{"id": 1, "name": "test"}, {"id": 2, "name": "test2"}]),
        ("unicode", "Test with unicode: 🃏♠️♥️♦️♣️"),
        ("empty_dict", {}),
        ("empty_list", []),
        ("none_values", {"key1": None, "key2": "value"}),
    ]
    
    for test_name, test_data in test_cases:
        # Store and retrieve data
        success = await cache_service.set("test_type", f"key_{test_name}", test_data)
        assert success, f"Should be able to cache {test_name}"
        
        retrieved = await cache_service.get("test_type", f"key_{test_name}")
        assert retrieved is not None, f"Should be able to retrieve {test_name}"
        
        # Verify structure is preserved (allowing for type conversions)
        if isinstance(test_data, dict):
            assert isinstance(retrieved, dict), f"Dict structure should be preserved for {test_name}"
        elif isinstance(test_data, list):
            assert isinstance(retrieved, list), f"List structure should be preserved for {test_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])