#!/usr/bin/env python3
"""
Redis caching service for poker analyzer.

This service implements comprehensive caching strategy for:
- Statistics calculations
- Analysis results  
- User preferences
- Hand parsing results
"""
import json
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.schemas.statistics import StatisticsFilters
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Comprehensive Redis caching service."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.connected = False
        
        # Cache TTL configurations (in seconds)
        self.ttl_config = {
            'user_stats': 3600,        # 1 hour
            'hand_analysis': 86400,    # 24 hours  
            'session_data': 21600,     # 6 hours
            'ai_response': 604800,     # 7 days
            'user_preferences': 3600,  # 1 hour
            'parsing_results': 43200,  # 12 hours
            'trend_data': 1800,        # 30 minutes
            'leaderboard': 900,        # 15 minutes
        }
        
        # Cache key prefixes
        self.key_prefixes = {
            'user_stats': 'stats:user',
            'hand_analysis': 'analysis:hand',
            'session_data': 'session:user',
            'ai_response': 'ai:response',
            'user_preferences': 'prefs:user',
            'parsing_results': 'parse:file',
            'trend_data': 'trends:user',
            'leaderboard': 'leaderboard:global',
        }
    
    async def connect(self) -> bool:
        """Initialize Redis connection."""
        try:
            if not self.redis_client:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                    retry_on_timeout=True,
                    health_check_interval=30
                )
                
            # Test connection
            await self.redis_client.ping()
            self.connected = True
            logger.info("Redis cache service connected successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.connected = False
            logger.info("Redis cache service disconnected")
    
    def _generate_cache_key(self, cache_type: str, identifier: str, **kwargs) -> str:
        """Generate standardized cache key."""
        prefix = self.key_prefixes.get(cache_type, cache_type)
        
        # Create hash of additional parameters for consistent keys
        if kwargs:
            params_str = json.dumps(kwargs, sort_keys=True, default=str)
            params_hash = hashlib.md5(params_str.encode()).hexdigest()[:8]
            return f"{prefix}:{identifier}:{params_hash}"
        
        return f"{prefix}:{identifier}"
    
    def _serialize_data(self, data: Any) -> str:
        """Serialize data for Redis storage."""
        def json_serializer(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            elif isinstance(obj, datetime):
                return obj.isoformat()
            elif hasattr(obj, 'dict'):  # Pydantic models
                return obj.dict()
            elif hasattr(obj, '__dict__'):  # Regular objects
                return obj.__dict__
            return str(obj)
        
        return json.dumps(data, default=json_serializer, ensure_ascii=False)
    
    def _deserialize_data(self, data: str) -> Any:
        """Deserialize data from Redis."""
        try:
            return json.loads(data)
        except (json.JSONDecodeError, TypeError):
            return data
    
    async def get(self, cache_type: str, identifier: str, **kwargs) -> Optional[Any]:
        """Get cached data."""
        if not self.connected:
            await self.connect()
            
        if not self.connected:
            return None
            
        try:
            cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
            data = await self.redis_client.get(cache_key)
            
            if data:
                logger.debug(f"Cache hit for key: {cache_key}")
                return self._deserialize_data(data)
            
            logger.debug(f"Cache miss for key: {cache_key}")
            return None
            
        except Exception as e:
            logger.error(f"Cache get error for {cache_type}:{identifier}: {e}")
            return None
    
    async def set(
        self, 
        cache_type: str, 
        identifier: str, 
        data: Any, 
        ttl: Optional[int] = None,
        **kwargs
    ) -> bool:
        """Set cached data with TTL."""
        if not self.connected:
            await self.connect()
            
        if not self.connected:
            return False
            
        try:
            cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
            serialized_data = self._serialize_data(data)
            
            # Use configured TTL or provided TTL
            ttl_seconds = ttl or self.ttl_config.get(cache_type, 3600)
            
            await self.redis_client.setex(cache_key, ttl_seconds, serialized_data)
            logger.debug(f"Cache set for key: {cache_key} (TTL: {ttl_seconds}s)")
            return True
            
        except Exception as e:
            logger.error(f"Cache set error for {cache_type}:{identifier}: {e}")
            return False
    
    async def delete(self, cache_type: str, identifier: str, **kwargs) -> bool:
        """Delete cached data."""
        if not self.connected:
            return False
            
        try:
            cache_key = self._generate_cache_key(cache_type, identifier, **kwargs)
            result = await self.redis_client.delete(cache_key)
            logger.debug(f"Cache delete for key: {cache_key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Cache delete error for {cache_type}:{identifier}: {e}")
            return False
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        if not self.connected:
            return 0
            
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries matching pattern: {pattern}")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Cache pattern invalidation error for {pattern}: {e}")
            return 0
    
    async def invalidate_user_cache(self, user_id: str) -> int:
        """Invalidate all cache entries for a specific user."""
        patterns = [
            f"stats:user:{user_id}:*",
            f"session:user:{user_id}:*", 
            f"prefs:user:{user_id}:*",
            f"trends:user:{user_id}:*"
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await self.invalidate_pattern(pattern)
            total_deleted += deleted
            
        logger.info(f"Invalidated {total_deleted} cache entries for user {user_id}")
        return total_deleted
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get Redis cache statistics."""
        if not self.connected:
            return {"connected": False}
            
        try:
            info = await self.redis_client.info()
            return {
                "connected": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"connected": False, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# Specialized cache methods for common use cases
class StatisticsCacheService(CacheService):
    """Specialized caching for statistics data."""
    
    async def get_user_statistics(
        self, 
        user_id: str, 
        filters: StatisticsFilters
    ) -> Optional[Dict[str, Any]]:
        """Get cached user statistics."""
        filters_dict = filters.dict() if hasattr(filters, 'dict') else filters.__dict__
        return await self.get('user_stats', user_id, filters=filters_dict)
    
    async def set_user_statistics(
        self, 
        user_id: str, 
        filters: StatisticsFilters,
        statistics: Dict[str, Any]
    ) -> bool:
        """Cache user statistics."""
        filters_dict = filters.dict() if hasattr(filters, 'dict') else filters.__dict__
        return await self.set('user_stats', user_id, statistics, filters=filters_dict)
    
    async def get_trend_data(
        self, 
        user_id: str, 
        time_period: str,
        filters: StatisticsFilters
    ) -> Optional[Dict[str, Any]]:
        """Get cached trend data."""
        filters_dict = filters.dict() if hasattr(filters, 'dict') else filters.__dict__
        return await self.get(
            'trend_data', 
            user_id, 
            period=time_period,
            filters=filters_dict
        )
    
    async def set_trend_data(
        self, 
        user_id: str, 
        time_period: str,
        filters: StatisticsFilters,
        trend_data: Dict[str, Any]
    ) -> bool:
        """Cache trend data."""
        filters_dict = filters.dict() if hasattr(filters, 'dict') else filters.__dict__
        return await self.set(
            'trend_data', 
            user_id, 
            trend_data,
            period=time_period,
            filters=filters_dict
        )


class AnalysisCacheService(CacheService):
    """Specialized caching for AI analysis results."""
    
    async def get_hand_analysis(
        self, 
        hand_hash: str, 
        ai_provider: str,
        prompt_version: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached hand analysis."""
        return await self.get(
            'hand_analysis', 
            hand_hash,
            provider=ai_provider,
            prompt_version=prompt_version
        )
    
    async def set_hand_analysis(
        self, 
        hand_hash: str, 
        ai_provider: str,
        prompt_version: str,
        analysis: Dict[str, Any]
    ) -> bool:
        """Cache hand analysis."""
        return await self.set(
            'hand_analysis', 
            hand_hash, 
            analysis,
            provider=ai_provider,
            prompt_version=prompt_version
        )


# Global cache service instances
cache_service = CacheService()
stats_cache = StatisticsCacheService()
analysis_cache = AnalysisCacheService()


async def get_cache_service() -> CacheService:
    """Dependency injection for cache service."""
    if not cache_service.connected:
        await cache_service.connect()
    return cache_service


async def get_stats_cache() -> StatisticsCacheService:
    """Dependency injection for statistics cache."""
    if not stats_cache.connected:
        await stats_cache.connect()
    return stats_cache


async def get_analysis_cache() -> AnalysisCacheService:
    """Dependency injection for analysis cache."""
    if not analysis_cache.connected:
        await analysis_cache.connect()
    return analysis_cache