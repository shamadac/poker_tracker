#!/bin/bash

# Stop development environment

set -e

echo "🛑 Stopping Professional Poker Analyzer development environment..."

# Stop services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml down

echo "✅ Development environment stopped."