#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from sqlalchemy.orm import Session
from database import engine, get_db
from routers.pages import get_entry_pages, get_most_visited_pages, get_exit_pages
from datetime import datetime

def test_bounce_rate():
    print("🧪 Testing Bounce Rate Calculation...")
    
    # Create database session
    db = next(get_db())
    
    try:
        project_id = 13
        
        print("\n📊 Testing Most Visited Pages Bounce Rate:")
        most_visited_result = get_most_visited_pages(
            project_id=project_id,
            limit=2,
            start_date=None,
            end_date=None,
            db=db
        )
        
        print("\n📊 Testing Entry Pages Bounce Rate:")
        entry_pages_result = get_entry_pages(
            project_id=project_id,
            limit=2,
            start_date=None,
            end_date=None,
            db=db
        )
        
        print("\n📊 Testing Exit Pages Bounce Rate:")
        exit_pages_result = get_exit_pages(
            project_id=project_id,
            limit=2,
            start_date=None,
            end_date=None,
            db=db
        )
        
        print("\n✅ Bounce Rate Test Completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_bounce_rate()
