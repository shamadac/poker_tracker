#!/bin/bash

# Professional Poker Analyzer Development Setup Script

set -e

echo "🚀 Setting up Professional Poker Analyzer development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create environment files if they don't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file. Please update it with your configuration."
fi

if [ ! -f backend/.env ]; then
    echo "📝 Creating backend/.env file..."
    cp backend/.env.example backend/.env 2>/dev/null || echo "Backend .env already exists"
fi

if [ ! -f frontend/.env.local ]; then
    echo "📝 Creating frontend/.env.local file..."
    cp frontend/.env.example frontend/.env.local 2>/dev/null || echo "Frontend .env.local already exists"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p database/init
mkdir -p database/dev-data
mkdir -p shared
mkdir -p logs

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "🌐 Services available at:"
echo "   Frontend: http://localhost:3001"
echo "   Backend API: http://localhost:8001"
echo "   API Docs: http://localhost:8001/api/v1/docs"
echo "   PostgreSQL: localhost:5432"
echo "   Redis: localhost:6379"
echo ""
echo "📝 Next steps:"
echo "   1. Update .env files with your configuration"
echo "   2. Run database migrations: ./scripts/migrate.sh"
echo "   3. Start development: ./scripts/dev-start.sh"
echo ""