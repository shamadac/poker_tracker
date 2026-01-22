# Database Schema Analysis

## Overview

The Professional Poker Analyzer uses PostgreSQL with a comprehensive schema designed to handle poker hand histories, user management, analysis results, and educational content. The database uses UUID primary keys and includes proper indexing for performance.

## Core Tables

### 1. Users (`users`)
**Purpose**: User authentication and profile management

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| email | VARCHAR(255) | UNIQUE, NOT NULL | User email address |
| password_hash | VARCHAR(255) | NOT NULL | Hashed password |
| api_keys | JSONB | NOT NULL, DEFAULT {} | Encrypted API keys for AI providers |
| hand_history_paths | JSONB | NOT NULL, DEFAULT {} | Directory paths for hand history files |
| preferences | JSONB | NOT NULL, DEFAULT {} | User preferences and settings |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Account status |
| is_superuser | BOOLEAN | NOT NULL, DEFAULT false | Admin privileges |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: email

### 2. Poker Hands (`poker_hands`)
**Purpose**: Store comprehensive poker hand history data

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| user_id | UUID | FK(users.id), NOT NULL | Owner of the hand |
| hand_id | VARCHAR(50) | NOT NULL | Platform-specific hand ID |
| platform | VARCHAR(20) | NOT NULL | pokerstars, ggpoker |
| game_type | VARCHAR(100) | | Hold'em, Omaha, etc. |
| game_format | VARCHAR(50) | | tournament, cash, sng |
| stakes | VARCHAR(50) | | Stakes level |
| blinds | JSONB | | Blind structure |
| table_size | INTEGER | | Number of seats |
| date_played | TIMESTAMP | | When hand was played |
| player_cards | ARRAY[VARCHAR] | | Player's hole cards |
| board_cards | ARRAY[VARCHAR] | | Community cards |
| position | VARCHAR(20) | | UTG, MP, CO, BTN, SB, BB |
| seat_number | INTEGER | | Seat number at table |
| button_position | INTEGER | | Button seat number |
| actions | JSONB | | Detailed action sequence |
| result | VARCHAR(20) | | won, lost, folded |
| pot_size | DECIMAL(10,2) | | Total pot size |
| rake | DECIMAL(10,2) | | House rake |
| jackpot_contribution | DECIMAL(10,2) | | Jackpot contribution |
| tournament_info | JSONB | | Tournament details |
| cash_game_info | JSONB | | Cash game details |
| player_stacks | JSONB | | All player stack sizes |
| timebank_info | JSONB | | Time usage information |
| hand_duration | INTEGER | | Hand duration in seconds |
| timezone | VARCHAR(50) | | Timezone when played |
| currency | VARCHAR(10) | | Currency used |
| is_play_money | BOOLEAN | NOT NULL, DEFAULT false | Play money flag |
| raw_text | TEXT | | Original hand history text |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Unique Constraints**: (user_id, hand_id, platform)
**Indexes**: user_id, date_played, (user_id, platform, date_played), game_format, stakes, position

### 3. Analysis Results (`analysis_results`)
**Purpose**: Store AI-generated hand analysis

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| hand_id | UUID | FK(poker_hands.id), NOT NULL | Associated hand |
| ai_provider | VARCHAR(20) | NOT NULL | groq, gemini |
| prompt_version | VARCHAR(50) | | Version of analysis prompt |
| analysis_text | TEXT | | Full analysis text |
| strengths | ARRAY[VARCHAR] | | Identified strengths |
| mistakes | ARRAY[VARCHAR] | | Identified mistakes |
| recommendations | ARRAY[VARCHAR] | | Recommendations |
| confidence_score | DECIMAL(3,2) | | AI confidence (0-1) |
| analysis_metadata | JSONB | | Additional metadata |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: hand_id, (hand_id, ai_provider)

## Support Tables

### 4. Statistics Cache (`statistics_cache`)
**Purpose**: Cache computed statistics for performance

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| user_id | UUID | FK(users.id), NOT NULL | Cache owner |
| cache_key | VARCHAR(255) | NOT NULL | Unique cache identifier |
| stat_type | VARCHAR(50) | NOT NULL | Type of statistic |
| data | JSONB | NOT NULL | Cached data |
| expires_at | TIMESTAMP | NOT NULL | Expiration time |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Unique Constraints**: (user_id, cache_key)
**Indexes**: user_id, (user_id, stat_type), expires_at

### 5. File Monitoring (`file_monitoring`)
**Purpose**: Track hand history directory monitoring

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| user_id | UUID | FK(users.id), NOT NULL | Monitor owner |
| platform | VARCHAR(20) | NOT NULL | pokerstars, ggpoker |
| directory_path | TEXT | NOT NULL | Path being monitored |
| last_scan | TIMESTAMP | | Last scan time |
| file_count | INTEGER | NOT NULL, DEFAULT 0 | Files found in last scan |
| is_active | BOOLEAN | NOT NULL, DEFAULT true | Monitoring status |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: user_id, (user_id, platform), is_active

### 6. File Processing Tasks (`file_processing_tasks`)
**Purpose**: Track background file processing

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| user_id | UUID | FK(users.id), NOT NULL | Task owner |
| task_name | VARCHAR(100) | NOT NULL | Human-readable name |
| task_type | VARCHAR(50) | NOT NULL | file_parse, batch_import |
| file_path | TEXT | | File being processed |
| file_size | INTEGER | | File size in bytes |
| platform | VARCHAR(20) | | pokerstars, ggpoker |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'pending' | pending, processing, completed, failed, cancelled |
| progress_percentage | INTEGER | NOT NULL, DEFAULT 0 | Progress (0-100) |
| current_step | VARCHAR(200) | | Current step description |
| started_at | TIMESTAMP | | Processing start time |
| completed_at | TIMESTAMP | | Processing completion time |
| estimated_completion | TIMESTAMP | | Estimated completion |
| hands_processed | INTEGER | NOT NULL, DEFAULT 0 | Successfully processed hands |
| hands_failed | INTEGER | NOT NULL, DEFAULT 0 | Failed hands |
| total_hands_expected | INTEGER | | Expected total hands |
| error_message | TEXT | | Error message |
| error_details | JSONB | | Detailed error info |
| processing_options | JSONB | | Processing configuration |
| result_summary | JSONB | | Processing results |
| processing_time_seconds | DECIMAL(10,3) | | Total processing time |
| hands_per_second | DECIMAL(10,3) | | Processing rate |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: user_id, (user_id, status), task_type, created_at

## RBAC System

### 7. Roles (`roles`)
**Purpose**: Define user roles

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| name | VARCHAR(50) | UNIQUE, NOT NULL | Role name |
| description | VARCHAR(255) | | Role description |
| is_system_role | BOOLEAN | NOT NULL, DEFAULT false | System-defined role |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Default Roles**: user, admin, superuser

### 8. Permissions (`permissions`)
**Purpose**: Define system permissions

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| name | VARCHAR(100) | UNIQUE, NOT NULL | Permission name |
| resource | VARCHAR(50) | NOT NULL | Resource type |
| action | VARCHAR(50) | NOT NULL | Action type |
| description | VARCHAR(255) | | Permission description |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Unique Constraints**: (resource, action)

### 9. Role Permissions (`role_permissions`)
**Purpose**: Many-to-many role-permission mapping

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| role_id | UUID | FK(roles.id), PK | Role reference |
| permission_id | UUID | FK(permissions.id), PK | Permission reference |
| created_at | TIMESTAMP | NOT NULL | Assignment timestamp |

### 10. User Roles (`user_roles`)
**Purpose**: Many-to-many user-role mapping with metadata

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | UUID | FK(users.id), PK | User reference |
| role_id | UUID | FK(roles.id), PK | Role reference |
| assigned_by | UUID | FK(users.id) | Who assigned the role |
| assigned_at | TIMESTAMP | NOT NULL | Assignment timestamp |
| expires_at | TIMESTAMP | | Role expiration (optional) |

## Education System

### 11. Education Content (`education_content`)
**Purpose**: Store educational poker content

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| title | VARCHAR(255) | NOT NULL | Content title |
| slug | VARCHAR(255) | UNIQUE, NOT NULL | URL-friendly identifier |
| category | ENUM | NOT NULL | basic, advanced, tournament, cash_game |
| difficulty | ENUM | NOT NULL | beginner, intermediate, advanced |
| definition | TEXT | NOT NULL | Term definition |
| explanation | TEXT | NOT NULL | Detailed explanation |
| examples | ARRAY[TEXT] | NOT NULL, DEFAULT {} | Usage examples |
| related_stats | ARRAY[VARCHAR] | NOT NULL, DEFAULT {} | Related statistics |
| video_url | VARCHAR(500) | | Educational video URL |
| interactive_demo | BOOLEAN | DEFAULT false | Has interactive demo |
| tags | ARRAY[VARCHAR] | NOT NULL, DEFAULT {} | Content tags |
| prerequisites | ARRAY[VARCHAR] | NOT NULL, DEFAULT {} | Required knowledge |
| learning_objectives | ARRAY[TEXT] | NOT NULL, DEFAULT {} | Learning goals |
| author | VARCHAR(255) | | Content author |
| version | VARCHAR(50) | DEFAULT '1.0' | Content version |
| is_published | BOOLEAN | DEFAULT true | Publication status |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: title, slug, category, difficulty, is_published

### 12. Education Progress (`education_progress`)
**Purpose**: Track user progress through educational content

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PK | Primary key |
| user_id | UUID | FK(users.id), NOT NULL | User reference |
| content_id | UUID | FK(education_content.id), NOT NULL | Content reference |
| is_read | BOOLEAN | DEFAULT false | Content read status |
| is_bookmarked | BOOLEAN | DEFAULT false | Bookmark status |
| is_favorite | BOOLEAN | DEFAULT false | Favorite status |
| time_spent_seconds | INTEGER | DEFAULT 0 | Time spent reading |
| last_accessed | TIMESTAMP | | Last access time |
| user_notes | TEXT | | User's personal notes |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**: user_id, content_id, (user_id, content_id), (user_id, is_bookmarked), (user_id, is_favorite)

## Key Relationships

1. **Users → Poker Hands**: One-to-many (user owns multiple hands)
2. **Poker Hands → Analysis Results**: One-to-many (hand can have multiple analyses)
3. **Users → Statistics Cache**: One-to-many (user has multiple cached stats)
4. **Users → File Monitoring**: One-to-many (user monitors multiple directories)
5. **Users → File Processing Tasks**: One-to-many (user has multiple processing tasks)
6. **Users ↔ Roles**: Many-to-many through user_roles
7. **Roles ↔ Permissions**: Many-to-many through role_permissions
8. **Users → Education Progress**: One-to-many (user progress on multiple content items)
9. **Education Content → Education Progress**: One-to-many (content tracked by multiple users)

## Data Integrity Features

- **Cascading Deletes**: User deletion removes all associated data
- **Unique Constraints**: Prevent duplicate hands per user/platform
- **Foreign Key Constraints**: Maintain referential integrity
- **Check Constraints**: Ensure valid enum values and ranges
- **Indexes**: Optimized for common query patterns

## Performance Considerations

- **UUID Primary Keys**: Better for distributed systems, avoid sequential hotspots
- **JSONB Columns**: Flexible schema for complex data with indexing support
- **Strategic Indexing**: Composite indexes for common query patterns
- **Statistics Caching**: Pre-computed statistics for dashboard performance
- **Partitioning Potential**: poker_hands table could be partitioned by date_played for large datasets

## Missing Tables for Requirements

Based on the requirements analysis, we may need to add:

1. **Encyclopedia Entries**: For the new encyclopedia system (separate from education_content)
2. **Encyclopedia Links**: For managing inter-entry hyperlinks
3. **AI Conversations**: For tracking encyclopedia content generation conversations
4. **File Upload History**: For tracking uploaded files and preventing duplicates
5. **User Sessions**: For tracking user activity and "today's" statistics

## Recommendations

1. **Add file upload tracking** to prevent duplicate imports
2. **Enhance statistics caching** with more granular cache keys
3. **Add audit logging** for important data changes
4. **Consider partitioning** poker_hands table by date for performance
5. **Add full-text search** indexes for educational content
6. **Implement soft deletes** for important data recovery