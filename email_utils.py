import smtplib
import ssl
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
    Send an email using SMTP with enhanced error handling
    
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
    
    # Validate configuration
    if not all([sender_email, password]):
        logger.error("Email configuration is incomplete. Check your .env file.")
        return False
    
    logger.info(f"Attempting to send email to {recipient} via {smtp_server}:{smtp_port}")
    
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
            logger.info("Sending email...")
            server.send_message(message)
            logger.info(f"Email sent successfully to {recipient}")
            
            return True
            
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP Authentication Error: {e}")
        logger.error("Please check your email credentials and ensure 'Less secure app access' is enabled in your Google account.")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP Error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    
    return False
