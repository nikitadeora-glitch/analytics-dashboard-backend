import pytest
import asyncio
import os
from dotenv import load_dotenv
from email_utils import send_email_async

@pytest.mark.asyncio
async def test_send_email():
    recipient = "nikita.deora@prpwebs.in"
    subject = "Test Email from State Counter"
    body = """
    <h2>Test Email</h2>
    <p>This is a test email sent from the State Counter application.</p>
    <p>If you're seeing this, the email sending is working correctly!</p>
    """
    
    print(f"Sending test email to {recipient}...")
    success = await send_email_async(recipient, subject, body)
    
    if success:
        print("[SUCCESS] Test email sent successfully!")
    else:
        print("[ERROR] Failed to send test email. Check the logs above for errors.")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(test_send_email())
