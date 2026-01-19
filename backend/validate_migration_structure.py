#!/usr/bin/env python3
"""
Migration structure validation script (no database required).
"""
import sys
import ast
import importlib.util
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))


def validate_migration_file(migration_path: Path) -> bool:
    """Validate a migration file structure."""
    print(f"Validating migration file: {migration_path.name}")
    
    try:
        # Read the migration file
        with open(migration_path, 'r') as f:
            content = f.read()
        
        # Parse the AST to validate structure
        tree = ast.parse(content)
        
        # Check for required variables
        required_vars = ['revision', 'down_revision', 'branch_labels', 'depends_on']
        found_vars = []
        
        # Check for required functions
        required_functions = ['upgrade', 'downgrade']
        found_functions = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        found_vars.append(target.id)
            elif isinstance(node, ast.AnnAssign):
                if isinstance(node.target, ast.Name):
                    found_vars.append(node.target.id)
            elif isinstance(node, ast.FunctionDef):
                found_functions.append(node.name)
        
        # Validate required variables
        missing_vars = set(required_vars) - set(found_vars)
        if missing_vars:
            print(f"  ❌ Missing required variables: {missing_vars}")
            return False
        
        # Validate required functions
        missing_functions = set(required_functions) - set(found_functions)
        if missing_functions:
            print(f"  ❌ Missing required functions: {missing_functions}")
            return False
        
        # Check if file can be imported (syntax validation)
        spec = importlib.util.spec_from_file_location("migration", migration_path)
        if spec is None:
            print(f"  ❌ Cannot create module spec")
            return False
        
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Validate revision ID
        if not hasattr(module, 'revision') or not module.revision:
            print(f"  ❌ Invalid revision ID")
            return False
        
        print(f"  ✅ Migration file is valid (revision: {module.revision})")
        return True
        
    except SyntaxError as e:
        print(f"  ❌ Syntax error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Validation error: {e}")
        return False


def validate_alembic_config() -> bool:
    """Validate Alembic configuration files."""
    print("Validating Alembic configuration...")
    
    # Check alembic.ini
    alembic_ini = backend_dir / "alembic.ini"
    if not alembic_ini.exists():
        print("  ❌ alembic.ini not found")
        return False
    
    # Check env.py
    env_py = backend_dir / "alembic" / "env.py"
    if not env_py.exists():
        print("  ❌ alembic/env.py not found")
        return False
    
    # Check versions directory
    versions_dir = backend_dir / "alembic" / "versions"
    if not versions_dir.exists():
        print("  ❌ alembic/versions directory not found")
        return False
    
    print("  ✅ Alembic configuration files found")
    return True


def validate_model_imports() -> bool:
    """Validate that all models can be imported."""
    print("Validating model imports...")
    
    try:
        # Import all models
        from app.models.base import Base
        from app.models.user import User
        from app.models.hand import PokerHand
        from app.models.analysis import AnalysisResult
        from app.models.statistics import StatisticsCache
        from app.models.monitoring import FileMonitoring
        
        print("  ✅ All models imported successfully")
        
        # Check that all models are registered with Base
        tables = Base.metadata.tables
        expected_tables = ['users', 'poker_hands', 'analysis_results', 'statistics_cache', 'file_monitoring']
        
        found_tables = list(tables.keys())
        missing_tables = set(expected_tables) - set(found_tables)
        
        if missing_tables:
            print(f"  ❌ Missing tables in metadata: {missing_tables}")
            return False
        
        print(f"  ✅ All expected tables found in metadata: {found_tables}")
        return True
        
    except ImportError as e:
        print(f"  ❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Model validation error: {e}")
        return False


def validate_migration_scripts() -> bool:
    """Validate all migration scripts."""
    print("Validating migration scripts...")
    
    versions_dir = backend_dir / "alembic" / "versions"
    migration_files = list(versions_dir.glob("*.py"))
    
    if not migration_files:
        print("  ❌ No migration files found")
        return False
    
    print(f"  Found {len(migration_files)} migration files")
    
    all_valid = True
    for migration_file in migration_files:
        if migration_file.name == "__pycache__":
            continue
        if not validate_migration_file(migration_file):
            all_valid = False
    
    return all_valid


def main():
    """Main validation function."""
    print("Professional Poker Analyzer - Migration Structure Validation")
    print("=" * 60)
    print()
    
    all_valid = True
    
    # Validate Alembic configuration
    if not validate_alembic_config():
        all_valid = False
    print()
    
    # Validate model imports
    if not validate_model_imports():
        all_valid = False
    print()
    
    # Validate migration scripts
    if not validate_migration_scripts():
        all_valid = False
    print()
    
    if all_valid:
        print("🎉 All migration structure validation tests passed!")
        print("\nNext steps:")
        print("1. Start PostgreSQL database")
        print("2. Run: python migrate.py upgrade")
        print("3. Run: python validate_migration.py (requires database)")
        return 0
    else:
        print("❌ Some validation tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())