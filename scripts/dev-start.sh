#!/bin/bash

# Start development environment

set -e

echo "🚀 Starting Professional Poker Analyzer development environment..."

# Check if alternative ports should be used
if [ "$1" = "--alt-ports" ]; then
    echo "🔄 Using alternative ports to avoid conflicts..."
    # Start services with alternative ports
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.alt-ports.yml up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 5

    # Show service status
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.alt-ports.yml ps

    echo ""
    echo "✅ Development environment is running with alternative ports!"
    echo ""
    echo "🌐 Services:"
    echo "   Frontend: http://localhost:3001"
    echo "   Backend: http://localhost:8001"
    echo "   API Docs: http://localhost:8001/api/v1/docs"
    echo "   PostgreSQL: localhost:5433"
    echo "   Redis: localhost:6380"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs: docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.alt-ports.yml logs -f [service]"
    echo "   Stop services: docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.alt-ports.yml down"
    echo "   Restart service: docker-compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.alt-ports.yml restart [service]"
else
    # Start services with standard ports
    docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
    
    echo "⏳ Waiting for services to start..."
    sleep 5

    # Show service status
    docker-compose ps

    echo ""
    echo "✅ Development environment is running!"
    echo ""
    echo "🌐 Services:"
    echo "   Frontend: http://localhost:3001"
    echo "   Backend: http://localhost:8001"
    echo "   API Docs: http://localhost:8001/api/v1/docs"
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs: docker-compose logs -f [service]"
    echo "   Stop services: docker-compose down"
    echo "   Restart service: docker-compose restart [service]"
fi
echo ""