import os
import logging
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def send_email_async(recipient: str, subject: str, body: str, html_body: Optional[str] = None):
    """
    Send an email using SendGrid API
    
    Args:
        recipient: Email address of the recipient
        subject: Email subject
        body: Email body (plain text)
        html_body: Email body (HTML) - optional, will use body if not provided
    """
    # Get SendGrid configuration
    api_key = os.getenv("SENDGRID_API_KEY")
    from_email = os.getenv("SENDGRID_FROM_EMAIL")
    app_name = os.getenv("APP_NAME", "Statify")
    
    # Enhanced debugging - Log configuration status
    print("\n=== SENDGRID CONFIGURATION DEBUG ===")
    print(f"SENDGRID_API_KEY: {'SET' if api_key else 'NOT SET'}")
    print(f"SENDGRID_FROM_EMAIL: {'SET' if from_email else 'NOT SET'}")
    print(f"APP_NAME: {app_name}")
    
    # Validate configuration
    if not api_key:
        error_msg = "SENDGRID_API_KEY is not set. Check your .env file."
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False
        
    if not from_email:
        error_msg = "SENDGRID_FROM_EMAIL is not set. Check your .env file."
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False
    
    print(f"\n📧 Attempting to send email to {recipient} via SendGrid")
    print(f"📧 From: {from_email}")
    print(f"📧 To: {recipient}")
    print(f"📧 Subject: {subject}")
    
    try:
        # Create email message
        message = Mail(
            from_email=from_email,
            to_emails=recipient,
            subject=subject,
            html_content=html_body or body,
            plain_text_content=body
        )
        
        # Send email using SendGrid API
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        # Check response
        if response.status_code == 202:
            print(f"📧 Email sent successfully to {recipient}")
            print(f"📧 SendGrid Response: {response.status_code}")
            logger.info(f"Email sent successfully to {recipient}")
            return True
        else:
            error_msg = f"SendGrid API returned status code: {response.status_code}"
            logger.error(error_msg)
            print(f"❌ {error_msg}")
            print(f"❌ Response body: {response.body}")
            return False
            
    except Exception as e:
        error_msg = f"Error sending email via SendGrid: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        import traceback
        print("❌ Full traceback:")
        traceback.print_exc()
        return False

def send_email(recipient: str, subject: str, body: str, html_body: Optional[str] = None):
    """
    Synchronous wrapper for send_email_async
    """
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(send_email_async(recipient, subject, body, html_body))
