#!/bin/bash

# Start development environment

set -e

echo "🚀 Starting Professional Poker Analyzer development environment..."

# Start services
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

echo "⏳ Waiting for services to start..."
sleep 5

# Show service status
docker-compose ps

echo ""
echo "✅ Development environment is running!"
echo ""
echo "🌐 Services:"
echo "   Frontend: http://localhost:3000"
echo "   Backend: http://localhost:8000"
echo "   API Docs: http://localhost:8000/api/v1/docs"
echo ""
echo "📋 Useful commands:"
echo "   View logs: docker-compose logs -f [service]"
echo "   Stop services: docker-compose down"
echo "   Restart service: docker-compose restart [service]"
echo ""