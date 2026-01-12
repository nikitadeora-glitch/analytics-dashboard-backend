from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
import models, schemas
import secrets
from datetime import datetime, timedelta
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import pytz

router = APIRouter()
security = HTTPBearer(auto_error=False)  # optional auth


# -------------------------------
# Optional Auth Helper
# -------------------------------
def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    if not credentials:
        return None
    try:
        from routers.auth import verify_token
        payload = verify_token(credentials.credentials)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id:
            return None

        return db.query(models.User).filter(models.User.id == user_id).first()
    except Exception:
        return None


# -------------------------------
# Create Project
# -------------------------------
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


# -------------------------------
# Get Projects List
# -------------------------------
@router.get("/", response_model=list[schemas.ProjectResponse])
def get_projects(
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    if current_user:
        return db.query(models.Project).filter(
            models.Project.user_id == current_user.id,
            models.Project.is_active == True
        ).all()

    return db.query(models.Project).filter(models.Project.is_active == True).all()


# =====================================================
# 🔥 IMPORTANT: STATIC ROUTE MUST COME FIRST
# =====================================================
@router.get("/stats/all")
def get_all_projects_stats(
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    if current_user:
        projects = db.query(models.Project).filter(
            models.Project.user_id == current_user.id,
            models.Project.is_active == True
        ).all()
    else:
        projects = db.query(models.Project).filter(
            models.Project.is_active == True
        ).all()

    if not projects:
        return []

    project_ids = [p.id for p in projects]

    # -------------------------------
    # Date ranges (IST based)
    # -------------------------------
    ist = pytz.timezone("Asia/Kolkata")
    now_utc = datetime.utcnow().replace(tzinfo=pytz.UTC)
    now_ist = now_utc.astimezone(ist)

    today_start_ist = now_ist.replace(hour=0, minute=0, second=0, microsecond=0)
    today_start_utc = today_start_ist.astimezone(pytz.UTC).replace(tzinfo=None)

    yesterday_start_ist = today_start_ist - timedelta(days=1)
    yesterday_start_utc = yesterday_start_ist.astimezone(pytz.UTC).replace(tzinfo=None)

    month_start_ist = today_start_ist.replace(day=1)
    month_start_utc = month_start_ist.astimezone(pytz.UTC).replace(tzinfo=None)

    # -------------------------------
    # PAGE VIEW BASED STATS
    # -------------------------------
    def page_view_stats(start=None, end=None):
        q = (
            db.query(
                models.Visit.project_id,
                func.count(models.PageView.id).label("count")
            )
            .join(models.PageView, models.Visit.id == models.PageView.visit_id)
            .filter(models.Visit.project_id.in_(project_ids))
        )
        if start:
            q = q.filter(models.PageView.viewed_at >= start)
        if end:
            q = q.filter(models.PageView.viewed_at < end)

        return {r.project_id: r.count for r in q.group_by(models.Visit.project_id).all()}

    today_dict = page_view_stats(start=today_start_utc)
    yesterday_dict = page_view_stats(start=yesterday_start_utc, end=today_start_utc)
    month_dict = page_view_stats(start=month_start_utc)
    total_dict = page_view_stats()

    # -------------------------------
    # VISITOR BASED STATS
    # -------------------------------
    unique_visitors = dict(
        db.query(
            models.Visit.project_id,
            func.count(func.distinct(models.Visit.visitor_id))
        )
        .filter(models.Visit.project_id.in_(project_ids))
        .group_by(models.Visit.project_id)
        .all()
    )

    five_min_ago = datetime.utcnow() - timedelta(minutes=5)
    live_visitors = dict(
        db.query(
            models.Visit.project_id,
            func.count(func.distinct(models.Visit.visitor_id))
        )
        .filter(
            models.Visit.project_id.in_(project_ids),
            models.Visit.visited_at >= five_min_ago
        )
        .group_by(models.Visit.project_id)
        .all()
    )

    # -------------------------------
    # Response
    # -------------------------------
    result = []
    for project in projects:
        result.append({
            "id": project.id,
            "name": project.name,
            "domain": project.domain,
            "tracking_code": project.tracking_code,
            "created_at": project.created_at,
            "is_active": project.is_active,

            # PAGE VIEWS
            "today": today_dict.get(project.id, 0),
            "yesterday": yesterday_dict.get(project.id, 0),
            "month": month_dict.get(project.id, 0),
            "total": total_dict.get(project.id, 0),
            "page_views": total_dict.get(project.id, 0),

            # VISITORS
            "unique_visitors": unique_visitors.get(project.id, 0),
            "live_visitors": live_visitors.get(project.id, 0),
        })

    return result


# -------------------------------
# Get Single Project
# -------------------------------
@router.get("/{project_id}", response_model=schemas.ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user and project.user_id and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return project


# -------------------------------
# Delete Project (Soft Delete)
# -------------------------------
@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user and project.user_id and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    project.is_active = False
    db.commit()
    return {"message": "Project deleted"}
