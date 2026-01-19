#!/usr/bin/env python3
"""
Comprehensive migration system test (no database required).
"""
import sys
import subprocess
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def run_command(command: list[str]) -> tuple[bool, str]:
    """Run a command and return success status and output."""
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            cwd=backend_dir,
            timeout=30
        )
        return result.returncode == 0, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def test_migration_commands():
    """Test migration commands that don't require database connection."""
    print("Testing migration commands...")
    
    tests = [
        {
            'name': 'Migration History',
            'command': ['python', 'migrate.py', 'history'],
            'expected_in_output': ['001', 'Initial schema creation']
        },
        {
            'name': 'Head Revisions',
            'command': ['python', 'migrate.py', 'heads'],
            'expected_in_output': ['001', 'head']
        },
        {
            'name': 'Alembic History',
            'command': ['alembic', 'history'],
            'expected_in_output': ['001', 'Initial schema creation']
        }
    ]
    
    all_passed = True
    
    for test in tests:
        print(f"  Testing {test['name']}...")
        success, output = run_command(test['command'])
        
        if not success:
            print(f"    ❌ Command failed: {output}")
            all_passed = False
            continue
        
        # Check for expected content
        missing_content = []
        for expected in test['expected_in_output']:
            if expected not in output:
                missing_content.append(expected)
        
        if missing_content:
            print(f"    ❌ Missing expected content: {missing_content}")
            print(f"    Output: {output}")
            all_passed = False
        else:
            print(f"    ✅ {test['name']} passed")
    
    return all_passed


def test_migration_file_generation():
    """Test that we can generate new migration files."""
    print("Testing migration file generation...")
    
    # Test creating an empty migration
    print("  Testing empty migration creation...")
    success, output = run_command([
        'python', 'migrate.py', 'create-empty', 'Test migration'
    ])
    
    if success and 'Generating' in output:
        print("    ✅ Empty migration creation works")
        
        # Find the generated file and clean it up
        versions_dir = backend_dir / "alembic" / "versions"
        migration_files = list(versions_dir.glob("*test_migration.py"))
        
        for file in migration_files:
            if file.name != "001_initial_schema_creation.py":
                file.unlink()
                print(f"    🧹 Cleaned up test file: {file.name}")
        
        return True
    else:
        print(f"    ❌ Empty migration creation failed: {output}")
        return False


def test_model_consistency():
    """Test that models are consistent with migration."""
    print("Testing model consistency...")
    
    try:
        # Import models and check metadata
        from app.models.base import Base
        from app.models.user import User
        from app.models.hand import PokerHand
        from app.models.analysis import AnalysisResult
        from app.models.statistics import StatisticsCache
        from app.models.monitoring import FileMonitoring
        
        # Get table names from models
        model_tables = set(Base.metadata.tables.keys())
        expected_tables = {
            'users', 'poker_hands', 'analysis_results', 
            'statistics_cache', 'file_monitoring'
        }
        
        if model_tables == expected_tables:
            print("    ✅ Model tables match expected schema")
            return True
        else:
            missing = expected_tables - model_tables
            extra = model_tables - expected_tables
            if missing:
                print(f"    ❌ Missing tables: {missing}")
            if extra:
                print(f"    ❌ Extra tables: {extra}")
            return False
            
    except Exception as e:
        print(f"    ❌ Model import failed: {e}")
        return False


def test_configuration():
    """Test configuration loading."""
    print("Testing configuration...")
    
    try:
        from app.core.config import settings
        
        # Check that essential settings are loaded
        required_settings = [
            'DATABASE_URL', 'SECRET_KEY', 'PROJECT_NAME'
        ]
        
        missing_settings = []
        for setting in required_settings:
            if not hasattr(settings, setting) or not getattr(settings, setting):
                missing_settings.append(setting)
        
        if missing_settings:
            print(f"    ❌ Missing settings: {missing_settings}")
            return False
        
        print("    ✅ Configuration loaded successfully")
        print(f"    Database URL: {settings.DATABASE_URL}")
        print(f"    Environment: {settings.ENVIRONMENT}")
        return True
        
    except Exception as e:
        print(f"    ❌ Configuration loading failed: {e}")
        return False


def main():
    """Main test function."""
    print("Professional Poker Analyzer - Migration System Test")
    print("=" * 55)
    print()
    
    all_tests_passed = True
    
    # Test configuration
    if not test_configuration():
        all_tests_passed = False
    print()
    
    # Test model consistency
    if not test_model_consistency():
        all_tests_passed = False
    print()
    
    # Test migration commands
    if not test_migration_commands():
        all_tests_passed = False
    print()
    
    # Test migration file generation
    if not test_migration_file_generation():
        all_tests_passed = False
    print()
    
    if all_tests_passed:
        print("🎉 All migration system tests passed!")
        print("\nMigration system is fully configured and ready to use!")
        print("\nTo use with a database:")
        print("1. Start PostgreSQL database")
        print("2. Run: python migrate.py upgrade")
        print("3. Run: python validate_migration.py")
        print("\nAvailable commands:")
        print("- python migrate.py upgrade          # Apply migrations")
        print("- python migrate.py current          # Show current revision")
        print("- python migrate.py history          # Show migration history")
        print("- python migrate.py create 'message' # Create new migration")
        return 0
    else:
        print("❌ Some migration system tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())