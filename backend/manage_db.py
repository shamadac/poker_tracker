#!/usr/bin/env python3
"""
Database management script for Professional Poker Analyzer.
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import create_tables, drop_tables, check_database_connection
from app.core.config import settings


async def create_all_tables():
    """Create all database tables."""
    print("Creating database tables...")
    try:
        await create_tables()
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False
    return True


async def drop_all_tables():
    """Drop all database tables."""
    print("Dropping database tables...")
    try:
        await drop_tables()
        print("✅ Database tables dropped successfully!")
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        return False
    return True


async def test_connection():
    """Test database connection."""
    print("Testing database connection...")
    try:
        success = await check_database_connection()
        if success:
            print("✅ Database connection successful!")
        else:
            print("❌ Database connection failed!")
        return success
    except Exception as e:
        print(f"❌ Error testing connection: {e}")
        return False


async def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python manage_db.py [create|drop|test]")
        print("  create - Create all database tables")
        print("  drop   - Drop all database tables")
        print("  test   - Test database connection")
        return
    
    command = sys.argv[1].lower()
    
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print()
    
    if command == "create":
        await create_all_tables()
    elif command == "drop":
        confirm = input("Are you sure you want to drop all tables? (yes/no): ")
        if confirm.lower() == "yes":
            await drop_all_tables()
        else:
            print("Operation cancelled.")
    elif command == "test":
        await test_connection()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: create, drop, test")


if __name__ == "__main__":
    asyncio.run(main())