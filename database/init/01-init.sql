-- Initialize PostgreSQL database for Professional Poker Analyzer
-- This script runs when the database container starts for the first time

-- Create database if it doesn't exist (handled by POSTGRES_DB env var)
-- CREATE DATABASE IF NOT EXISTS poker_analyzer;

-- Create extensions for UUID generation and advanced indexing
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search and similarity
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For advanced indexing
CREATE EXTENSION IF NOT EXISTS "pgcrypto"; -- For encryption functions

-- Set timezone to UTC for consistent timestamps
SET timezone = 'UTC';

-- Create initial schema placeholder
-- Actual tables will be created by Alembic migrations
-- This ensures proper dependency management and version control

-- Grant necessary permissions for the application user
-- (These will be handled by the POSTGRES_USER environment variable)