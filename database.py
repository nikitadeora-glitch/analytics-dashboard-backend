from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("❌ DATABASE_URL is missing! Check your .env file.")

# Create engine with SQLite support and no timeout limits
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL, 
        connect_args={"check_same_thread": False},
        pool_size=20,           # Increase pool size
        max_overflow=30,        # Increase overflow
        pool_timeout=None,      # Remove timeout
        pool_recycle=3600,       # Recycle connections after 1 hour
        pool_pre_ping=True      # Verify connections before use
    )
else:
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,           # Increase pool size
        max_overflow=30,        # Increase overflow
        pool_timeout=None,      # Remove timeout
        pool_recycle=3600,       # Recycle connections after 1 hour
        pool_pre_ping=True      # Verify connections before use
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
