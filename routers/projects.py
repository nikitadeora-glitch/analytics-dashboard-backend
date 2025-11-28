from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
import models, schemas
import secrets
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/", response_model=schemas.ProjectResponse)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    tracking_code = secrets.token_urlsafe(16)
    db_project = models.Project(
        name=project.name,
        domain=project.domain,
        tracking_code=tracking_code
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/", response_model=list[schemas.ProjectResponse])
def get_projects(db: Session = Depends(get_db)):
    return db.query(models.Project).filter(models.Project.is_active == True).all()

@router.get("/{project_id}", response_model=schemas.ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.is_active = False
    db.commit()
    return {"message": "Project deleted"}

@router.get("/stats/all")
def get_all_projects_stats(db: Session = Depends(get_db)):
    projects = db.query(models.Project).filter(models.Project.is_active == True).all()
    
    result = []
    for project in projects:
        # Today's stats
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        today_visits = db.query(models.Visit).filter(
            models.Visit.project_id == project.id,
            models.Visit.visited_at >= today_start
        ).count()
        
        # Yesterday's stats
        yesterday_start = today_start - timedelta(days=1)
        yesterday_visits = db.query(models.Visit).filter(
            models.Visit.project_id == project.id,
            models.Visit.visited_at >= yesterday_start,
            models.Visit.visited_at < today_start
        ).count()
        
        # This month's stats
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        month_visits = db.query(models.Visit).filter(
            models.Visit.project_id == project.id,
            models.Visit.visited_at >= month_start
        ).count()
        
        # Total visits
        total_visits = db.query(models.Visit).filter(
            models.Visit.project_id == project.id
        ).count()
        
        # Total page views
        total_page_views = db.query(func.sum(models.Page.total_views)).filter(
            models.Page.project_id == project.id
        ).scalar() or 0
        
        result.append({
            "id": project.id,
            "name": project.name,
            "domain": project.domain,
            "tracking_code": project.tracking_code,
            "created_at": project.created_at,
            "today": today_visits,
            "yesterday": yesterday_visits,
            "month": month_visits,
            "total": total_visits,
            "page_views": total_page_views
        })
    
    return result
