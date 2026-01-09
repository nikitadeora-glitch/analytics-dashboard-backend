from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
import models, schemas
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter()
security = HTTPBearer(auto_error=False)  # Make authentication optional

def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    
    try:
        from routers.auth import verify_token
        token = credentials.credentials
        payload = verify_token(token)
        
        if payload is None:
            return None
        
        user_id = payload.get("sub")
        if user_id is None:
            return None
        
        user = db.query(models.User).filter(models.User.id == user_id).first()
        return user
    except:
        return None

@router.post("/", response_model=schemas.ProjectResponse)
def create_project(
    project: schemas.ProjectCreate, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    tracking_code = secrets.token_urlsafe(16)
    db_project = models.Project(
        name=project.name,
        domain=project.domain,
        tracking_code=tracking_code,
        user_id=current_user.id if current_user else None
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/", response_model=list[schemas.ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    """Get projects - if user is authenticated, show only their projects, otherwise show all (for backward compatibility)"""
    if current_user:
        # Authenticated user - show only their projects
        return db.query(models.Project).filter(
            models.Project.user_id == current_user.id,
            models.Project.is_active == True
        ).all()
    else:
        # Non-authenticated user - show all projects (backward compatibility)
        return db.query(models.Project).filter(models.Project.is_active == True).all()

@router.get("/{project_id}", response_model=schemas.ProjectResponse)
def get_project(
    project_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    """Get a specific project - if user is authenticated, check ownership, otherwise allow access (for backward compatibility)"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # If user is authenticated, check if they own the project
    if current_user and project.user_id and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return project

@router.delete("/{project_id}")
def delete_project(
    project_id: int, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    """Delete a project - if user is authenticated, check ownership, otherwise allow access (for backward compatibility)"""
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # If user is authenticated, check if they own the project
    if current_user and project.user_id and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    project.is_active = False
    db.commit()
    return {"message": "Project deleted"}

@router.get("/stats/all")
def get_all_projects_stats(
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    """Get stats for projects - if user is authenticated, show only their projects, otherwise show all (for backward compatibility)"""
    if current_user:
        # Authenticated user - show only their projects
        projects = db.query(models.Project).filter(
            models.Project.user_id == current_user.id,
            models.Project.is_active == True
        ).all()
    else:
        # Non-authenticated user - show all projects (backward compatibility)
        projects = db.query(models.Project).filter(models.Project.is_active == True).all()
    
    if not projects:
        return []
    
    project_ids = [p.id for p in projects]
    
    # Date ranges - using IST timezone for consistency
    import pytz
    ist = pytz.timezone('Asia/Kolkata')
    now_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)
    now_ist = now_utc.astimezone(ist)
    
    today_start_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_utc = today_start_ist.astimezone(pytz.UTC).replace(tzinfo=None)
    
    yesterday_start_ist = today_start_ist - timedelta(days=1)
    yesterday_start_utc = yesterday_start_ist.astimezone(pytz.UTC).replace(tzinfo=None)
    
    month_start_ist = now_ist.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    month_start_utc = month_start_ist.astimezone(pytz.UTC).replace(tzinfo=None)
    
    print(f"Date ranges for page views: Today IST {today_start_ist} (UTC {today_start_utc}), Yesterday IST {yesterday_start_ist} (UTC {yesterday_start_utc}), Month IST {month_start_ist} (UTC {month_start_utc})")
    
    # Bulk query for today's PAGE VIEWS (not visits)
    today_stats = db.query(
        models.Visit.project_id,
        func.count(models.PageView.id).label('count')
    ).join(
        models.PageView, models.Visit.id == models.PageView.visit_id
    ).filter(
        models.Visit.project_id.in_(project_ids),
        models.PageView.viewed_at >= today_start_utc
    ).group_by(models.Visit.project_id).all()
    
    # Bulk query for yesterday's PAGE VIEWS (not visits)
    yesterday_stats = db.query(
        models.Visit.project_id,
        func.count(models.PageView.id).label('count')
    ).join(
        models.PageView, models.Visit.id == models.PageView.visit_id
    ).filter(
        models.Visit.project_id.in_(project_ids),
        models.PageView.viewed_at >= yesterday_start_utc,
        models.PageView.viewed_at < today_start_utc
    ).group_by(models.Visit.project_id).all()
    
    # Bulk query for month's PAGE VIEWS (not visits)
    month_stats = db.query(
        models.Visit.project_id,
        func.count(models.PageView.id).label('count')
    ).join(
        models.PageView, models.Visit.id == models.PageView.visit_id
    ).filter(
        models.Visit.project_id.in_(project_ids),
        models.PageView.viewed_at >= month_start_utc
    ).group_by(models.Visit.project_id).all()
    
    # Bulk query for total PAGE VIEWS (not visits)
    total_stats = db.query(
        models.Visit.project_id,
        func.count(models.PageView.id).label('count')
    ).join(
        models.PageView, models.Visit.id == models.PageView.visit_id
    ).filter(
        models.Visit.project_id.in_(project_ids)
    ).group_by(models.Visit.project_id).all()
    
    # Bulk query for unique visitors (from visits table - this should remain visitor-based)
    unique_visitor_stats = db.query(
        models.Visit.project_id,
        func.count(func.distinct(models.Visit.visitor_id)).label('count')
    ).filter(
        models.Visit.project_id.in_(project_ids)
    ).group_by(models.Visit.project_id).all()
    
    # Bulk query for live visitors (last 5 minutes)
    five_min_ago = datetime.utcnow() - timedelta(minutes=5)
    live_visitor_stats = db.query(
        models.Visit.project_id,
        func.count(func.distinct(models.Visit.visitor_id)).label('count')
    ).filter(
        models.Visit.project_id.in_(project_ids),
        models.Visit.visited_at >= five_min_ago
    ).group_by(models.Visit.project_id).all()
    
    # Convert to dictionaries for easy lookup
    today_dict = {stat.project_id: stat.count for stat in today_stats}
    yesterday_dict = {stat.project_id: stat.count for stat in yesterday_stats}
    month_dict = {stat.project_id: stat.count for stat in month_stats}
    total_dict = {stat.project_id: stat.count for stat in total_stats}
    unique_visitors_dict = {stat.project_id: stat.count for stat in unique_visitor_stats}
    live_visitors_dict = {stat.project_id: stat.count for stat in live_visitor_stats}
    
    # Build response
    result = []
    for project in projects:
        project_data = {
            "id": project.id,
            "name": project.name,
            "domain": project.domain,
            "tracking_code": project.tracking_code,
            "created_at": project.created_at,
            "is_active": project.is_active,
            "today": today_dict.get(project.id, 0),  # Now PAGE VIEWS
            "yesterday": yesterday_dict.get(project.id, 0),  # Now PAGE VIEWS
            "month": month_dict.get(project.id, 0),  # Now PAGE VIEWS
            "total": total_dict.get(project.id, 0),  # Now PAGE VIEWS
            "page_views": total_dict.get(project.id, 0),  # Same as total (page views)
            "unique_visitors": unique_visitors_dict.get(project.id, 0),  # Still visitor-based
            "live_visitors": live_visitors_dict.get(project.id, 0)  # Still visitor-based
        }
        result.append(project_data)
    
    return result
