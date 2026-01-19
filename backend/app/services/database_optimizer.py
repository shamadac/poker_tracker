#!/usr/bin/env python3
"""
Database optimization service for poker analyzer.

This service implements:
- Connection pooling optimization
- Query performance monitoring
- Index usage analysis
- Query optimization recommendations
"""
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy import text, inspect
from sqlalchemy.engine import Engine

from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class DatabaseOptimizer:
    """Database performance optimization and monitoring service."""
    
    def __init__(self):
        self.query_stats = {}
        self.slow_query_threshold = 1.0  # seconds
        self.connection_pool_stats = {}
        
    async def create_optimized_engine(self) -> AsyncSession:
        """Create database engine with optimized connection pooling."""
        
        # Optimized connection pool settings
        engine = create_async_engine(
            settings.DATABASE_URL,
            # Connection pool settings
            poolclass=QueuePool,
            pool_size=20,           # Base number of connections
            max_overflow=30,        # Additional connections when needed
            pool_pre_ping=True,     # Validate connections before use
            pool_recycle=3600,      # Recycle connections every hour
            
            # Query optimization settings
            echo=False,             # Set to True for query debugging
            echo_pool=False,        # Set to True for pool debugging
            
            # Connection settings
            connect_args={
                "server_settings": {
                    "application_name": "poker_analyzer",
                    "jit": "off",  # Disable JIT for consistent performance
                }
            }
        )
        
        return async_sessionmaker(
            engine, 
            class_=AsyncSession,
            expire_on_commit=False
        )
    
    @asynccontextmanager
    async def monitored_query(self, db: AsyncSession, query_name: str):
        """Context manager to monitor query performance."""
        start_time = time.time()
        
        try:
            yield
        finally:
            execution_time = time.time() - start_time
            
            # Record query statistics
            if query_name not in self.query_stats:
                self.query_stats[query_name] = {
                    'count': 0,
                    'total_time': 0.0,
                    'avg_time': 0.0,
                    'max_time': 0.0,
                    'slow_queries': 0
                }
            
            stats = self.query_stats[query_name]
            stats['count'] += 1
            stats['total_time'] += execution_time
            stats['avg_time'] = stats['total_time'] / stats['count']
            stats['max_time'] = max(stats['max_time'], execution_time)
            
            if execution_time > self.slow_query_threshold:
                stats['slow_queries'] += 1
                logger.warning(
                    f"Slow query detected: {query_name} took {execution_time:.3f}s"
                )
    
    async def analyze_query_performance(self, db: AsyncSession) -> Dict[str, Any]:
        """Analyze database query performance and provide recommendations."""
        
        performance_analysis = {
            'query_stats': self.query_stats.copy(),
            'recommendations': [],
            'index_analysis': await self._analyze_indexes(db),
            'connection_pool_stats': await self._get_pool_stats(db),
            'database_stats': await self._get_database_stats(db)
        }
        
        # Generate recommendations based on analysis
        recommendations = []
        
        # Check for slow queries
        for query_name, stats in self.query_stats.items():
            if stats['slow_queries'] > 0:
                slow_percentage = (stats['slow_queries'] / stats['count']) * 100
                recommendations.append({
                    'type': 'slow_query',
                    'query': query_name,
                    'message': f"Query '{query_name}' is slow {slow_percentage:.1f}% of the time",
                    'suggestion': "Consider adding indexes or optimizing the query"
                })
        
        # Check for frequently executed queries
        for query_name, stats in self.query_stats.items():
            if stats['count'] > 100 and stats['avg_time'] > 0.1:
                recommendations.append({
                    'type': 'frequent_query',
                    'query': query_name,
                    'message': f"Query '{query_name}' executed {stats['count']} times with avg time {stats['avg_time']:.3f}s",
                    'suggestion': "Consider caching results or optimizing the query"
                })
        
        performance_analysis['recommendations'] = recommendations
        return performance_analysis
    
    async def _analyze_indexes(self, db: AsyncSession) -> Dict[str, Any]:
        """Analyze database indexes and their usage."""
        try:
            # Get index usage statistics
            index_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes 
                ORDER BY idx_scan DESC;
            """)
            
            result = await db.execute(index_query)
            indexes = result.fetchall()
            
            # Get unused indexes
            unused_indexes_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname
                FROM pg_stat_user_indexes 
                WHERE idx_scan = 0
                AND indexname NOT LIKE '%_pkey';
            """)
            
            unused_result = await db.execute(unused_indexes_query)
            unused_indexes = unused_result.fetchall()
            
            return {
                'total_indexes': len(indexes),
                'unused_indexes': len(unused_indexes),
                'index_usage': [dict(row._mapping) for row in indexes],
                'unused_index_list': [dict(row._mapping) for row in unused_indexes]
            }
            
        except Exception as e:
            logger.error(f"Error analyzing indexes: {e}")
            return {'error': str(e)}
    
    async def _get_pool_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get connection pool statistics."""
        try:
            engine = db.get_bind()
            pool = engine.pool
            
            return {
                'pool_size': pool.size(),
                'checked_in': pool.checkedin(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'invalid': pool.invalid()
            }
            
        except Exception as e:
            logger.error(f"Error getting pool stats: {e}")
            return {'error': str(e)}
    
    async def _get_database_stats(self, db: AsyncSession) -> Dict[str, Any]:
        """Get general database statistics."""
        try:
            # Get database size and connection info
            stats_query = text("""
                SELECT 
                    pg_size_pretty(pg_database_size(current_database())) as database_size,
                    (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections,
                    (SELECT count(*) FROM pg_stat_activity) as total_connections;
            """)
            
            result = await db.execute(stats_query)
            stats = result.fetchone()
            
            # Get table sizes
            table_sizes_query = text("""
                SELECT 
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                FROM pg_tables 
                WHERE schemaname = 'public'
                ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
            """)
            
            table_result = await db.execute(table_sizes_query)
            table_sizes = table_result.fetchall()
            
            return {
                'database_size': stats[0] if stats else 'Unknown',
                'active_connections': stats[1] if stats else 0,
                'total_connections': stats[2] if stats else 0,
                'table_sizes': [dict(row._mapping) for row in table_sizes]
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}
    
    async def optimize_statistics_queries(self, db: AsyncSession) -> Dict[str, Any]:
        """Optimize common statistics queries with better indexes."""
        
        optimization_results = {
            'indexes_created': [],
            'indexes_failed': [],
            'recommendations': []
        }
        
        # Recommended indexes for poker hand queries
        recommended_indexes = [
            {
                'name': 'idx_poker_hands_user_date_platform',
                'table': 'poker_hands',
                'columns': ['user_id', 'date_played', 'platform'],
                'reason': 'Optimize filtered statistics queries'
            },
            {
                'name': 'idx_poker_hands_game_type_stakes',
                'table': 'poker_hands', 
                'columns': ['game_type', 'stakes'],
                'reason': 'Optimize game type and stakes filtering'
            },
            {
                'name': 'idx_poker_hands_position_result',
                'table': 'poker_hands',
                'columns': ['position', 'result'],
                'reason': 'Optimize positional analysis queries'
            },
            {
                'name': 'idx_analysis_results_hand_provider_created',
                'table': 'analysis_results',
                'columns': ['hand_id', 'ai_provider', 'created_at'],
                'reason': 'Optimize analysis result lookups'
            }
        ]
        
        for index_info in recommended_indexes:
            try:
                # Check if index already exists
                check_query = text("""
                    SELECT indexname 
                    FROM pg_indexes 
                    WHERE tablename = :table_name 
                    AND indexname = :index_name;
                """)
                
                result = await db.execute(
                    check_query, 
                    {'table_name': index_info['table'], 'index_name': index_info['name']}
                )
                
                if result.fetchone():
                    optimization_results['recommendations'].append({
                        'type': 'index_exists',
                        'message': f"Index {index_info['name']} already exists"
                    })
                    continue
                
                # Create the index
                columns_str = ', '.join(index_info['columns'])
                create_index_query = text(f"""
                    CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_info['name']} 
                    ON {index_info['table']} ({columns_str});
                """)
                
                await db.execute(create_index_query)
                await db.commit()
                
                optimization_results['indexes_created'].append({
                    'name': index_info['name'],
                    'table': index_info['table'],
                    'columns': index_info['columns'],
                    'reason': index_info['reason']
                })
                
                logger.info(f"Created index: {index_info['name']}")
                
            except Exception as e:
                optimization_results['indexes_failed'].append({
                    'name': index_info['name'],
                    'error': str(e)
                })
                logger.error(f"Failed to create index {index_info['name']}: {e}")
        
        return optimization_results
    
    async def vacuum_analyze_tables(self, db: AsyncSession) -> Dict[str, Any]:
        """Run VACUUM ANALYZE on important tables for performance."""
        
        vacuum_results = {
            'tables_processed': [],
            'tables_failed': [],
            'total_time': 0.0
        }
        
        # Important tables to vacuum and analyze
        important_tables = [
            'poker_hands',
            'analysis_results', 
            'statistics_cache',
            'users',
            'file_monitoring'
        ]
        
        start_time = time.time()
        
        for table in important_tables:
            try:
                table_start = time.time()
                
                # Run VACUUM ANALYZE
                vacuum_query = text(f"VACUUM ANALYZE {table};")
                await db.execute(vacuum_query)
                await db.commit()
                
                table_time = time.time() - table_start
                vacuum_results['tables_processed'].append({
                    'table': table,
                    'time': round(table_time, 3)
                })
                
                logger.info(f"VACUUM ANALYZE completed for {table} in {table_time:.3f}s")
                
            except Exception as e:
                vacuum_results['tables_failed'].append({
                    'table': table,
                    'error': str(e)
                })
                logger.error(f"VACUUM ANALYZE failed for {table}: {e}")
        
        vacuum_results['total_time'] = round(time.time() - start_time, 3)
        return vacuum_results


# Global database optimizer instance
db_optimizer = DatabaseOptimizer()


async def get_db_optimizer() -> DatabaseOptimizer:
    """Dependency injection for database optimizer."""
    return db_optimizer