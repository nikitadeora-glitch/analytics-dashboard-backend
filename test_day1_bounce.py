#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from sqlalchemy.orm import Session
from database import engine, get_db
from routers.pages import get_entry_pages
from datetime import datetime, timedelta

def test_day1_bounce_rate():
    print("🧪 Testing Day 1 Bounce Rate Calculation...")
    
    # Create database session
    db = next(get_db())
    
    try:
        project_id = 13
        
        # Get today's date in IST
        from datetime import datetime
        import pytz
        IST = pytz.timezone("Asia/Kolkata")
        now_ist = IST.localize(datetime.now())
        
        # Day 1 = today only
        start_date = now_ist.strftime("%Y-%m-%d")
        end_date = now_ist.strftime("%Y-%m-%d")
        
        print(f"\n📅 Testing Day 1 Data: {start_date} to {end_date}")
        
        print("\n📊 Testing Entry Pages Bounce Rate for Day 1:")
        entry_pages_result = get_entry_pages(
            project_id=project_id,
            limit=5,
            start_date=start_date,
            end_date=end_date,
            db=db
        )
        
        print(f"\n✅ Day 1 Entry Pages Result: {len(entry_pages_result['data'])} pages")
        for page in entry_pages_result['data']:
            print(f"  - {page['page']}: {page['sessions']} sessions, {page['bounce_rate']:.1f}% bounce rate")
        
        print("\n✅ Day 1 Bounce Rate Test Completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_day1_bounce_rate()
