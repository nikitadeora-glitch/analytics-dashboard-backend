from fastapi import APIRouter, Depends, HTTPException, status, Request, Body , BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer ,HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import secrets
import os
import bcrypt

# Import models and schemas directly
from models import User, PasswordReset
from schemas import UserCreate, UserLogin, Token, PasswordResetRequest, PasswordResetConfirm, GoogleLoginSchema
from database import get_db
from email_utils import send_email_async
import jwt
from routers.google import verify_google_token

router = APIRouter()
security = HTTPBearer()

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
# Token expiration times (in minutes for access token, days for refresh token)
ACCESS_TOKEN_EXPIRE_MINUTES = 30  # 30 minutes
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 days


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


@router.post("/signup", response_model=Token)
async def signup(user_data: UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Register a new user"""
    # Log UTM data if present
    if user_data.utm:
        print(f"🎯 UTM Data during signup: {user_data.utm}")
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
        
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        company_name=user_data.company_name if user_data.company_name else None,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Send welcome email in background (commented out for debugging)
    frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
    welcome_message = f"""
    <h2>Welcome to State Counter Analytics!</h2>
    <p>Hello {user_data.full_name},</p>
    <p>Thank you for signing up with State Counter Analytics. We're excited to have you on board!</p>
    <p>Start tracking your website's performance now by adding your first project.</p>
    <p>Best regards,<br>State Counter Team</p>
    """
    # <p>Start tracking your website's performance now by adding your first project.</p>
    # <p>Best regards,<br>State Counter Team</p>
    # """
    
    # background_tasks.add_task(
    #     send_email_async,
    #         recipient=user_data.email,
    #         subject="Welcome to State Counter Analytics",
    #         body=welcome_message
    # )
    
    # Create tokens for auto-login
    access_token = create_access_token(data={"sub": str(new_user.id)})
    refresh_token = create_refresh_token(data={"sub": str(new_user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": new_user.id,
            "full_name": new_user.full_name,
            "email": new_user.email
        }
    }

@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return tokens"""
    # Log UTM data if present
    if credentials.utm:
        print(f"🎯 UTM Data during login: {credentials.utm}")
    
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
            "email": user.email
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
            "email": user.email
        }
    }

@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Logout user (client should remove tokens)"""
    return {"message": "Logged out successfully"}

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
@router.post("/forgot-password")
async def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Password reset request with UTM tracking"""
    # Log UTM data if present
    if request.utm:
        print(f"🎯 UTM Data during password reset: {request.utm}")
    
    try:
        email = request.email
        print(f"Received password reset request for email: {email}")

        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"No user found with email: {email}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(minutes=10)
        
        print(f"Generated token: {reset_token}")
        print(f"Token expires at (UTC): {expires_at}")

        # Create or update password reset record
        reset_record = db.query(PasswordReset).filter(
            PasswordReset.email == email
        ).first()

        if reset_record:
            reset_record.token = reset_token
            reset_record.expires_at = expires_at
            reset_record.used = False
        else:
            reset_record = PasswordReset(
                email=email,
                token=reset_token,
                expires_at=expires_at
            )
            db.add(reset_record)

        db.commit()

        # Create reset link - Use environment variable
        FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')
        reset_link = f"{FRONTEND_URL}/reset-password?token={reset_token}"


        print(f"Sending password reset email to: {email}")
        print(f"Reset link: {reset_link}")

        # Send email
        try:
            print(f"\n📧 Attempting to send password reset email...")
            email_sent = await send_email_async(
                recipient=email,
                subject="Password Reset Request - State Counter",
                body=f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Password Reset Request</h2>
                    <p>Click the link below to reset your password. This link will expire in 10 minutes:</p>
                    <a href="{reset_link}" style="background: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin: 20px 0;">
                        Reset Password
                    </a>
                    <p>Or copy this link: {reset_link}</p>
                    <p>This link will expire in 10 minutes.</p>
                </div>
                """
            )
            
            if email_sent:
                print(f"✅ Password reset email sent successfully to {email}")
                return {"message": "If your email is registered, you will receive a password reset link"}
            else:
                print(f"❌ Failed to send password reset email to {email}")
                # Don't expose specific error details for security
                return {"message": "If your email is registered, you will receive a password reset link"}
                
        except Exception as e:
            print(f"❌ Error sending password reset email: {str(e)}")
            import traceback
            traceback.print_exc()
            # Always return the same message for security (don't reveal if email exists or not)
            return {"message": "If your email is registered, you will receive a password reset link"}

    except HTTPException as e:
        # Re-raise HTTP exceptions as-is (like our "User not found" error)
        raise e
    except Exception as e:
        print(f"Error in forgot_password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your request"
        )

@router.get("/verify-reset-token")
async def verify_reset_token(
    token: str,
    db: Session = Depends(get_db)
):
    # Rest of the verify_reset_token function...
    """Verify if a password reset token is valid"""
    current_time = datetime.utcnow()
    print("\n=== Token Verification Debug ===")
    print(f"Token: {token}")
    print(f"Verification time (UTC): {current_time}")
    
    # First check if token exists and is not used
    reset_record = db.query(PasswordReset).filter(
        PasswordReset.token == token,
        PasswordReset.used == False
    ).first()
    
    if reset_record:
        print("\nToken found in database:")
        print(f"- ID: {reset_record.id}")
        print(f"- Email: {reset_record.email}")
        print(f"- Created at: {reset_record.created_at}")
        print(f"- Expires at: {reset_record.expires_at} (UTC)")
        print(f"- Is used: {reset_record.used}")
        
        # Check if token is expired
        is_expired = current_time > reset_record.expires_at
        print(f"\nToken status:")
        print(f"- Current time (UTC): {current_time}")
        print(f"- Token expires at: {reset_record.expires_at} (UTC)")
        print(f"- Is expired: {is_expired}")
        
        if is_expired:
            time_elapsed = current_time - reset_record.expires_at
            print(f"- Expired by: {time_elapsed}")
    else:
        print("\nNo active token found in database")
        # Check if token exists but is used
        used_token = db.query(PasswordReset).filter(
            PasswordReset.token == token,
            PasswordReset.used == True
        ).first()
        
        if used_token:
            print("\nToken was already used:")
            print(f"- Used at: {used_token.used_at}")
            print(f"- Expired at: {used_token.expires_at}")
    
    if not reset_record:
        print("\nToken validation failed. Possible reasons:")
        print("- Token not found")
        print("- Token already used")
        
        # Get any matching token for debugging
        any_token = db.query(PasswordReset).filter(
            PasswordReset.token == token
        ).first()
        
        if any_token:
            print("\nFound matching token with issues:")
            print(f"- ID: {any_token.id}")
            print(f"- Email: {any_token.email}")
            print(f"- Created: {any_token.created_at}")
            print(f"- Expires: {any_token.expires_at}")
            print(f"- Used: {any_token.used}")
            if any_token.used:
                print(f"- Used at: {any_token.used_at}")
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )
    
    # Get user email for the token
    user = db.query(User).filter(User.email == reset_record.email).first()
    if not user:
        print(f"\nUser not found for email: {reset_record.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )
    
    print("\n✅ Token is valid")
    print(f"- User: {user.email}")
    print(f"- Token expires in: {reset_record.expires_at - current_time}")
    
    return {
        "message": "Token is valid",
        "user_email": user.email,
        "expires_at": reset_record.expires_at.isoformat()
    }

@router.post("/reset-password")
async def reset_password(
    request: dict,
    db: Session = Depends(get_db)
):
    """Reset password using token"""
    try:
        # Get token and password from request body
        token = request.get('token')
        password = request.get('password')  # Changed from new_password to password
        
        if not token or not password:
            print(f"Missing required fields. Token: {token}, Has password: {bool(password)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token and password are required"
            )

        print(f"Attempting password reset with token: {token}")

        # Find the reset record
        reset_record = db.query(PasswordReset).filter(
            PasswordReset.token == token,
            PasswordReset.used == False,
            PasswordReset.expires_at > datetime.utcnow()
        ).first()

        if not reset_record:
            print("No valid reset record found for token")
            # Check if token exists but is expired
            expired_token = db.query(PasswordReset).filter(
                PasswordReset.token == token
            ).first()
            if expired_token:
                print(f"Token found but expired at: {expired_token.expires_at}")
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired token"
            )

        # Find the user
        user = db.query(User).filter(User.email == reset_record.email).first()
        if not user:
            print(f"User not found for email: {reset_record.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User not found"
            )

        # Update user's password
        user.hashed_password = hash_password(password)
        
        # Mark token as used
        reset_record.used = True
        reset_record.used_at = datetime.utcnow()
        
        db.commit()
        
        print(f"Password successfully reset for user: {user.email}")
        return {"message": "Password has been reset successfully"}

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in reset_password: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while resetting the password"
        )

@router.post("/google")
def google_login(data: GoogleLoginSchema, db: Session = Depends(get_db)):
    # Log UTM data if present
    if data.utm:
        print(f"🎯 UTM Data during Google login: {data.utm}")
    
    # 1️⃣ Verify token
    try:
        payload = verify_google_token(data.id_token)
    except Exception as e:
        print("❌ GOOGLE VERIFY ERROR:", e)
        raise HTTPException(status_code=401, detail="Invalid Google token")

    # 2️⃣ Find user
    user = db.query(User).filter(User.email == payload["email"]).first()

    # 3️⃣ Create user if not exists
    if not user:
        try:
            user = User(
                full_name=payload.get("name") or payload["email"].split("@")[0],
                email=payload["email"],
                google_id=payload["google_id"],
                avatar=payload.get("picture"),
                hashed_password="",  # No password for Google users
                company_name="",  # Empty string instead of None
                is_verified=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        except Exception as e:
            db.rollback()
            print("❌ DB CREATE ERROR:", e)
            raise HTTPException(
                status_code=500,
                detail="User creation failed"
            )

    # 4️⃣ Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email
        }
    }
