# Professional Poker Analyzer Backend

FastAPI-based backend for the Professional Poker Analyzer platform.

## Features

- FastAPI with async/await support
- PostgreSQL database with SQLAlchemy 2.0
- Alembic migrations
- Redis caching
- Multi-platform poker hand parsing
- AI analysis integration (Gemini & Groq)
- Comprehensive statistics engine

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start the development server:
```bash
uvicorn app.main:app --reload
```

## Database Management

Use the database management script:

```bash
# Test database connection
python manage_db.py test

# Create all tables
python manage_db.py create

# Drop all tables (with confirmation)
python manage_db.py drop
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/v1/docs
- ReDoc: http://localhost:8000/api/v1/redoc