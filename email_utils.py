import smtplib
import ssl
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

async def send_email_async(recipient: str, subject: str, body: str):
    """
    Send an email using SMTP with enhanced error handling and timeout
    
    Args:
        recipient: Email address of the recipient
        subject: Email subject
        body: Email body (HTML)
    """
    # Get email configuration
    sender_email = os.getenv("MAIL_USERNAME")
    password = os.getenv("MAIL_PASSWORD")
    smtp_server = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("MAIL_PORT", 587))
    
    # Enhanced debugging - Log all environment variables
    print("\n=== EMAIL CONFIGURATION DEBUG ===")
    print(f"MAIL_USERNAME: {'SET' if sender_email else 'NOT SET'}")
    print(f"MAIL_PASSWORD: {'SET' if password else 'NOT SET'}")
    print(f"MAIL_SERVER: {smtp_server}")
    print(f"MAIL_PORT: {smtp_port}")
    print(f"All ENV vars: {[k for k in os.environ.keys() if 'MAIL' in k.upper()]}")
    
    # Validate configuration
    if not all([sender_email, password]):
        error_msg = "Email configuration is incomplete. Check your .env file."
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False
    
    print(f"\n📧 Attempting to send email to {recipient} via {smtp_server}:{smtp_port}")
    print(f"📧 From: {sender_email}")
    print(f"📧 To: {recipient}")
    print(f"📧 Subject: {subject}")
    
    try:
        # Run the synchronous SMTP operations in a thread pool with timeout
        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(None, _send_email_sync, recipient, subject, body, sender_email, password, smtp_server, smtp_port),
            timeout=30.0  # 30 second timeout
        )
        return result
            
    except asyncio.TimeoutError:
        error_msg = "Email sending timed out after 30 seconds"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        return False
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        import traceback
        print("❌ Full traceback:")
        traceback.print_exc()
        return False

def _send_email_sync(recipient: str, subject: str, body: str, sender_email: str, password: str, smtp_server: str, smtp_port: int):
    """Synchronous email sending function to be run in thread pool"""
    try:
        # Create message
        message = MIMEMultipart()
        message["From"] = f"Statify  <{sender_email}>"
        message["To"] = recipient
        message["Subject"] = subject
        
        # Add HTML body
        message.attach(MIMEText(body, "html"))
        
        # Create SSL context
        context = ssl.create_default_context()
        
        # Create secure connection with server and send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.ehlo()
            
            # Start TLS encryption
            if smtp_port == 587:
                server.starttls(context=context)
                server.ehlo()
            
            # Login to the SMTP server
            logger.info("Authenticating with SMTP server...")
            server.login(sender_email, password)
            logger.info("Successfully authenticated with SMTP server")
            
            # Send the email
            print("📧 Sending email...")
            result = server.send_message(message)
            print(f"📧 Email sent successfully to {recipient}")
            print(f"📧 Server response: {result}")
            logger.info(f"Email sent successfully to {recipient}")
            
            return True
            
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"SMTP Authentication Error: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        print("❌ Please check your email credentials and ensure 'Less secure app access' is enabled in your Google account.")
        print("❌ Or use an App Password if 2FA is enabled.")
        raise
    except smtplib.SMTPException as e:
        error_msg = f"SMTP Error: {e}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        raise
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        print(f"❌ {error_msg}")
        import traceback
        print("❌ Full traceback:")
        traceback.print_exc()
        raise
