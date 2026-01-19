#!/usr/bin/env python3
"""
Schema validation script to ensure all tables, indexes, and constraints are properly defined.
"""
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.models.base import Base
from app.models import *


def validate_schema():
    """Validate the database schema definition."""
    print("🔍 Validating database schema...")
    
    # Check that all expected tables are defined
    expected_tables = {
        'users', 'poker_hands', 'analysis_results', 
        'statistics_cache', 'file_monitoring'
    }
    
    actual_tables = set(Base.metadata.tables.keys())
    
    print(f"📋 Expected tables: {sorted(expected_tables)}")
    print(f"📋 Actual tables: {sorted(actual_tables)}")
    
    if expected_tables == actual_tables:
        print("✅ All expected tables are defined")
    else:
        missing = expected_tables - actual_tables
        extra = actual_tables - expected_tables
        if missing:
            print(f"❌ Missing tables: {missing}")
        if extra:
            print(f"⚠️  Extra tables: {extra}")
        return False
    
    # Validate table structures
    print("\n🔍 Validating table structures...")
    
    # Check users table
    users_table = Base.metadata.tables['users']
    required_users_columns = {
        'id', 'email', 'password_hash', 'api_keys', 
        'hand_history_paths', 'preferences', 'created_at', 'updated_at'
    }
    users_columns = set(users_table.columns.keys())
    
    if required_users_columns.issubset(users_columns):
        print("✅ Users table structure is valid")
    else:
        missing = required_users_columns - users_columns
        print(f"❌ Users table missing columns: {missing}")
        return False
    
    # Check poker_hands table
    hands_table = Base.metadata.tables['poker_hands']
    required_hands_columns = {
        'id', 'user_id', 'hand_id', 'platform', 'game_type', 
        'game_format', 'stakes', 'blinds', 'date_played', 
        'player_cards', 'board_cards', 'position', 'actions', 
        'result', 'pot_size', 'rake', 'raw_text', 'created_at'
    }
    hands_columns = set(hands_table.columns.keys())
    
    if required_hands_columns.issubset(hands_columns):
        print("✅ Poker hands table structure is valid")
    else:
        missing = required_hands_columns - hands_columns
        print(f"❌ Poker hands table missing columns: {missing}")
        return False
    
    # Check indexes
    print("\n🔍 Validating indexes...")
    
    # Count indexes for each table
    index_counts = {}
    for table_name, table in Base.metadata.tables.items():
        index_counts[table_name] = len(table.indexes)
    
    print(f"📊 Index counts: {index_counts}")
    
    # Validate that key tables have indexes
    if index_counts.get('poker_hands', 0) >= 4:  # Should have multiple indexes
        print("✅ Poker hands table has sufficient indexes")
    else:
        print("⚠️  Poker hands table may need more indexes")
    
    # Check constraints
    print("\n🔍 Validating constraints...")
    
    constraint_counts = {}
    for table_name, table in Base.metadata.tables.items():
        constraint_counts[table_name] = len(table.constraints)
    
    print(f"📊 Constraint counts: {constraint_counts}")
    
    # Validate foreign keys
    fk_count = 0
    for table in Base.metadata.tables.values():
        for constraint in table.constraints:
            if hasattr(constraint, 'referred_table'):
                fk_count += 1
    
    print(f"🔗 Total foreign key constraints: {fk_count}")
    
    if fk_count >= 4:  # Should have FKs for user relationships
        print("✅ Foreign key constraints are properly defined")
    else:
        print("⚠️  May need more foreign key constraints")
    
    print("\n✅ Schema validation completed successfully!")
    return True


if __name__ == "__main__":
    success = validate_schema()
    sys.exit(0 if success else 1)