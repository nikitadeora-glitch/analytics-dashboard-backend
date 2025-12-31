import asyncio
import os
from email_utils import send_email_async

def test_email_send():
    recipient = "nikita.deora@prpwebs.in"  # Change this to your test email
    subject = "Test Email from State Counter"
    body = """
    <h2>Test Email</h2>
    <p>This is a test email to verify email sending functionality.</p>
    <p>If you're seeing this, the email sending is working correctly!</p>
    """
    
    print(f"Sending test email to {recipient}...")
    success = asyncio.run(send_email_async(recipient, subject, body))
    
    if success:
        print("[SUCCESS] Email sent successfully!")
    else:
        print("[ERROR] Failed to send email. Please check the logs above for errors.")

if __name__ == "__main__":
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Print current email config for debugging
    print("Current Email Configuration:")
    print(f"MAIL_SERVER: {os.getenv('MAIL_SERVER')}")
    print(f"MAIL_PORT: {os.getenv('MAIL_PORT')}")
    print(f"MAIL_USERNAME: {os.getenv('MAIL_USERNAME')}")
    print(f"MAIL_ENCRYPTION: {os.getenv('MAIL_ENCRYPTION')}")
    
    test_email_send()
