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
    
    # Date ranges
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday_start = today_start - timedelta(days=1)
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Bulk query for today's visits
    today_stats = db.query(
        models.Visit.project_id,
        func.count(models.Visit.id).label('count')
    ).filter(
        models.Visit.project_id.in_(project_ids),
        models.Visit.visited_at >= today_start
    ).group_by(models.Visit.project_id).all()
    
    # Bulk query for yesterday's visits
    yesterday_stats = db.query(
        models.Visit.project_id,
        func.count(models.Visit.id).label('count')
    ).filter(
        models.Visit.project_id.in_(project_ids),
        models.Visit.visited_at >= yesterday_start,
        models.Visit.visited_at < today_start
    ).group_by(models.Visit.project_id).all()
    
    # Bulk query for month's visits
    month_stats = db.query(
        models.Visit.project_id,
        func.count(models.Visit.id).label('count')
    ).filter(
        models.Visit.project_id.in_(project_ids),
        models.Visit.visited_at >= month_start
    ).group_by(models.Visit.project_id).all()
    
    # Bulk query for total visits
    total_stats = db.query(
        models.Visit.project_id,
        func.count(models.Visit.id).label('count')
    ).filter(
        models.Visit.project_id.in_(project_ids)
    ).group_by(models.Visit.project_id).all()
    
    # Bulk query for page views
    page_view_stats = db.query(
        models.Page.project_id,
        func.sum(models.Page.total_views).label('total_views')
    ).filter(
        models.Page.project_id.in_(project_ids)
    ).group_by(models.Page.project_id).all()
    
    # Convert to dictionaries for easy lookup
    today_dict = {stat.project_id: stat.count for stat in today_stats}
    yesterday_dict = {stat.project_id: stat.count for stat in yesterday_stats}
    month_dict = {stat.project_id: stat.count for stat in month_stats}
    total_dict = {stat.project_id: stat.count for stat in total_stats}
    page_views_dict = {stat.project_id: stat.total_views or 0 for stat in page_view_stats}
    
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
            "today": today_dict.get(project.id, 0),
            "yesterday": yesterday_dict.get(project.id, 0),
            "month": month_dict.get(project.id, 0),
            "total": total_dict.get(project.id, 0),
            "page_views": page_views_dict.get(project.id, 0),
            "unique_visitors": total_dict.get(project.id, 0),  # Simplified for now
            "live_visitors": 0  # Would need real-time calculation
        }
        result.append(project_data)
    
    return result
    
    # Convert to dictionaries for fast lookup
    today_dict = {stat.project_id: stat.count for stat in today_stats}
    yesterday_dict = {stat.project_id: stat.count for stat in yesterday_stats}
    month_dict = {stat.project_id: stat.count for stat in month_stats}
    total_dict = {stat.project_id: stat.count for stat in total_stats}
    page_views_dict = {stat.project_id: int(stat.total_views or 0) for stat in page_view_stats}
    
    # Build result
    result = []
    for project in projects:
        result.append({
            "id": project.id,
            "name": project.name,
            "domain": project.domain,
            "tracking_code": project.tracking_code,
            "created_at": project.created_at,
            "updated_at": project.created_at,  # Add updated_at field
            "today": today_dict.get(project.id, 0),
            "yesterday": yesterday_dict.get(project.id, 0),
            "month": month_dict.get(project.id, 0),
            "total": total_dict.get(project.id, 0),
            "page_views": page_views_dict.get(project.id, 0),
            "unique_visitors": total_dict.get(project.id, 0),  # For now, same as total visits
            "live_visitors": 0  # Add live visitors (can be enhanced later)
        })
    
    return result
