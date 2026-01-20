#!/usr/bin/env python3
"""
Script to seed education content into the database.
"""
import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.database import get_async_session
from app.services.education_content_seeder import seed_education_content


async def main():
    """Main function to seed education content."""
    print("Starting education content seeding...")
    
    try:
        async with get_async_session() as db:
            await seed_education_content(db)
        print("✅ Education content seeded successfully!")
    except Exception as e:
        print(f"❌ Error seeding education content: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())