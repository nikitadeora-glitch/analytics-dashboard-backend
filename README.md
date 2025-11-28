# Backend - State Counter Analytics

Python FastAPI backend for analytics platform.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn main:app --reload
```

## API Documentation

Visit http://127.0.0.1:8000/docs for interactive API documentation.

## Database

SQLite by default. To use PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/analytics_db
```

## Structure

- `main.py` - FastAPI application
- `database.py` - Database configuration
- `models.py` - SQLAlchemy models
- `schemas.py` - Pydantic schemas
- `utils.py` - Helper functions
- `routers/` - API endpoints
