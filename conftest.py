"""
pytest configuration and fixtures
"""
import pytest
import os
from database import engine, Base
from models import *  # Import all models

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create database tables before running tests"""
    # Set test environment
    os.environ["ENVIRONMENT"] = "test"
    
    print("\n=== Setting up test database ===")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise
    
    yield
    
    # Clean up environment
    os.environ.pop("ENVIRONMENT", None)
