#!/usr/bin/env python3
"""
Test script for SendPlus email integration
Run this to test if email sending is working properly
"""

import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_sendplus_email():
    """Test SendPlus email sending"""
    
    # Get API key from environment
    api_key = os.getenv("SENDPLUS_API_KEY")
    if not api_key:
        print("❌ SENDPLUS_API_KEY not found in .env file")
        print("Please add your SendPlus API key to the .env file:")
        print("SENDPLUS_API_KEY=your_actual_api_key_here")
        return False
    
    # Test email configuration
    test_email = input("Enter test email address: ").strip()
    if not test_email:
        print("❌ No email address provided")
        return False
    
    # SendPlus API configuration
    sendplus_api_url = "https://api.sendplus.in/api/mail/send"
    
    # Test email content
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Test Email</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .header { background: linear-gradient(135deg, #0f0c29 0%, #302b63 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
            .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🧪 Test Email</h1>
            </div>
            <div class="content">
                <p>This is a test email from State Counter Analytics.</p>
                <p>If you received this email, the SendPlus integration is working correctly!</p>
                <p><strong>Timestamp:</strong> {timestamp}</p>
            </div>
        </div>
    </body>
    </html>
    """.format(timestamp=str(os.popen('date').read().strip()))
    
    # Email payload
    payload = {
        "apikey": api_key,
        "to": test_email,
        "from": os.getenv("FROM_EMAIL", "noreply@statecounter.com"),
        "fromname": "State Counter Analytics",
        "subject": "🧪 Test Email - SendPlus Integration",
        "html": html_content
    }
    
    try:
        print(f"📧 Sending test email to {test_email}...")
        response = requests.post(sendplus_api_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print(f"✅ Test email sent successfully!")
                print(f"📧 Check {test_email} for the test email")
                return True
            else:
                print(f"❌ SendPlus API error: {result.get('message', 'Unknown error')}")
                print(f"Full response: {result}")
                return False
        else:
            print(f"❌ HTTP error {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 SendPlus Email Integration Test")
    print("=" * 40)
    
    success = test_sendplus_email()
    
    if success:
        print("\n✅ Email test completed successfully!")
        print("Your SendPlus integration is working correctly.")
    else:
        print("\n❌ Email test failed!")
        print("Please check your SendPlus API key and configuration.")