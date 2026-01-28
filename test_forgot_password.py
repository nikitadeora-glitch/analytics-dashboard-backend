#!/usr/bin/env python3
"""
Test forgot password functionality
"""

import asyncio
import requests
import json
import pytest
@pytest.mark.asyncio   # Only use asyncio for FastAPI
async def test_forgot_password():
    """Test the forgot password endpoint"""
    
    print("🧪 Testing Forgot Password Endpoint")
    print("=" * 50)
    
    # Test with a real email address (replace with actual test email)
    test_email = "team@prpwebs.com"  # Using your verified sender email
    
    print(f"📧 Testing with email: {test_email}")
    
    try:
        # Test the forgot password endpoint
        response = requests.post(
            "http://localhost:8000/api/auth/forgot-password",
            json={"email": test_email},
            headers={"Content-Type": "application/json"}
        )
        
        print(f"📊 Status Code: {response.status_code}")
        print(f"📄 Response: {response.json()}")
        
        if response.status_code == 200:
            print("✅ Forgot password endpoint working!")
        else:
            print("❌ Forgot password endpoint failed!")
            
    except Exception as e:
        print(f"❌ Error testing forgot password: {e}")
    
    # Also test direct email sending
    print(f"\n📧 Testing direct email to: {test_email}")
    
    from sendgrid_email import send_notification_email
    
    try:
        result = await send_notification_email(
            recipient_email=test_email,
            notification_title="Direct Email Test",
            notification_message="This is a direct test of the SendGrid email system."
        )
        
        if result:
            print("✅ Direct email test successful!")
        else:
            print("❌ Direct email test failed!")
            
    except Exception as e:
        print(f"❌ Direct email test error: {e}")

if __name__ == "__main__":
    asyncio.run(test_forgot_password())
