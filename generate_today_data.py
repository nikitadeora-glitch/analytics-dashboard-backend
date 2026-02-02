#!/usr/bin/env python3
"""
Generate test visitor data for today (Feb 2, 2026)
"""

import requests
import json
from datetime import datetime, timezone, timedelta
import random

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
PROJECT_ID = 13

def generate_test_visitor_data():
    """Generate test visitor data for today"""
    
    print("🧪 Generating test visitor data for today...")
    
    # Sample visitor data
    test_visitors = [
        {
            "visitor_id": f"test_visitor_{random.randint(1000, 9999)}",
            "ip_address": f"192.168.1.{random.randint(1, 255)}",
            "country": "India",
            "state": "Maharashtra",
            "city": "Mumbai",
            "isp": "Test ISP",
            "device": "Desktop",
            "browser": "Chrome",
            "os": "Windows",
            "screen_resolution": "1920x1080",
            "language": "en-US",
            "timezone": "Asia/Kolkata",
            "local_time": datetime.now(timezone.utc).isoformat(),
            "referrer": "direct",
            "entry_page": "https://hathistore.com/",
            "exit_page": "https://hathistore.com/products",
            "session_duration": random.randint(30, 300),
            "visited_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "visitor_id": f"test_visitor_{random.randint(1000, 9999)}",
            "ip_address": f"203.0.113.{random.randint(1, 255)}",
            "country": "United States",
            "state": "California",
            "city": "San Francisco",
            "isp": "Test ISP US",
            "device": "Mobile",
            "browser": "Safari",
            "os": "iOS",
            "screen_resolution": "375x667",
            "language": "en-US",
            "timezone": "America/Los_Angeles",
            "local_time": datetime.now(timezone.utc).isoformat(),
            "referrer": "https://google.com",
            "entry_page": "https://hathistore.com/products",
            "exit_page": "https://hathistore.com/checkout",
            "session_duration": random.randint(60, 400),
            "visited_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        },
        {
            "visitor_id": f"test_visitor_{random.randint(1000, 9999)}",
            "ip_address": f"198.51.100.{random.randint(1, 255)}",
            "country": "United Kingdom",
            "state": "England",
            "city": "London",
            "isp": "Test ISP UK",
            "device": "Desktop",
            "browser": "Firefox",
            "os": "Mac",
            "screen_resolution": "1440x900",
            "language": "en-GB",
            "timezone": "Europe/London",
            "local_time": datetime.now(timezone.utc).isoformat(),
            "referrer": "https://facebook.com",
            "entry_page": "https://hathistore.com/blog",
            "exit_page": "https://hathistore.com/contact",
            "session_duration": random.randint(45, 250),
            "visited_at": (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat()
        }
    ]
    
    # Insert test data via API (if there's an endpoint)
    for i, visitor in enumerate(test_visitors):
        print(f"\n📝 Creating test visitor {i+1}:")
        print(f"  Visitor ID: {visitor['visitor_id']}")
        print(f"  Country: {visitor['country']}")
        print(f"  Device: {visitor['device']}")
        print(f"  Visit Time: {visitor['visited_at']}")
        
        # Try to insert via analytics tracking endpoint
        try:
            response = requests.post(f"{BASE_URL}/api/analytics/{PROJECT_ID}/track", json=visitor)
            if response.status_code == 200:
                print(f"  ✅ Successfully inserted visitor {i+1}")
            else:
                print(f"  ❌ Failed to insert visitor {i+1}: {response.status_code}")
                print(f"     Response: {response.text}")
        except Exception as e:
            print(f"  ❌ Exception inserting visitor {i+1}: {e}")
    
    # Verify the data was inserted
    print("\n🔍 Verifying test data...")
    try:
        today = datetime.now(timezone.utc)
        start_date = today.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        end_date = today.replace(hour=23, minute=59, second=59, microsecond=999999).isoformat()
        
        response = requests.get(f"{BASE_URL}/api/visitors/{PROJECT_ID}/activity-view", params={
            'start_date': start_date,
            'end_date': end_date
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Found {len(data)} visitors for today!")
            if data:
                print("Sample visitors:")
                for i, visitor in enumerate(data[:3]):
                    print(f"  {i+1}. {visitor.get('visitor_id', 'N/A')} from {visitor.get('country', 'N/A')}")
            else:
                print("❌ No visitors found for today")
        else:
            print(f"❌ Error verifying data: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Exception verifying data: {e}")

if __name__ == "__main__":
    generate_test_visitor_data()
