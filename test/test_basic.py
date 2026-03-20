import pytest


@pytest.mark.asyncio
async def test_sample():
    """Sample test to verify pytest configuration"""
    assert True


@pytest.mark.asyncio
async def test_database_connection():
    """Test that database connection works"""
    from database import engine, SessionLocal
    from sqlalchemy import text
    
    # Test synchronous database connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1
    
    # Test session creation
    db = SessionLocal()
    try:
        result = db.execute(text("SELECT 1"))
        assert result.fetchone()[0] == 1
    finally:
        db.close()
