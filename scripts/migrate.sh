#!/bin/bash

# Run database migrations

set -e

echo "🗄️ Running database migrations..."

# Run migrations in the backend container
docker-compose exec backend alembic upgrade head

echo "✅ Database migrations completed."