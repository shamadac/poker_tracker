#!/usr/bin/env python3
"""
Migration validation script for Professional Poker Analyzer.
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import settings


async def validate_migration():
    """Validate that the migration creates the expected schema."""
    print("Validating migration schema...")
    
    # Create engine
    engine = create_async_engine(settings.DATABASE_URL)
    
    try:
        async with engine.begin() as conn:
            # Check if all tables exist
            tables_query = text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            
            result = await conn.execute(tables_query)
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'alembic_version',
                'analysis_results',
                'file_monitoring',
                'poker_hands',
                'statistics_cache',
                'users'
            ]
            
            print(f"Found tables: {tables}")
            
            missing_tables = set(expected_tables) - set(tables)
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            
            # Check users table structure
            users_columns_query = text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position;
            """)
            
            result = await conn.execute(users_columns_query)
            users_columns = result.fetchall()
            print(f"Users table columns: {len(users_columns)} columns found")
            
            # Check poker_hands table structure
            hands_columns_query = text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns 
                WHERE table_name = 'poker_hands' 
                ORDER BY ordinal_position;
            """)
            
            result = await conn.execute(hands_columns_query)
            hands_columns = result.fetchall()
            print(f"Poker hands table columns: {len(hands_columns)} columns found")
            
            # Check foreign key constraints
            fk_query = text("""
                SELECT 
                    tc.table_name, 
                    kcu.column_name, 
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name 
                FROM 
                    information_schema.table_constraints AS tc 
                    JOIN information_schema.key_column_usage AS kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage AS ccu
                      ON ccu.constraint_name = tc.constraint_name
                      AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                ORDER BY tc.table_name;
            """)
            
            result = await conn.execute(fk_query)
            foreign_keys = result.fetchall()
            print(f"Foreign key constraints: {len(foreign_keys)} found")
            
            # Check indexes
            indexes_query = text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    indexdef
                FROM pg_indexes 
                WHERE schemaname = 'public'
                ORDER BY tablename, indexname;
            """)
            
            result = await conn.execute(indexes_query)
            indexes = result.fetchall()
            print(f"Indexes: {len(indexes)} found")
            
            # Validate specific constraints
            constraints_query = text("""
                SELECT 
                    tc.table_name,
                    tc.constraint_name,
                    tc.constraint_type
                FROM information_schema.table_constraints tc
                WHERE tc.table_schema = 'public'
                AND tc.constraint_type IN ('UNIQUE', 'PRIMARY KEY')
                ORDER BY tc.table_name, tc.constraint_type;
            """)
            
            result = await conn.execute(constraints_query)
            constraints = result.fetchall()
            print(f"Constraints: {len(constraints)} found")
            
            print("✅ Migration validation completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Migration validation failed: {e}")
        return False
    
    finally:
        await engine.dispose()


async def test_basic_operations():
    """Test basic database operations after migration."""
    print("\nTesting basic database operations...")
    
    engine = create_async_engine(settings.DATABASE_URL)
    
    try:
        async with engine.begin() as conn:
            # Test inserting a user
            insert_user_query = text("""
                INSERT INTO users (id, email, password_hash, api_keys, hand_history_paths, preferences)
                VALUES (gen_random_uuid(), 'test@example.com', 'hashed_password', '{}', '{}', '{}')
                RETURNING id;
            """)
            
            result = await conn.execute(insert_user_query)
            user_id = result.fetchone()[0]
            print(f"✅ Successfully inserted test user: {user_id}")
            
            # Test inserting a poker hand
            insert_hand_query = text("""
                INSERT INTO poker_hands (
                    id, user_id, hand_id, platform, game_type, is_play_money
                ) VALUES (
                    gen_random_uuid(), :user_id, 'TEST123', 'pokerstars', 'Hold''em No Limit', true
                ) RETURNING id;
            """)
            
            result = await conn.execute(insert_hand_query, {"user_id": user_id})
            hand_id = result.fetchone()[0]
            print(f"✅ Successfully inserted test poker hand: {hand_id}")
            
            # Test foreign key relationship
            select_query = text("""
                SELECT h.hand_id, u.email 
                FROM poker_hands h 
                JOIN users u ON h.user_id = u.id 
                WHERE h.id = :hand_id;
            """)
            
            result = await conn.execute(select_query, {"hand_id": hand_id})
            row = result.fetchone()
            print(f"✅ Successfully joined tables: {row[0]} -> {row[1]}")
            
            # Clean up test data
            await conn.execute(text("DELETE FROM poker_hands WHERE id = :hand_id"), {"hand_id": hand_id})
            await conn.execute(text("DELETE FROM users WHERE id = :user_id"), {"user_id": user_id})
            print("✅ Test data cleaned up")
            
            print("✅ Basic operations test completed successfully!")
            return True
            
    except Exception as e:
        print(f"❌ Basic operations test failed: {e}")
        return False
    
    finally:
        await engine.dispose()


async def main():
    """Main validation function."""
    print("Professional Poker Analyzer - Migration Validation")
    print("=" * 50)
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print()
    
    # Validate migration
    migration_valid = await validate_migration()
    if not migration_valid:
        return 1
    
    # Test basic operations
    operations_valid = await test_basic_operations()
    if not operations_valid:
        return 1
    
    print("\n🎉 All validation tests passed!")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))