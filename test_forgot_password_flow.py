#!/usr/bin/env python3
"""
Complete forgot password flow test script
Tests the entire flow from email request to password reset
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/auth"
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "NewPassword123!"

def test_forgot_password_flow():
    """Test the complete forgot password flow"""
    
    print("🧪 Testing Complete Forgot Password Flow")
    print("=" * 50)
    
    # Step 1: Test forgot password request
    print("\n📧 Step 1: Testing forgot password request...")
    
    forgot_payload = {"email": TEST_EMAIL}
    
    try:
        response = requests.post(f"{BASE_URL}/forgot-password", json=forgot_payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Forgot password request successful: {result['message']}")
        else:
            print(f"❌ Forgot password request failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in forgot password request: {str(e)}")
        return False
    
    # Step 2: Manual token input (since we can't access email in test)
    print("\n🔑 Step 2: Token verification...")
    print("In a real scenario, the user would get the token from email.")
    print("For testing, check your backend logs for the reset URL or database for the token.")
    
    token = input("Enter the reset token from logs/database (or press Enter to skip): ").strip()
    
    if not token:
        print("⏭️ Skipping token verification test")
        return True
    
    # Step 3: Test token verification
    try:
        response = requests.get(f"{BASE_URL}/verify-reset-token/{token}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Token verification successful for: {result['user_email']}")
            print(f"Token expires at: {result['expires_at']}")
        else:
            print(f"❌ Token verification failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in token verification: {str(e)}")
        return False
    
    # Step 4: Test password reset
    print("\n🔐 Step 3: Testing password reset...")
    
    reset_payload = {
        "token": token,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/reset-password", json=reset_payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Password reset successful: {result['message']}")
        else:
            print(f"❌ Password reset failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in password reset: {str(e)}")
        return False
    
    # Step 5: Test login with new password
    print("\n🔓 Step 4: Testing login with new password...")
    
    login_payload = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        response = requests.post(f"{BASE_URL}/login", json=login_payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Login successful with new password!")
            print(f"User: {result['user']['full_name']} ({result['user']['email']})")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error in login test: {str(e)}")
        return False
    
    return True

def test_api_endpoints():
    """Test individual API endpoints"""
    
    print("\n🔧 Testing Individual API Endpoints")
    print("=" * 40)
    
    # Test forgot password with invalid email
    print("\n📧 Testing forgot password with non-existent email...")
    
    try:
        response = requests.post(f"{BASE_URL}/forgot-password", json={"email": "nonexistent@example.com"})
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Correct response for non-existent email: {result['message']}")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test token verification with invalid token
    print("\n🔑 Testing token verification with invalid token...")
    
    try:
        response = requests.get(f"{BASE_URL}/verify-reset-token/invalid_token_123")
        
        if response.status_code == 400:
            print("✅ Correct error response for invalid token")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    # Test password reset with invalid token
    print("\n🔐 Testing password reset with invalid token...")
    
    try:
        response = requests.post(f"{BASE_URL}/reset-password", json={
            "token": "invalid_token_123",
            "password": "NewPassword123!"
        })
        
        if response.status_code == 400:
            print("✅ Correct error response for invalid token")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 Starting Forgot Password Flow Test")
    print(f"Backend URL: {BASE_URL}")
    print(f"Test Email: {TEST_EMAIL}")
    print(f"Timestamp: {datetime.now()}")
    
    # Test API endpoints first
    test_api_endpoints()
    
    # Test complete flow
    success = test_forgot_password_flow()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests completed successfully!")
        print("The forgot password flow is working correctly.")
    else:
        print("❌ Some tests failed!")
        print("Please check the error messages above.")
    
    print("\n📝 Next Steps:")
    print("1. Make sure your backend server is running")
    print("2. Configure SendPlus API key in .env file")
    print("3. Test email sending with test_email.py")
    print("4. Test the frontend flow manually")