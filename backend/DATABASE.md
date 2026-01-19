# Database Schema Documentation

## Overview

The Professional Poker Analyzer uses PostgreSQL as the primary database with comprehensive schema design to support multi-platform poker hand analysis, AI-powered insights, and advanced statistics tracking.

## Database Architecture

### Core Tables

#### 1. Users Table
Stores user accounts, encrypted API keys, and preferences.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    api_keys JSONB DEFAULT '{}', -- Encrypted API keys for AI providers
    hand_history_paths JSONB DEFAULT '{}', -- Platform-specific directory paths
    preferences JSONB DEFAULT '{}', -- User settings and preferences
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### 2. Poker Hands Table
Comprehensive storage for poker hand data from multiple platforms.

```sql
CREATE TABLE poker_hands (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    hand_id VARCHAR(50) NOT NULL, -- Platform-specific hand ID
    platform VARCHAR(20) NOT NULL, -- 'pokerstars' or 'ggpoker'
    game_type VARCHAR(100), -- Hold'em, Omaha, etc.
    game_format VARCHAR(50), -- tournament, cash, sng
    stakes VARCHAR(50), -- $0.50/$1.00, etc.
    blinds JSONB, -- {small: 0.5, big: 1.0, ante: 0.1}
    table_size INTEGER, -- Number of seats
    date_played TIMESTAMP,
    player_cards TEXT[], -- Player's hole cards
    board_cards TEXT[], -- Community cards
    position VARCHAR(20), -- UTG, MP, CO, BTN, SB, BB
    seat_number INTEGER,
    button_position INTEGER,
    actions JSONB, -- Detailed action sequence
    result VARCHAR(20), -- won, lost, folded
    pot_size DECIMAL(10,2),
    rake DECIMAL(10,2),
    jackpot_contribution DECIMAL(10,2),
    tournament_info JSONB, -- Tournament-specific data
    cash_game_info JSONB, -- Cash game-specific data
    player_stacks JSONB, -- All player stack information
    timebank_info JSONB, -- Time usage data
    hand_duration INTEGER, -- Duration in seconds
    timezone VARCHAR(50),
    currency VARCHAR(10),
    is_play_money BOOLEAN DEFAULT false,
    raw_text TEXT, -- Original hand history text
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, hand_id, platform)
);
```

#### 3. Analysis Results Table
Stores AI-generated analysis for poker hands.

```sql
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hand_id UUID REFERENCES poker_hands(id) ON DELETE CASCADE,
    ai_provider VARCHAR(20), -- 'gemini' or 'groq'
    prompt_version VARCHAR(50), -- Track prompt template versions
    analysis_text TEXT, -- Full analysis from AI
    strengths TEXT[], -- Identified strengths
    mistakes TEXT[], -- Identified mistakes
    recommendations TEXT[], -- Improvement suggestions
    confidence_score DECIMAL(3,2), -- AI confidence (0.00-1.00)
    analysis_metadata JSONB, -- Additional analysis data
    created_at TIMESTAMP DEFAULT NOW()
);
```

#### 4. Statistics Cache Table
Caches computed poker statistics for performance.

```sql
CREATE TABLE statistics_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    cache_key VARCHAR(255), -- Unique key based on filters
    stat_type VARCHAR(50), -- basic, advanced, tournament, etc.
    data JSONB, -- Cached statistics data
    expires_at TIMESTAMP, -- Cache expiration time
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, cache_key)
);
```

#### 5. File Monitoring Table
Tracks hand history directory monitoring status.

```sql
CREATE TABLE file_monitoring (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(20), -- 'pokerstars' or 'ggpoker'
    directory_path TEXT, -- Path being monitored
    last_scan TIMESTAMP, -- Last scan time
    file_count INTEGER DEFAULT 0, -- Files found in last scan
    is_active BOOLEAN DEFAULT true, -- Monitoring status
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Indexes and Performance

### Primary Indexes
- All tables have UUID primary keys with proper indexing
- Foreign key relationships are indexed for join performance
- Unique constraints prevent data duplication

### Performance Indexes
```sql
-- Poker hands performance indexes
CREATE INDEX idx_poker_hands_user_platform_date ON poker_hands(user_id, platform, date_played DESC);
CREATE INDEX idx_poker_hands_game_format ON poker_hands(game_format);
CREATE INDEX idx_poker_hands_stakes ON poker_hands(stakes);
CREATE INDEX idx_poker_hands_position ON poker_hands(position);

-- Analysis results indexes
CREATE INDEX idx_analysis_results_hand_provider ON analysis_results(hand_id, ai_provider);

-- Statistics cache indexes
CREATE INDEX idx_statistics_cache_user_type ON statistics_cache(user_id, stat_type);
CREATE INDEX idx_statistics_cache_expires ON statistics_cache(expires_at);

-- File monitoring indexes
CREATE INDEX idx_file_monitoring_user_platform ON file_monitoring(user_id, platform);
CREATE INDEX idx_file_monitoring_active ON file_monitoring(is_active);
```

## Data Types and Constraints

### JSONB Usage
The schema extensively uses PostgreSQL's JSONB type for flexible data storage:
- **api_keys**: Encrypted API credentials for different providers
- **hand_history_paths**: Platform-specific directory configurations
- **preferences**: User settings and UI preferences
- **blinds**: Flexible blind structure storage
- **actions**: Complex action sequences with timing data
- **tournament_info**: Tournament-specific metadata
- **player_stacks**: Complete table state information
- **analysis_metadata**: AI analysis additional data

### Array Types
PostgreSQL arrays are used for:
- **player_cards**: Hole cards (e.g., ['As', 'Kh'])
- **board_cards**: Community cards (e.g., ['Ac', '7s', '2d'])
- **strengths**: AI-identified strengths
- **mistakes**: AI-identified mistakes
- **recommendations**: AI improvement suggestions

### Decimal Precision
Financial data uses DECIMAL types for accuracy:
- **pot_size**: DECIMAL(10,2) for precise pot amounts
- **rake**: DECIMAL(10,2) for house rake
- **confidence_score**: DECIMAL(3,2) for AI confidence (0.00-1.00)

## Security Considerations

### Data Encryption
- API keys are encrypted at rest using AES-256
- Password hashes use bcrypt with proper salting
- Sensitive user data is protected with appropriate access controls

### Access Control
- Row-level security through user_id foreign keys
- Cascade deletes ensure data consistency
- Proper indexing prevents unauthorized data access

## Migration Management

### Alembic Integration
The schema is managed through Alembic migrations:
- Version-controlled schema changes
- Automatic migration generation
- Rollback capabilities for safe deployments

### Migration Commands
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Performance Considerations

### Query Optimization
- Composite indexes for common query patterns
- JSONB GIN indexes for flexible queries
- Proper foreign key indexing for joins

### Caching Strategy
- Statistics cache with TTL for expensive calculations
- Redis integration for session and temporary data
- Intelligent cache invalidation on data updates

### Scalability Features
- UUID primary keys for distributed systems
- Partitioning-ready design for large datasets
- Efficient indexing for multi-tenant architecture

## Data Integrity

### Constraints
- Foreign key constraints with CASCADE deletes
- Unique constraints for business logic enforcement
- Check constraints for data validation

### Validation
- Application-level validation through Pydantic models
- Database-level constraints for data integrity
- Comprehensive error handling for constraint violations

## Backup and Recovery

### Backup Strategy
- Regular automated backups of all user data
- Point-in-time recovery capabilities
- Encrypted backup storage for security

### Data Retention
- Configurable data retention policies
- Secure data deletion for account removal
- Audit trails for compliance requirements