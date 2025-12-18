from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
import secrets
import os
import requests
import json

from database import get_db
from models import User, PasswordReset
from schemas import UserCreate, UserLogin, Token, PasswordResetRequest, PasswordResetConfirm

router = APIRouter()
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict):
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str, token_type: str = "access"):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except jwt.PyJWTError:
        return None

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def send_email_via_sendplus(to_email: str, subject: str, html_content: str):
    """Send email using SendPlus API"""
    try:
        # SendPlus API configuration
        sendplus_api_key = os.getenv("SENDPLUS_API_KEY")
        sendplus_api_url = "https://api.sendplus.in/api/mail/send"
        
        if not sendplus_api_key:
            print("⚠️ SENDPLUS_API_KEY not found in environment variables")
            return False
        
        # Email payload for SendPlus
        payload = {
            "apikey": sendplus_api_key,
            "to": to_email,
            "from": os.getenv("FROM_EMAIL", "noreply@statecounter.com"),
            "fromname": "State Counter Analytics",
            "subject": subject,
            "html": html_content
        }
        
        # Send email via SendPlus
        response = requests.post(sendplus_api_url, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print(f"✅ Email sent successfully to {to_email}")
                return True
            else:
                print(f"❌ SendPlus API error: {result.get('message', 'Unknown error')}")
                return False
        else:
            print(f"❌ SendPlus API HTTP error: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error sending email: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error sending email: {str(e)}")
        return False



@router.post("/signup", response_model=Token)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    user = User(
        full_name=user_data.fullName,
        email=user_data.email,
        company_name=user_data.companyName,
        hashed_password=hashed_password
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create access and refresh tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    

    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "company_name": user.company_name
        }
    }

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return tokens"""
    user = db.query(User).filter(User.email == credentials.email).first()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "company_name": user.company_name
        }
    }

@router.post("/refresh", response_model=Token)
def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token using refresh token"""
    payload = verify_token(refresh_token, "refresh")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "company_name": user.company_name
        }
    }

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should remove tokens)"""
    return {"message": "Logged out successfully"}

@router.get("/test")
def test_endpoint():
    """Test endpoint to check if logs are working"""
    print("🧪 Test endpoint called!")
    return {"message": "Test successful"}

@router.post("/forgot-password")
def forgot_password(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """Send password reset email via SendPlus"""
    print(f"🔍 Forgot password request for email: {request.email}")
    
    # Step 3: Check if email is registered in system
    user = db.query(User).filter(User.email == request.email).first()
    print(f"🔍 User found: {user is not None}")
    
    if not user:
        # Don't reveal if email exists or not for security
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Step 4: Generate secure reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(minutes=15)  # Token expires in 15 minutes
    
    # Save reset token to database with unused status
    password_reset = PasswordReset(
        user_id=user.id,
        token=reset_token,
        expires_at=expires_at,
        used=False
    )
    
    db.add(password_reset)
    db.commit()
    
    # Step 5: Create reset password link (HTTPS compulsory in production)
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3001')
    reset_url = f"{frontend_url}/reset-password?token={reset_token}"
    
    # Step 6: Send email via SendPlus
    reset_email_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Password Reset Request</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4; }}
            .container {{ max-width: 600px; margin: 0 auto; background-color: white; }}
            .header {{ background: linear-gradient(135deg, #0f0c29 0%, #302b63 100%); color: white; padding: 40px 30px; text-align: center; }}
            .header h1 {{ margin: 0; font-size: 28px; font-weight: 700; }}
            .content {{ padding: 40px 30px; }}
            .content p {{ margin: 0 0 20px 0; font-size: 16px; line-height: 1.6; }}
            .button {{ display: inline-block; background: linear-gradient(135deg, #0f0c29 0%, #302b63 100%); color: white !important; padding: 15px 30px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 20px 0; font-size: 16px; }}
            .button:hover {{ background: linear-gradient(135deg, #302b63 0%, #0f0c29 100%); }}
            .footer {{ background-color: #f8f9fa; padding: 30px; text-align: center; color: #666; font-size: 14px; }}
            .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; border-radius: 8px; padding: 15px; margin: 20px 0; color: #856404; }}
            .link-text {{ word-break: break-all; color: #666; font-size: 14px; background-color: #f8f9fa; padding: 10px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔐 Password Reset Request</h1>
            </div>
            <div class="content">
                <p>Hi <strong>{user.full_name}</strong>,</p>
                
                <p>We received a request to reset the password for your <strong>State Counter Analytics</strong> account.</p>
                
                <p>Click the button below to create a new password:</p>
                
                <p style="text-align: center;">
                    <a href="{reset_url}" class="button">Reset My Password</a>
                </p>
                
                <div class="warning">
                    <p><strong>⏰ Important:</strong> This link will expire in <strong>15 minutes</strong> for security reasons.</p>
                </div>
                
                <p>If you didn't request this password reset, please ignore this email. Your account remains secure.</p>
                
                <p>If the button doesn't work, copy and paste this link into your browser:</p>
                <div class="link-text">{reset_url}</div>
            </div>
            <div class="footer">
                <p><strong>State Counter Analytics Team</strong></p>
                <p>Need help? Contact us at support@statecounter.com</p>
                <p style="margin-top: 20px; font-size: 12px; color: #999;">
                    This is an automated email. Please do not reply to this message.
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Send email via SendPlus
    email_sent = send_email_via_sendplus(
        to_email=user.email,
        subject="🔐 Reset Your State Counter Password - Expires in 15 minutes",
        html_content=reset_email_html
    )
    
    if email_sent:
        print(f"✅ Password reset email sent to {user.email}")
    else:
        print(f"❌ Failed to send password reset email to {user.email}")
        # For development: Print reset URL to console as fallback
        print(f"🔗 Password Reset URL (fallback): {reset_url}")
    
    return {"message": "If the email exists, a reset link has been sent"}

@router.get("/verify-reset-token/{token}")
def verify_reset_token(token: str, db: Session = Depends(get_db)):
    """Verify if reset token is valid"""
    print(f"🔍 Verifying reset token: {token[:10]}...")
    
    # Check if token exists and is valid
    password_reset = db.query(PasswordReset).filter(
        PasswordReset.token == token,
        PasswordReset.used == False,
        PasswordReset.expires_at > datetime.utcnow()
    ).first()
    
    if not password_reset:
        print("❌ Invalid or expired reset token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user info
    user = db.query(User).filter(User.id == password_reset.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    print(f"✅ Valid reset token for user: {user.email}")
    
    return {
        "valid": True,
        "user_email": user.email,
        "expires_at": password_reset.expires_at
    }

@router.post("/reset-password")
def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Reset password using token"""
    print(f"🔑 Reset password request with token: {request.token[:10]}...")
    
    # Step 7: Verify reset token
    password_reset = db.query(PasswordReset).filter(
        PasswordReset.token == request.token,
        PasswordReset.used == False,
        PasswordReset.expires_at > datetime.utcnow()
    ).first()
    
    if not password_reset:
        print("❌ Invalid or expired reset token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Step 9: Update user password securely
    user = db.query(User).filter(User.id == password_reset.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    # Hash new password
    user.hashed_password = hash_password(request.password)
    
    # Step 9: Mark token as used (single use only)
    password_reset.used = True
    
    db.commit()
    
    print(f"✅ Password reset successfully for user: {user.email}")
    
    # Step 10: Return success response
    return {"message": "Password reset successfully"}

@router.get("/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "company_name": current_user.company_name,
        "is_verified": current_user.is_verified,
        "created_at": current_user.created_at
    }