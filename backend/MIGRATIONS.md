# Database Migrations

This document describes the database migration system for the Professional Poker Analyzer.

## Overview

The project uses Alembic for database schema migrations with PostgreSQL. The migration system is configured to work with async SQLAlchemy and supports both development and production environments.

## Setup

### Prerequisites

1. PostgreSQL 15+ running locally or accessible via network
2. Python environment with required dependencies installed
3. Environment variables configured (see `.env.example`)

### Environment Variables

Create a `.env` file in the `backend` directory with:

```bash
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/poker_analyzer
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=poker_analyzer
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
SECRET_KEY=your-secret-key-at-least-32-characters-long
```

## Migration Commands

### Using the Migration Script (Recommended)

The `migrate.py` script provides a convenient interface for common migration operations:

```bash
# Upgrade to latest migration
python migrate.py upgrade

# Upgrade to specific revision
python migrate.py upgrade abc123

# Create new migration with autogenerate
python migrate.py create "Add user preferences table"

# Create empty migration
python migrate.py create-empty "Custom data migration"

# Downgrade to previous revision
python migrate.py downgrade -1

# Show current revision
python migrate.py current

# Show migration history
python migrate.py history

# Validate database state
python migrate.py validate
```

### Using Alembic Directly

You can also use Alembic commands directly:

```bash
# Set environment variable
export DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/poker_analyzer

# Run migrations
alembic upgrade head
alembic current
alembic history
alembic revision --autogenerate -m "Description"
```

## Migration Files

### Current Migrations

- `001_initial_schema_creation.py` - Creates all initial tables and indexes

### Migration Structure

```
backend/alembic/
├── versions/           # Migration files
├── env.py             # Alembic environment configuration
└── script.py.mako     # Migration template
```

## Database Schema

### Tables Created

1. **users** - User accounts and preferences
   - Stores encrypted API keys for AI providers
   - Hand history directory paths
   - User preferences and settings

2. **poker_hands** - Comprehensive poker hand data
   - Multi-platform support (PokerStars, GGPoker)
   - Complete hand information including actions, results
   - Tournament and cash game specific data

3. **analysis_results** - AI analysis results
   - Multiple analyses per hand
   - Provider-specific analysis data
   - Confidence scores and metadata

4. **statistics_cache** - Cached poker statistics
   - Performance optimization for complex calculations
   - Configurable TTL and cache invalidation

5. **file_monitoring** - Hand history file monitoring
   - Directory monitoring configuration
   - Platform-specific path tracking

### Key Features

- **UUID Primary Keys** - All tables use UUID primary keys for scalability
- **Proper Foreign Keys** - Referential integrity with CASCADE deletes
- **Comprehensive Indexes** - Optimized for common query patterns
- **JSONB Columns** - Flexible data storage for complex structures
- **Timezone Support** - All timestamps include timezone information

## Validation

### Automatic Validation

Run the validation script to verify migration integrity:

```bash
python validate_migration.py
```

This script:
- Verifies all expected tables exist
- Checks column definitions and constraints
- Validates foreign key relationships
- Tests basic CRUD operations
- Ensures indexes are properly created

### Manual Validation

Connect to PostgreSQL and verify:

```sql
-- Check tables
\dt

-- Check specific table structure
\d users
\d poker_hands

-- Verify foreign keys
SELECT * FROM information_schema.table_constraints 
WHERE constraint_type = 'FOREIGN KEY';

-- Check indexes
SELECT * FROM pg_indexes WHERE schemaname = 'public';
```

## Development Workflow

### Creating New Migrations

1. **Modify Models** - Update SQLAlchemy models in `app/models/`
2. **Generate Migration** - Run `python migrate.py create "Description"`
3. **Review Migration** - Check the generated migration file
4. **Test Migration** - Run on development database
5. **Validate** - Run validation script

### Best Practices

1. **Always Review** - Check generated migrations before applying
2. **Test Thoroughly** - Test both upgrade and downgrade paths
3. **Backup Data** - Always backup before running migrations in production
4. **Descriptive Names** - Use clear, descriptive migration messages
5. **Small Changes** - Keep migrations focused and atomic

### Common Issues

1. **Import Errors** - Ensure all models are imported in `env.py`
2. **Type Mismatches** - Verify PostgreSQL types match SQLAlchemy definitions
3. **Constraint Conflicts** - Check for naming conflicts in constraints
4. **Data Migration** - Use separate data migrations for complex transformations

## Production Deployment

### Pre-deployment Checklist

- [ ] Backup production database
- [ ] Test migration on staging environment
- [ ] Verify rollback procedures
- [ ] Check for breaking changes
- [ ] Coordinate with application deployment

### Deployment Steps

1. **Backup Database**
   ```bash
   pg_dump -h host -U user -d database > backup.sql
   ```

2. **Run Migration**
   ```bash
   python migrate.py upgrade
   ```

3. **Validate Results**
   ```bash
   python validate_migration.py
   ```

4. **Monitor Application**
   - Check application logs
   - Verify functionality
   - Monitor performance

### Rollback Procedures

If issues occur:

```bash
# Rollback to previous revision
python migrate.py downgrade -1

# Rollback to specific revision
python migrate.py downgrade abc123

# Restore from backup (if necessary)
psql -h host -U user -d database < backup.sql
```

## Troubleshooting

### Common Errors

1. **Connection Refused**
   - Check PostgreSQL is running
   - Verify connection parameters
   - Check firewall settings

2. **Permission Denied**
   - Verify database user permissions
   - Check schema ownership
   - Ensure CREATE privileges

3. **Migration Conflicts**
   - Check for multiple heads: `alembic heads`
   - Merge branches if necessary
   - Resolve conflicts manually

4. **Type Errors**
   - Verify PostgreSQL version compatibility
   - Check extension requirements (uuid-ossp)
   - Validate column type definitions

### Getting Help

1. Check Alembic documentation: https://alembic.sqlalchemy.org/
2. Review SQLAlchemy async documentation
3. Check PostgreSQL logs for detailed error messages
4. Use `alembic check` to validate current state

## Monitoring

### Health Checks

Regular monitoring should include:

- Migration status verification
- Database connection health
- Schema integrity checks
- Performance monitoring

### Automated Checks

Consider implementing:

- Pre-deployment migration validation
- Post-deployment health checks
- Automated rollback triggers
- Performance regression detection