from email_utils import send_email_async as send_email
from typing import Optional
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def send_welcome_email(recipient_email: str, user_name: str = None) -> bool:
    """
    Send welcome email to new user
    
    Args:
        recipient_email: Email address of the recipient
        user_name: Optional user name for personalization
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    app_name = os.getenv("APP_NAME", "Statify")
    frontend_url = os.getenv("FRONTEND_URL", "https://seo.prpwebs.com")
    
    subject = f"Welcome to {app_name}!"
    
    # Personalize greeting
    greeting = f"Hello {user_name}!" if user_name else "Hello!"
    
    # HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to {app_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Welcome to {app_name}!</h1>
            </div>
            <div class="content">
                <p>{greeting}</p>
                <p>Thank you for joining {app_name}! We're excited to have you on board.</p>
                <p>{app_name} helps you track and analyze your website traffic with powerful analytics and insights.</p>
                
                <p>Get started by exploring your dashboard:</p>
                <div style="text-align: center;">
                    <a href="{frontend_url}" class="button">Go to Dashboard</a>
                </div>
                
                <p>If you have any questions or need help, feel free to reach out to our support team.</p>
                
                <p>Best regards,<br>The {app_name} Team</p>
            </div>
            <div class="footer">
                <p>This email was sent to {recipient_email}. If you didn't create an account, please ignore this email.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
    Welcome to {app_name}!
    
    {greeting}
    
    Thank you for joining {app_name}! We're excited to have you on board.
    
    {app_name} helps you track and analyze your website traffic with powerful analytics and insights.
    
    Get started by visiting your dashboard: {frontend_url}
    
    If you have any questions or need help, feel free to reach out to our support team.
    
    Best regards,
    The {app_name} Team
    
    This email was sent to {recipient_email}. If you didn't create an account, please ignore this email.
    """
    
    return await send_email(recipient_email, subject, text_body, html_body)

async def send_notification_email(recipient_email: str, notification_title: str, notification_message: str) -> bool:
    """
    Send notification email
    
    Args:
        recipient_email: Email address of the recipient
        notification_title: Title of the notification
        notification_message: Message content
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    app_name = os.getenv("APP_NAME", "Statify")
    frontend_url = os.getenv("FRONTEND_URL", "https://seo.prpwebs.com")
    
    subject = f"[{app_name}] {notification_title}"
    
    # HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{notification_title}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; text-align: center; border-radius: 10px 10px 0 0; }}
            .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
            .button {{ display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            .footer {{ text-align: center; margin-top: 30px; color: #666; font-size: 14px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>{notification_title}</h2>
            </div>
            <div class="content">
                <p>Hi there,</p>
                <p>{notification_message}</p>
                
                <div style="text-align: center;">
                    <a href="{frontend_url}" class="button">View Dashboard</a>
                </div>
                
                <p>Best regards,<br>The {app_name} Team</p>
            </div>
            <div class="footer">
                <p>This notification was sent to {recipient_email}.</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Plain text version
    text_body = f"""
    {notification_title}
    
    Hi there,
    
    {notification_message}
    
    View your dashboard: {frontend_url}
    
    Best regards,
    The {app_name} Team
    
    This notification was sent to {recipient_email}.
    """
    
    return await send_email(recipient_email, subject, text_body, html_body)

# Test function
async def test_sendgrid_email():
    """
    Test function to verify SendGrid email functionality
    """
    test_email = "test@example.com"  # Replace with your test email
    
    print("Testing SendGrid Email Configuration...")
    
    # Test welcome email
    result = await send_welcome_email(test_email, "Test User")
    if result:
        print("✅ Welcome email test successful!")
    else:
        print("❌ Welcome email test failed!")
    
    # Test notification email
    result = await send_notification_email(
        test_email, 
        "Test Notification", 
        "This is a test notification to verify SendGrid email functionality is working correctly."
    )
    if result:
        print("✅ Notification email test successful!")
    else:
        print("❌ Notification email test failed!")

if __name__ == "__main__":
    asyncio.run(test_sendgrid_email())