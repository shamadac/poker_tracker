@echo off
REM Professional Poker Analyzer Development Setup Script for Windows

echo 🚀 Setting up Professional Poker Analyzer development environment...

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    pause
    exit /b 1
)

REM Create environment files if they don't exist
if not exist .env (
    echo 📝 Creating .env file from template...
    copy .env.example .env
    echo ✅ Created .env file. Please update it with your configuration.
)

if not exist backend\.env (
    echo 📝 Creating backend\.env file...
    if exist backend\.env.example copy backend\.env.example backend\.env
)

if not exist frontend\.env.local (
    echo 📝 Creating frontend\.env.local file...
    if exist frontend\.env.example copy frontend\.env.example frontend\.env.local
)

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist database\init mkdir database\init
if not exist database\dev-data mkdir database\dev-data
if not exist shared mkdir shared
if not exist logs mkdir logs

REM Build and start services
echo 🐳 Building and starting Docker services...
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d

REM Wait for services to be healthy
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check service health
echo 🔍 Checking service health...
docker-compose ps

echo.
echo ✅ Development environment setup complete!
echo.
echo 🌐 Services available at:
echo    Frontend: http://localhost:3001
echo    Backend API: http://localhost:8001
echo    API Docs: http://localhost:8001/api/v1/docs
echo    PostgreSQL: localhost:5432
echo    Redis: localhost:6379
echo.
echo 📝 Next steps:
echo    1. Update .env files with your configuration
echo    2. Run database migrations: scripts\migrate.bat
echo    3. Start development: scripts\dev-start.bat
echo.
pause