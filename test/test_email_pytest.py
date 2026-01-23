#!/usr/bin/env python3
"""
Pytest-compatible email configuration tests
"""

import os
import pytest
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the current directory to Python path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_utils import send_email_async

def test_environment():
    """Test if environment variables are loaded correctly"""
    # Check which .env file exists
    env_files = ['.env', '.env.local', '.env.production']
    found_files = [f for f in env_files if os.path.exists(f)]
    assert len(found_files) > 0, "No .env file found"
    
    # Check required email variables
    required_vars = ['MAIL_USERNAME', 'MAIL_PASSWORD', 'MAIL_SERVER', 'MAIL_PORT']
    for var in required_vars:
        value = os.getenv(var)
        assert value is not None, f"Required environment variable {var} is not set"
        assert value.strip() != "", f"Environment variable {var} is empty"

@pytest.mark.asyncio
async def test_email_sending():
    """Test actual email sending with configured email"""
    # Get email from environment or use a test email
    test_email = os.getenv('MAIL_USERNAME')  # Send to self for testing
    
    assert test_email is not None, "MAIL_USERNAME not configured for testing"
    assert '@' in test_email, "Invalid email format in MAIL_USERNAME"
    
    # Test email sending
    result = await send_email_async(
        recipient=test_email,
        subject="🧪 Automated Test Email - State Counter Analytics",
        body=f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2>🧪 Automated Test Email</h2>
            <p>This is an automated test email from State Counter Analytics.</p>
            <p>If you receive this email, the email configuration is working correctly!</p>
            <hr>
            <p><strong>Test Details:</strong></p>
            <ul>
                <li>Server: {os.getenv('MAIL_SERVER')}</li>
                <li>Port: {os.getenv('MAIL_PORT')}</li>
                <li>From: {os.getenv('MAIL_USERNAME')}</li>
                <li>To: {test_email}</li>
            </ul>
            <p>✅ Email sending is working!</p>
            <p><em>This was an automated test. No action needed.</em></p>
        </div>
        """
    )
    
    assert result is True, "Email sending failed"

def test_email_config_values():
    """Test that email configuration values are valid"""
    mail_server = os.getenv('MAIL_SERVER')
    mail_port = os.getenv('MAIL_PORT')
    mail_username = os.getenv('MAIL_USERNAME')
    
    # Test server
    assert mail_server in ['smtp.gmail.com', 'smtp.sendgrid.net', 'smtp.mailgun.org'], f"Unexpected mail server: {mail_server}"
    
    # Test port
    port = int(mail_port)
    assert port in [587, 465, 2525], f"Unexpected mail port: {port}"
    
    # Test email format
    assert '@' in mail_username, f"Invalid email format: {mail_username}"
    assert '.' in mail_username.split('@')[1], f"Invalid email domain: {mail_username}"
