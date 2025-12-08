from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
import models

router = APIRouter()

@router.get("/{project_id}/most-visited")
def get_most_visited_pages(project_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """Get all visited pages sorted by total views (Top Pages)"""
    # Get page views with aggregated data
    page_stats = db.query(
        models.PageView.url,
        models.PageView.title,
        func.count(models.PageView.id).label('total_views'),
        func.count(func.distinct(models.PageView.visit_id)).label('unique_sessions'),
        func.avg(models.PageView.time_spent).label('avg_time_spent')
    ).join(models.Visit).filter(
        models.Visit.project_id == project_id
    ).group_by(
        models.PageView.url,
        models.PageView.title
    ).order_by(desc('total_views')).limit(limit).all()
    
    result = []
    for ps in page_stats:
        # Calculate bounce rate for this page
        # (sessions where this was both entry and exit)
        bounced = db.query(func.count(models.Visit.id)).filter(
            models.Visit.project_id == project_id,
            models.Visit.entry_page == ps[0],
            models.Visit.exit_page == ps[0]
        ).scalar() or 0
        
        total_as_entry = db.query(func.count(models.Visit.id)).filter(
            models.Visit.project_id == project_id,
            models.Visit.entry_page == ps[0]
        ).scalar() or 1
        
        bounce_rate = (bounced / total_as_entry * 100) if total_as_entry > 0 else 0
        
        # Get all visits that viewed this page with visitor_id and session_id
        visits = db.query(
            models.Visit.session_id,
            models.Visit.visitor_id,
            models.Visit.visited_at,
            models.Visit.session_duration
        ).join(models.PageView).filter(
            models.Visit.project_id == project_id,
            models.PageView.url == ps[0]
        ).order_by(desc(models.Visit.visited_at)).distinct().all()
        
        result.append({
            "url": ps[0],
            "title": ps[1],
            "total_views": ps[2],
            "unique_views": ps[3],
            "avg_time_spent": ps[4] or 0,
            "bounce_rate": bounce_rate,
            "visits": [{
                "session_id": v[0],
                "visitor_id": v[1],
                "visited_at": v[2],
                "time_spent": v[3] or 0
            } for v in visits]
        })
    
    return result

@router.get("/{project_id}/entry-pages")
def get_entry_pages(project_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """Get pages where visitors first land (entry pages)"""
    entry_pages = db.query(
        models.Visit.entry_page,
        func.count(models.Visit.id).label('sessions'),
        func.count(func.distinct(models.Visit.visitor_id)).label('unique_visitors')
    ).filter(
        models.Visit.project_id == project_id,
        models.Visit.entry_page.isnot(None)
    ).group_by(models.Visit.entry_page).order_by(desc('sessions')).limit(limit).all()
    
    result = []
    for ep in entry_pages:
        # Calculate bounce rate (sessions with only 1 page view)
        total_sessions = ep[1]
        bounced_sessions = db.query(func.count(models.Visit.id)).filter(
            models.Visit.project_id == project_id,
            models.Visit.entry_page == ep[0],
            models.Visit.entry_page == models.Visit.exit_page  # Entry = Exit means bounced
        ).scalar() or 0
        
        bounce_rate = (bounced_sessions / total_sessions * 100) if total_sessions > 0 else 0
        
        # Get all visits for this entry page with visitor_id and session_id
        visits = db.query(
            models.Visit.session_id,
            models.Visit.visitor_id,
            models.Visit.visited_at,
            models.Visit.session_duration
        ).filter(
            models.Visit.project_id == project_id,
            models.Visit.entry_page == ep[0]
        ).order_by(desc(models.Visit.visited_at)).all()
        
        # Calculate total page views for this entry page
        total_page_views = db.query(func.count(models.PageView.id)).join(models.Visit).filter(
            models.Visit.project_id == project_id,
            models.Visit.entry_page == ep[0]
        ).scalar() or 0
        
        result.append({
            "page": ep[0],
            "sessions": ep[1],
            "unique_visitors": ep[2],
            "bounce_rate": bounce_rate,
            "total_page_views": total_page_views,
            "visits": [{
                "session_id": v[0],
                "visitor_id": v[1],
                "visited_at": v[2],
                "time_spent": v[3] or 0
            } for v in visits]
        })
    
    return result

@router.get("/{project_id}/exit-pages")
def get_exit_pages(project_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """Get pages where visitors leave the site (exit pages)"""
    exit_pages = db.query(
        models.Visit.exit_page,
        func.count(models.Visit.id).label('exits'),
        func.count(func.distinct(models.Visit.visitor_id)).label('unique_visitors')
    ).filter(
        models.Visit.project_id == project_id,
        models.Visit.exit_page.isnot(None)
    ).group_by(models.Visit.exit_page).order_by(desc('exits')).limit(limit).all()
    
    result = []
    for ep in exit_pages:
        # Calculate exit rate (exits from this page / total page views)
        total_exits = ep[1]
        total_views = db.query(func.count(models.PageView.id)).join(models.Visit).filter(
            models.Visit.project_id == project_id,
            models.PageView.url == ep[0]
        ).scalar() or total_exits
        
        exit_rate = (total_exits / total_views * 100) if total_views > 0 else 0
        
        # Get all visits for this exit page with visitor_id and session_id
        visits = db.query(
            models.Visit.session_id,
            models.Visit.visitor_id,
            models.Visit.visited_at,
            models.Visit.session_duration
        ).filter(
            models.Visit.project_id == project_id,
            models.Visit.exit_page == ep[0]
        ).order_by(desc(models.Visit.visited_at)).all()
        
        # Calculate total page views for this exit page
        total_page_views = db.query(func.count(models.PageView.id)).join(models.Visit).filter(
            models.Visit.project_id == project_id,
            models.Visit.exit_page == ep[0]
        ).scalar() or 0
        
        result.append({
            "page": ep[0],
            "exits": ep[1],
            "unique_visitors": ep[2],
            "bounce_rate": exit_rate,  # Using bounce_rate field for exit rate
            "total_page_views": total_page_views,
            "visits": [{
                "session_id": v[0],
                "visitor_id": v[1],
                "visited_at": v[2],
                "time_spent": v[3] or 0
            } for v in visits]
        })
    
    return result

@router.get("/{project_id}/page-activity")
def get_page_activity(project_id: int, hours: int = 24, db: Session = Depends(get_db)):
    from datetime import datetime, timedelta
    
    time_ago = datetime.utcnow() - timedelta(hours=hours)
    
    # SQLite compatible - use strftime instead of date_trunc
    activity = db.query(
        func.strftime('%Y-%m-%d %H:00:00', models.PageView.viewed_at).label('hour'),
        func.count(models.PageView.id).label('views')
    ).join(models.Visit).filter(
        models.Visit.project_id == project_id,
        models.PageView.viewed_at >= time_ago
    ).group_by('hour').order_by('hour').all()
    
    return [{"hour": str(a[0]), "views": a[1]} for a in activity]
