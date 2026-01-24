# Professional Poker Analyzer

A modern, enterprise-grade poker analysis platform built with Next.js, FastAPI, PostgreSQL, and Redis. Provides comprehensive poker hand analysis, statistics tracking, and AI-powered coaching through Gemini and Groq providers.

## 🚀 Quick Start

### Prerequisites

- Docker Desktop
- Docker Compose
- Git

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd professional-poker-analyzer
   ```

2. **Run setup script**
   ```bash
   # Linux/macOS
   ./scripts/dev-setup.sh
   
   # Windows
   scripts\dev-setup.bat
   ```

3. **Access the application**
   - Frontend: http://localhost:3001
   - Backend API: http://localhost:8001
   - API Documentation: http://localhost:8001/api/v1/docs

## 🏗️ Architecture

### Monorepo Structure
```
├── frontend/          # Next.js 14 + TypeScript frontend
├── backend/           # FastAPI + Python backend
├── database/          # PostgreSQL initialization scripts
├── scripts/           # Development and deployment scripts
├── shared/            # Shared types and utilities
└── docker-compose.yml # Container orchestration
```

### Technology Stack

**Frontend:**
- Next.js 14 with App Router
- TypeScript
- Tailwind CSS + Shadcn/ui
- React Query for state management
- Recharts for data visualization

**Backend:**
- FastAPI with async/await
- SQLAlchemy 2.0 + Alembic
- Pydantic for validation
- Structured logging with structlog
- Redis for caching

**Infrastructure:**
- PostgreSQL 15 database
- Redis 7 cache
- Docker containers
- Docker Compose orchestration

## 🛠️ Development

### Starting Development Environment

```bash
# Start all services
./scripts/dev-start.sh

# View logs
docker-compose logs -f [service-name]

# Stop services
./scripts/dev-stop.sh
```

### Database Management

```bash
# Run migrations
./scripts/migrate.sh

# Access PostgreSQL
docker-compose exec postgres psql -U postgres -d poker_analyzer

# Access Redis
docker-compose exec redis redis-cli
```

### Environment Configuration

Copy `.env.example` to `.env` and update the values:

```env
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/poker_analyzer

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-here

# API
BACKEND_CORS_ORIGINS=["http://localhost:3001"]
```

## 📊 Features

### Core Features
- **Multi-Platform Support**: PokerStars and GGPoker hand history parsing
- **AI Analysis**: Gemini and Groq integration with user-provided API keys
- **Advanced Statistics**: Comprehensive poker metrics and visualizations
- **Real-time Monitoring**: Automatic hand history file detection
- **Responsive Design**: Works on desktop, tablet, and mobile

### Security Features
- OAuth 2.0 with PKCE authentication
- JWT token management
- AES-256 encryption for sensitive data
- Rate limiting and CSRF protection
- Role-based access control

### Performance Features
- Redis caching for statistics and analysis
- Database query optimization
- Asynchronous processing
- Connection pooling
- Performance monitoring

## 🧪 Testing

### Running Tests

```bash
# Backend tests
docker-compose exec backend pytest

# Frontend tests
docker-compose exec frontend npm test

# Property-based tests
docker-compose exec backend pytest -m property
```

### Test Coverage
- Unit tests for core functionality
- Property-based tests for universal properties
- Integration tests for API endpoints
- End-to-end tests for critical user journeys

## 📝 API Documentation

The API documentation is automatically generated and available at:
- Development: http://localhost:8001/api/v1/docs
- Interactive docs: http://localhost:8001/api/v1/redoc

### Key Endpoints
- `GET /health` - Health check
- `POST /api/v1/auth/login` - User authentication
- `POST /api/v1/hands/upload` - Upload hand histories
- `GET /api/v1/stats/user/{user_id}` - Get user statistics
- `POST /api/v1/analysis/hand` - Analyze single hand

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `SECRET_KEY` | JWT signing key | Required |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |

### AI Provider Configuration
Users configure their own API keys through the web interface:
- Gemini API key for deep analysis
- Groq API key for fast analysis

## 🚀 Deployment

### Production Deployment

1. **Update environment variables**
   ```bash
   cp .env.example .env.production
   # Update with production values
   ```

2. **Build and deploy**
   ```bash
   docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
   ```

3. **Run migrations**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

### Health Checks
- Backend: `GET /health`
- Database: PostgreSQL health check
- Cache: Redis ping

## 📚 Documentation

- [API Documentation](http://localhost:8001/api/v1/docs)
- [Architecture Guide](docs/architecture.md)
- [Development Guide](docs/development.md)
- [Deployment Guide](docs/deployment.md)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation
- Review the API docs at `/api/v1/docs`