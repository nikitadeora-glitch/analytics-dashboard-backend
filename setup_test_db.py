#!/usr/bin/env python3
"""
Setup script to create database tables for testing
"""
import os
import sys
from database import engine, Base
from models import *  # Import all models to ensure they're registered with Base

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False

if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)
