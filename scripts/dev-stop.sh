#!/bin/bash

# Stop development environment

set -e

echo "🛑 Stopping Professional Poker Analyzer development environment..."

# Check if alternative ports configuration exists and is running
if docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.alt-ports.yml ps | grep -q "Up"; then
    echo "🔄 Stopping services with alternative ports..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.alt-ports.yml down
elif docker-compose -f docker-compose.yml -f docker-compose.dev.yml ps | grep -q "Up"; then
    echo "🔄 Stopping services with standard ports..."
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down
else
    echo "🔄 Stopping any running services..."
    docker-compose down 2>/dev/null || true
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml down 2>/dev/null || true
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.alt-ports.yml down 2>/dev/null || true
fi

echo ""
echo "✅ Development environment stopped!"