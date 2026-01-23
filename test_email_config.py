#!/usr/bin/env python3
"""
Email Configuration Debug Script
Run this script to test email sending configuration
"""

import os
import asyncio
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_utils import send_email_async

def test_environment():
    """Test if environment variables are loaded correctly"""
    print("🔍 Testing Environment Configuration...")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check which .env file is being used
    env_files = ['.env', '.env.local', '.env.production']
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"📄 Found: {env_file}")
    
    print("\n📧 Email Configuration:")
    email_vars = [
        'MAIL_USERNAME',
        'MAIL_PASSWORD', 
        'MAIL_SERVER',
        'MAIL_PORT',
        'FRONTEND_URL'
    ]
    
    for var in email_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                print(f"✅ {var}: {'*' * len(value)}")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: NOT SET")
    
    print("\n🌍 All Environment Variables (containing 'MAIL'):")
    mail_env_vars = {k: v for k, v in os.environ.items() if 'MAIL' in k.upper()}
    for k, v in mail_env_vars.items():
        if 'PASSWORD' in k:
            print(f"  {k}: {'*' * len(v) if v else 'NOT SET'}")
        else:
            print(f"  {k}: {v or 'NOT SET'}")

async def test_email_sending():
    """Test actual email sending"""
    print("\n📧 Testing Email Sending...")
    print("=" * 50)
    
    # Get test email from command line or use default
    test_email = input("Enter test email address (or press Enter to use configured email): ").strip()
    if not test_email:
        test_email = os.getenv('MAIL_USERNAME')
        if not test_email:
            print("❌ No test email provided and MAIL_USERNAME not set")
            return False
    
    print(f"📧 Sending test email to: {test_email}")
    
    try:
        result = await send_email_async(
            recipient=test_email,
            subject="🧪 Test Email - State Counter Analytics",
            body="""
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <h2>🧪 Test Email</h2>
                <p>This is a test email from State Counter Analytics.</p>
                <p>If you receive this email, the email configuration is working correctly!</p>
                <hr>
                <p><strong>Configuration Details:</strong></p>
                <ul>
                    <li>Server: {smtp_server}</li>
                    <li>Port: {smtp_port}</li>
                    <li>From: {sender_email}</li>
                </ul>
                <p>✅ Email sending is working!</p>
            </div>
            """.format(
                smtp_server=os.getenv('MAIL_SERVER', 'smtp.gmail.com'),
                smtp_port=os.getenv('MAIL_PORT', 587),
                sender_email=os.getenv('MAIL_USERNAME', 'Not configured')
            )
        )
        
        if result:
            print("✅ Email sent successfully!")
            return True
        else:
            print("❌ Email sending failed")
            return False
            
    except Exception as e:
        print(f"❌ Error sending email: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main function"""
    print("🔧 Email Configuration Debug Tool")
    print("=" * 50)
    
    # Test environment
    test_environment()
    
    # Ask if user wants to test email sending
    print("\n" + "=" * 50)
    choice = input("Do you want to test email sending? (y/n): ").strip().lower()
    
    if choice in ['y', 'yes']:
        # Run async test
        success = asyncio.run(test_email_sending())
        
        if success:
            print("\n🎉 All tests passed! Email configuration is working.")
        else:
            print("\n❌ Email test failed. Check the error messages above.")
    else:
        print("\n⏭️  Skipping email test.")
    
    print("\n📋 Next Steps:")
    print("1. If email variables are missing, update your .env file")
    print("2. If authentication fails, check your email credentials")
    print("3. For Gmail, enable 'Less secure app access' or use App Passwords")
    print("4. For production, consider using SendGrid or AWS SES")

if __name__ == "__main__":
    main()
