#!/usr/bin/env python3
"""
Alembic migration management script for Professional Poker Analyzer.
"""
import os
import sys
import subprocess
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.core.config import settings


def run_alembic_command(command: list[str]) -> int:
    """Run an Alembic command with proper environment setup."""
    # Set environment variables for Alembic
    env = os.environ.copy()
    env['DATABASE_URL'] = settings.DATABASE_URL
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Run the command
    try:
        result = subprocess.run(['alembic'] + command, env=env, check=False)
        return result.returncode
    except FileNotFoundError:
        print("❌ Alembic not found. Please install it with: pip install alembic")
        return 1


def upgrade_database(revision: str = "head") -> int:
    """Upgrade database to a specific revision."""
    print(f"Upgrading database to revision: {revision}")
    return run_alembic_command(['upgrade', revision])


def downgrade_database(revision: str) -> int:
    """Downgrade database to a specific revision."""
    print(f"Downgrading database to revision: {revision}")
    return run_alembic_command(['downgrade', revision])


def create_migration(message: str, autogenerate: bool = True) -> int:
    """Create a new migration."""
    print(f"Creating new migration: {message}")
    command = ['revision']
    if autogenerate:
        command.append('--autogenerate')
    command.extend(['-m', message])
    return run_alembic_command(command)


def show_current_revision() -> int:
    """Show current database revision."""
    print("Current database revision:")
    return run_alembic_command(['current'])


def show_migration_history() -> int:
    """Show migration history."""
    print("Migration history:")
    return run_alembic_command(['history'])


def show_heads() -> int:
    """Show head revisions."""
    print("Head revisions:")
    return run_alembic_command(['heads'])


def validate_database() -> int:
    """Validate current database state."""
    print("Validating database state...")
    return run_alembic_command(['check'])


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python migrate.py [command] [options]")
        print("\nAvailable commands:")
        print("  upgrade [revision]     - Upgrade database (default: head)")
        print("  downgrade <revision>   - Downgrade database to revision")
        print("  create <message>       - Create new migration with autogenerate")
        print("  create-empty <message> - Create empty migration")
        print("  current               - Show current revision")
        print("  history               - Show migration history")
        print("  heads                 - Show head revisions")
        print("  validate              - Validate database state")
        print("\nExamples:")
        print("  python migrate.py upgrade")
        print("  python migrate.py create 'Add user preferences'")
        print("  python migrate.py downgrade -1")
        return 1
    
    command = sys.argv[1].lower()
    
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print()
    
    if command == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        return upgrade_database(revision)
    
    elif command == "downgrade":
        if len(sys.argv) < 3:
            print("❌ Downgrade requires a revision argument")
            return 1
        revision = sys.argv[2]
        return downgrade_database(revision)
    
    elif command == "create":
        if len(sys.argv) < 3:
            print("❌ Create requires a message argument")
            return 1
        message = sys.argv[2]
        return create_migration(message, autogenerate=True)
    
    elif command == "create-empty":
        if len(sys.argv) < 3:
            print("❌ Create-empty requires a message argument")
            return 1
        message = sys.argv[2]
        return create_migration(message, autogenerate=False)
    
    elif command == "current":
        return show_current_revision()
    
    elif command == "history":
        return show_migration_history()
    
    elif command == "heads":
        return show_heads()
    
    elif command == "validate":
        return validate_database()
    
    else:
        print(f"❌ Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())