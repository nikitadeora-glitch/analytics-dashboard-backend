#!/usr/bin/env python3
"""
Test script to verify date filtering works in VisitorPath
"""

import requests
import json
from datetime import datetime, timezone, timedelta

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
PROJECT_ID = 13  # Use your test project ID

def test_date_filtering():
    """Test date filtering with different ranges"""
    
    print("Testing VisitorPath date filtering...")
    
    # Test 1: 1 day filter
    print("\nTest 1: 1 Day Filter")
    today = datetime.now(timezone.utc)
    start_date_1day = today.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    end_date_1day = today.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
    
    url_1day = f"{BASE_URL}/api/visitors/{PROJECT_ID}/activity-view"
    params_1day = {
        "start_date": start_date_1day,
        "end_date": end_date_1day
    }
    
    try:
        response = requests.get(url_1day, params=params_1day)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Visitors found: {len(data)}")
            if data:
                print(f"  Sample visitor: {data[0]['visitor_id']}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"  Exception: {e}")
    
    # Test 2: 7 days filter
    print("\nTest 2: 7 Days Filter")
    start_date_7days = (today.replace(hour=0, minute=0, second=0, microsecond=0) - 
                       timedelta(days=6)).isoformat()
    
    url_7days = f"{BASE_URL}/api/visitors/{PROJECT_ID}/activity-view"
    params_7days = {
        "start_date": start_date_7days,
        "end_date": end_date_1day
    }
    
    try:
        response = requests.get(url_7days, params=params_7days)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Visitors found: {len(data)}")
            if data:
                print(f"  Sample visitor: {data[0]['visitor_id']}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"  Exception: {e}")
    
    # Test 3: No filter (should return more data)
    print("\nTest 3: No Date Filter")
    url_no_filter = f"{BASE_URL}/api/visitors/{PROJECT_ID}/activity-view"
    
    try:
        response = requests.get(url_no_filter)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  Visitors found: {len(data)}")
            if data:
                print(f"  Sample visitor: {data[0]['visitor_id']}")
        else:
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"  Exception: {e}")

if __name__ == "__main__":
    test_date_filtering()
