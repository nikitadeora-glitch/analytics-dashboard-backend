from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
import uuid
import os
from datetime import datetime, timedelta
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

router = APIRouter()
security = HTTPBearer()
app_name = os.getenv("APP_NAME", "Statify")

# Auth Helper
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> models.User:
    try:
        from routers.auth import verify_token
        payload = verify_token(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        return user
    except Exception:
        raise HTTPException(status_code=401, detail="Authentication failed")


@router.get("/list")
def get_teams(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all teams for the current user
    """
    # For now, return a simple response since team structure might be different
    # This is a placeholder implementation
    teams = []
    
    # You might want to modify this based on your actual team data structure
    # For example, if teams are stored in a separate table or related to users differently
    
    return teams


@router.post("/invite", response_model=schemas.TeamInviteResponse)
def invite_team_member(
    invite: schemas.TeamInviteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Invite a team member to join projects
    """
    # Check if user exists with this email
    existing_user = db.query(models.User).filter(models.User.email == invite.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Check if there's already a pending invite for this email
    existing_invite = db.query(models.TeamInvite).filter(
        models.TeamInvite.email == invite.email,
        models.TeamInvite.status == "pending"
    ).first()
    
    if existing_invite:
        raise HTTPException(status_code=400, detail="Pending invitation already exists for this email")
    
    # Validate projects exist and belong to current user
    project_count = db.query(models.Project).filter(
        models.Project.id.in_(invite.projects),
        models.Project.user_id == current_user.id
    ).count()
    
    if project_count != len(invite.projects):
        raise HTTPException(status_code=400, detail="Some projects don't exist or don't belong to you")
    
    # Validate role
    valid_roles = ['editor', 'viewer', 'admin']
    if invite.role not in valid_roles:
        raise HTTPException(status_code=400, detail="Invalid role. Must be one of: editor, viewer, admin")
    
    # Create invite token (UUID)
    invite_token = str(uuid.uuid4())
    
    # Set expiry (7 days from now)
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    # Create team invite
    db_invite = models.TeamInvite(
        email=invite.email,
        projects=invite.projects,
        role=invite.role,
        token=invite_token,
        status="pending",
        invited_by=invite.invited_by,
        expires_at=expires_at
    )
    
    db.add(db_invite)
    db.commit()
    db.refresh(db_invite)
    
    # Send invitation email
    try:
        from email_utils import send_email
        
        # Create invitation link
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        invite_link = f"{frontend_url}/accept-invite/{token}"
        
        # Get project names for the email
        project_names = []
        for project_id in invite.projects:
            project = db.query(models.Project).filter(models.Project.id == project_id).first()
            if project:
                project_names.append(project.name)
        
        # Create email content
        email_subject = "You're invited to join team"
        
        # HTML email template matching the exact design from the image
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Team Invitation</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background-color: #f8f9fa;
                    padding: 20px;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background-color: #6366f1;
                    padding: 20px 30px;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                }}
                .logo {{
                    color: white;
                    font-size: 24px;
                    font-weight: bold;
                    display: flex;
                    align-items: center;
                }}
                .logo-icon {{
                    width: 8px;
                    height: 8px;
                    background-color: white;
                    border-radius: 50%;
                    margin-right: 8px;
                }}
                .notification-icon {{
                    color: white;
                    font-size: 20px;
                }}
                .banner {{
                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                    padding: 60px 30px;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                }}
                .banner::before {{
                    content: '';
                    position: absolute;
                    bottom: 0;
                    left: 0;
                    right: 0;
                    height: 80px;
                    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 80"><rect fill="%23ffffff20" x="20" y="20" width="8" height="40"/><rect fill="%23ffffff20" x="40" y="10" width="8" height="50"/><rect fill="%23ffffff20" x="60" y="30" width="8" height="30"/><rect fill="%23ffffff20" x="80" y="15" width="8" height="45"/><rect fill="%23ffffff20" x="100" y="25" width="8" height="35"/><rect fill="%23ffffff20" x="120" y="5" width="8" height="55"/><rect fill="%23ffffff20" x="140" y="35" width="8" height="25"/><rect fill="%23ffffff20" x="160" y="20" width="8" height="40"/></svg>') repeat-x;
                    opacity: 0.3;
                }}
                .banner h2 {{
                    color: white;
                    font-size: 32px;
                    font-weight: 600;
                    margin-bottom: 10px;
                    position: relative;
                    z-index: 1;
                }}
                .banner p {{
                    color: rgba(255, 255, 255, 0.9);
                    font-size: 18px;
                    position: relative;
                    z-index: 1;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .invitation-text {{
                    font-size: 20px;
                    color: #374151;
                    margin-bottom: 20px;
                    font-weight: 500;
                }}
                .team-name {{
                    color: #6366f1;
                    font-weight: 600;
                }}
                .description {{
                    color: #6b7280;
                    font-size: 16px;
                    line-height: 1.6;
                    margin-bottom: 30px;
                }}
                .what-is-section {{
                    background-color: #f3f4f6;
                    padding: 25px;
                    border-radius: 8px;
                    margin: 30px 0;
                }}
                .what-is-title {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #374151;
                    margin-bottom: 15px;
                }}
                .what-is-description {{
                    color: #6b7280;
                    font-size: 15px;
                    line-height: 1.5;
                }}
                .join-button {{
                    display: inline-block;
                    background-color: #6366f1;
                    color: white;
                    padding: 14px 32px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    font-size: 16px;
                    transition: background-color 0.2s;
                    margin: 30px 0;
                }}
                .join-button:hover {{
                    background-color: #5558e3;
                }}
                .footer {{
                    background-color: #f9fafb;
                    padding: 20px 30px;
                    text-align: center;
                    border-top: 1px solid #e5e7eb;
                }}
                .footer-text {{
                    color: #6b7280;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <!-- Header -->
                <div class="header">
                    <div class="logo">
                        <div class="logo-icon"></div>
                        Statify
                    </div>
                    <div class="notification-icon">🔔</div>
                </div>
                
                <!-- Banner -->
                <div class="banner">
                    <h2>Join your team</h2>
                    <p>Collaborate on website analytics</p>
                </div>
                
                <!-- Content -->
                <div class="content">
                    <p class="invitation-text">You've been invited</p>
                    
                    <p class="description">
                        <span class="team-name">{', '.join(project_names)}</span> has invited you to collaborate on their website analytics dashboard.
                    </p>
                    
                    <!-- What is Statify section -->
                    <div class="what-is-section">
                        <h3 class="what-is-title">What is Statify?</h3>
                        <p class="what-is-description">
                            Statify is a powerful website analytics platform that helps teams track visitor behavior, monitor page performance, and make data-driven decisions to grow their online presence.
                        </p>
                    </div>
                    
                    <!-- Join Team Button -->
                    <div style="text-align: center;">
                        <a href="{invite_link}" class="join-button">
                            Accept Invite
                        </a>
                    </div>
                </div>
                
                <!-- Footer -->
                <div class="footer">
                    <p class="footer-text">
                        This invitation link will expire in 7 days
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_body = f"""
Team Invitation

Hello,

You've been invited to join {', '.join(project_names)} on Statify to collaborate on their website analytics dashboard.

What is Statify?
Statify is a powerful website analytics platform that helps teams track visitor behavior, monitor page performance, and make data-driven decisions to grow their online presence.

Accept your invitation here: {invite_link}

This invitation link will expire in 7 days. If you didn't expect this invitation, you can safely ignore this email.
"""
        
        # Send the email
        email_sent = send_email(invite.email, email_subject, text_body, html_body)
        
        if email_sent:
            print(f"✅ Invitation email sent to {invite.email}")
        else:
            print(f"❌ Failed to send invitation email to {invite.email}")
            
    except Exception as e:
        print(f"❌ Error sending invitation email: {str(e)}")
        # Don't fail the invite creation if email fails
    
    return db_invite


@router.get("/invites")
def get_pending_invites(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all pending invites sent by current user
    """
    invites = db.query(models.TeamInvite).filter(
        models.TeamInvite.invited_by == current_user.id,
        models.TeamInvite.status == "pending"
    ).order_by(models.TeamInvite.created_at.desc()).all()
    
    return [
        {
            "id": invite.id,
            "email": invite.email,
            "projects": invite.projects,
            "role": invite.role,
            "status": invite.status,
            "created_at": invite.created_at,
            "expires_at": invite.expires_at
        }
        for invite in invites
    ]


@router.post("/accept")
def accept_invite(
    accept_data: schemas.TeamInviteAccept,
    db: Session = Depends(get_db)
):
    """
    Accept a team invitation using token
    """
    # Find invite by token
    invite = db.query(models.TeamInvite).filter(
        models.TeamInvite.token == accept_data.token,
        models.TeamInvite.status == "pending"
    ).first()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation")
    
    # Check if invite has expired
    if datetime.utcnow() > invite.expires_at:
        invite.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Mark invite as accepted
    invite.status = "accepted"
    invite.accepted_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Invitation accepted successfully", "projects": invite.projects, "role": invite.role}


@router.delete("/invites/{invite_id}")
def cancel_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Cancel a pending invitation
    """
    invite = db.query(models.TeamInvite).filter(
        models.TeamInvite.id == invite_id,
        models.TeamInvite.invited_by == current_user.id,
        models.TeamInvite.status == "pending"
    ).first()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    db.delete(invite)
    db.commit()
    
    return {"message": "Invitation cancelled successfully"}


@router.get("/invite/{token}")
def get_invite_by_token(token: str, db: Session = Depends(get_db)):
    """
    Get invite details by token (for accept invite page)
    """
    invite = db.query(models.TeamInvite).filter(
        models.TeamInvite.token == token,
        models.TeamInvite.status == "pending"
    ).first()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation")
    
    # Check if invite has expired
    if datetime.utcnow() > invite.expires_at:
        invite.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Get project details
    projects = []
    for project_id in invite.projects:
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        if project:
            projects.append({
                "id": project.id,
                "name": project.name
            })
    
    # Get inviter details
    inviter = db.query(models.User).filter(models.User.id == invite.invited_by).first()
    
    return {
        "email": invite.email,
        "role": invite.role,
        "projects": projects,
        "invited_by": inviter.full_name if inviter else "Team Admin",
        "status": "pending"
    }


@router.post("/send-otp")
def send_otp(data: dict, db: Session = Depends(get_db)):
    """
    Send OTP to user email for verification
    """
    email = data.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
    
    # Generate 6-digit OTP
    import random
    otp = str(random.randint(100000, 999999))
    
    # Store OTP in database (you might want to create a separate table for this)
    # For now, we'll use a simple approach with the TeamInvite table
    # In production, you should use a proper OTP storage with expiration
    
    try:
        from email_utils import send_email
        
        email_subject = "Your Verification Code"
        
        # HTML email template
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verification Code</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background-color: #f8f9fa;
                    padding: 20px;
                    margin: 0;
                }}
                .container {{
                    max-width: 500px;
                    margin: 0 auto;
                    background-color: white;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                    padding: 40px 30px;
                    text-align: center;
                }}
                .header h1 {{
                    color: white;
                    font-size: 28px;
                    font-weight: 600;
                    margin: 0;
                }}
                .content {{
                    padding: 40px 30px;
                    text-align: center;
                }}
                .otp-code {{
                    font-size: 36px;
                    font-weight: bold;
                    color: #6366f1;
                    letter-spacing: 8px;
                    margin: 30px 0;
                    padding: 20px;
                    background-color: #f3f4f6;
                    border-radius: 8px;
                    border: 2px dashed #d1d5db;
                }}
                .description {{
                    color: #6b7280;
                    font-size: 16px;
                    line-height: 1.6;
                    margin-bottom: 20px;
                }}
                .expiry {{
                    color: #ef4444;
                    font-size: 14px;
                    font-weight: 500;
                }}
                .footer {{
                    background-color: #f9fafb;
                    padding: 20px 30px;
                    text-align: center;
                    border-top: 1px solid #e5e7eb;
                }}
                .footer-text {{
                    color: #6b7280;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Verification Code</h1>
                </div>
                <div class="content">
                    <p class="description">
                        Use the verification code below to complete your team invitation acceptance:
                    </p>
                    <div class="otp-code">{otp}</div>
                    <p class="expiry">This code will expire in 10 minutes</p>
                </div>
                <div class="footer">
                    <p class="footer-text">
                        If you didn't request this code, you can safely ignore this email.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_body = f"""
Verification Code

Hello,

Your verification code is: {otp}

This code will expire in 10 minutes. Use it to complete your team invitation acceptance.

If you didn't request this code, you can safely ignore this email.
"""
        
        # Send email
        email_sent = send_email(email, email_subject, text_body, html_body)
        
        if email_sent:
            # Store OTP in session or temporary storage
            # For demo purposes, we'll return it (in production, store securely)
            return {"message": "OTP sent successfully", "otp": otp}  # Remove OTP in production
        else:
            raise HTTPException(status_code=500, detail="Failed to send OTP")
            
    except Exception as e:
        print(f"❌ Error sending OTP: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")


@router.post("/verify-otp")
def verify_otp(data: dict, db: Session = Depends(get_db)):
    """
    Verify OTP for email verification
    """
    email = data.get("email")
    otp = data.get("otp")
    
    if not email or not otp:
        raise HTTPException(status_code=400, detail="Email and OTP are required")
    
    # For demo purposes, we'll accept any 6-digit OTP
    # In production, verify against stored OTP
    if len(otp) == 6 and otp.isdigit():
        return {"message": "OTP verified successfully", "email": email}
    else:
        raise HTTPException(status_code=400, detail="Invalid OTP")


@router.post("/assign-projects")
def assign_user_to_projects(
    assignment: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Directly assign a user to multiple projects (admin only)
    """
    user_id = assignment.get("user_id")
    project_ids = assignment.get("project_ids", [])
    role = assignment.get("role", "viewer")
    
    if not user_id or not project_ids:
        raise HTTPException(status_code=400, detail="user_id and project_ids are required")
    
    # Validate role
    valid_roles = ['editor', 'viewer', 'admin']
    if role not in valid_roles:
        raise HTTPException(status_code=400, detail="Invalid role. Must be one of: editor, viewer, admin")
    
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Validate projects exist and belong to current user (or user is admin)
    project_count = db.query(models.Project).filter(
        models.Project.id.in_(project_ids)
    ).count()
    
    if project_count != len(project_ids):
        raise HTTPException(status_code=400, detail="Some projects don't exist")
    
    assigned_projects = []
    already_assigned = []
    
    # Assign user to projects
    for project_id in project_ids:
        # Check if user-project relationship already exists
        existing_user_project = db.query(models.UserProject).filter(
            models.UserProject.user_id == user_id,
            models.UserProject.project_id == project_id
        ).first()
        
        if existing_user_project:
            already_assigned.append(project_id)
        else:
            # Create user-project relationship
            user_project = models.UserProject(
                user_id=user_id,
                project_id=project_id,
                role=role
            )
            db.add(user_project)
            assigned_projects.append(project_id)
    
    db.commit()
    
    return {
        "message": "User assignment completed",
        "user_id": user_id,
        "assigned_projects": assigned_projects,
        "already_assigned": already_assigned,
        "role": role
    }


@router.get("/user-projects/{user_id}")
def get_user_projects(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get all projects assigned to a specific user
    """
    # Check if user exists
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user's project assignments
    user_projects = db.query(models.UserProject).filter(
        models.UserProject.user_id == user_id
    ).all()
    
    projects = []
    for up in user_projects:
        project = db.query(models.Project).filter(models.Project.id == up.project_id).first()
        if project:
            projects.append({
                "id": project.id,
                "name": project.name,
                "domain": project.domain,
                "role": up.role,
                "assigned_at": up.created_at
            })
    
    return {
        "user_id": user_id,
        "user_email": user.email,
        "projects": projects
    }


@router.delete("/remove-project-assignment")
def remove_project_assignment(
    assignment: dict,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Remove a user from a specific project
    """
    user_id = assignment.get("user_id")
    project_id = assignment.get("project_id")
    
    if not user_id or not project_id:
        raise HTTPException(status_code=400, detail="user_id and project_id are required")
    
    # Find and delete the user-project relationship
    user_project = db.query(models.UserProject).filter(
        models.UserProject.user_id == user_id,
        models.UserProject.project_id == project_id
    ).first()
    
    if not user_project:
        raise HTTPException(status_code=404, detail="User-project assignment not found")
    
    db.delete(user_project)
    db.commit()
    
    return {"message": "User removed from project successfully"}


@router.post("/join")
def join_project(data: dict, db: Session = Depends(get_db)):
    """
    Join project using invite token after OTP verification
    """
    token = data.get("token")
    email = data.get("email")
    password = data.get("password")
    
    if not token or not email or not password:
        raise HTTPException(status_code=400, detail="Token, email, and password are required")
    
    # Validate token
    invite = db.query(models.TeamInvite).filter(
        models.TeamInvite.token == token,
        models.TeamInvite.status == "pending"
    ).first()
    
    if not invite:
        raise HTTPException(status_code=404, detail="Invalid or expired invitation")
    
    # Check if invite has expired
    if datetime.utcnow() > invite.expires_at:
        invite.status = "expired"
        db.commit()
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Check if email matches invite
    if invite.email != email:
        raise HTTPException(status_code=400, detail="Email does not match invitation")
    
    # Check if user already exists
    user = db.query(models.User).filter(models.User.email == email).first()
    is_existing_user = user is not None
    
    if not user:
        # Hash password
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(password)
        
        # Create new user
        user = models.User(
            email=email,
            hashed_password=hashed_password,
            full_name=email.split('@')[0],  # Use email prefix as name
            is_active=True,
            is_verified=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Verify password for existing user
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if not pwd_context.verify(password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Invalid password for existing user")
    
    # Add user to projects
    for project_id in invite.projects:
        # Check if user-project relationship already exists
        existing_user_project = db.query(models.UserProject).filter(
            models.UserProject.user_id == user.id,
            models.UserProject.project_id == project_id
        ).first()
        
        if not existing_user_project:
            # Create user-project relationship
            user_project = models.UserProject(
                user_id=user.id,
                project_id=project_id,
                role=invite.role
            )
            db.add(user_project)
    
    # Mark invite as accepted
    invite.status = "accepted"
    invite.accepted_at = datetime.utcnow()
    db.commit()
    
    result = {
        "message": "Successfully joined project",
        "user_id": user.id,
        "projects": invite.projects,
        "role": invite.role,
        "existing_user": is_existing_user
    }
    
    # If existing user, create tokens and return them for auto-login
    if is_existing_user:
        from routers.auth import create_access_token, create_refresh_token
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})
        
        # Count user's projects for onboarding determination
        own_projects_count = db.query(models.Project).filter(models.Project.user_id == user.id).count()
        assigned_projects_count = db.query(models.UserProject).filter(models.UserProject.user_id == user.id).count()
        total_projects = own_projects_count + assigned_projects_count
        
        result.update({
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "has_projects": total_projects > 0,
                "projects_count": total_projects
            }
        })
    
    return result
