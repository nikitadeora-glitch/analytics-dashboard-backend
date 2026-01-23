#!/usr/bin/env python3
"""
Quick test to check email sending in production
"""

import os
import asyncio
import sys
from dotenv import load_dotenv

# Load production environment
load_dotenv('.env.production')

# Add path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_utils import send_email_async

async def test_email():
    """Test email sending with production config"""
    print("🔍 Testing Email Configuration...")
    print("=" * 50)
    
    # Check environment
    print(f"MAIL_USERNAME: {os.getenv('MAIL_USERNAME')}")
    print(f"MAIL_PASSWORD: {'SET' if os.getenv('MAIL_PASSWORD') else 'NOT SET'}")
    print(f"MAIL_SERVER: {os.getenv('MAIL_SERVER')}")
    print(f"MAIL_PORT: {os.getenv('MAIL_PORT')}")
    
    if not os.getenv('MAIL_USERNAME') or not os.getenv('MAIL_PASSWORD'):
        print("❌ Email credentials not configured!")
        return False
    
    # Test email sending
    test_email = os.getenv('MAIL_USERNAME')  # Send to self
    print(f"\n📧 Sending test email to: {test_email}")
    
    try:
        result = await send_email_async(
            recipient=test_email,
            subject="🧪 Production Email Test",
            body="""
            <h2>Production Email Test</h2>
            <p>If you receive this email, the production email configuration is working!</p>
            <p>Time: {}</p>
            """.format(os.getenv('TIMESTAMP', 'Unknown'))
        )
        
        if result:
            print("✅ Email sent successfully!")
            return True
        else:
            print("❌ Email sending failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_email())
    print(f"\nResult: {'SUCCESS' if success else 'FAILED'}")
