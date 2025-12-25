from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from database import get_db
import models
import utils

router = APIRouter()

@router.get("/{project_id}/most-visited")
def get_most_visited_pages(project_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """Get all visited pages sorted by total views (Top Pages), grouped by Base URL"""
    # Group by Base URL (removing query params)
    base_url_exp = func.split_part(models.PageView.url, '?', 1)
    
    page_stats = db.query(
        base_url_exp.label('base_url'),
        func.count(models.PageView.id).label('total_views'),
        func.count(func.distinct(models.PageView.visit_id)).label('unique_sessions'),
        func.avg(models.PageView.time_spent).label('avg_time_spent')
    ).join(models.Visit).filter(
        models.Visit.project_id == project_id
    ).group_by(
        base_url_exp
    ).order_by(desc('total_views')).limit(limit).all()
    
    result = []
    for ps in page_stats:
        base_url = ps[0]
        
        # Get best title (shortest usually implies main page name)
        title = db.query(models.PageView.title).join(models.Visit).filter(
            models.Visit.project_id == project_id,
            func.split_part(models.PageView.url, '?', 1) == base_url,
            models.PageView.title.isnot(None)
        ).order_by(func.length(models.PageView.title)).limit(1).scalar()
        
        title = title or base_url
        
        # Calculate bounce rate for this base_url
        # Sessions where entry_page base == this base AND entry == exit
        bounced = db.query(func.count(models.Visit.id)).filter(
            models.Visit.project_id == project_id,
            func.split_part(models.Visit.entry_page, '?', 1) == base_url,
            models.Visit.entry_page == models.Visit.exit_page
        ).scalar() or 0
        
        total_as_entry = db.query(func.count(models.Visit.id)).filter(
            models.Visit.project_id == project_id,
            func.split_part(models.Visit.entry_page, '?', 1) == base_url
        ).scalar() or 1
        
        bounce_rate = (bounced / total_as_entry * 100) if total_as_entry > 0 else 0
        
        # Get all visits that viewed ANY page matching this base_url
        visits = db.query(
            models.Visit.session_id,
            models.Visit.visitor_id,
            models.Visit.visited_at,
            models.Visit.session_duration
        ).join(models.PageView).filter(
            models.Visit.project_id == project_id,
            func.split_part(models.PageView.url, '?', 1) == base_url
        ).order_by(desc(models.Visit.visited_at)).distinct().all()
        
        result.append({
            "url": base_url,
            "title": title,
            "total_views": ps[1],
            "unique_views": ps[2],
            "avg_time_spent": ps[3] or 0,
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
    """Get pages where visitors first land (entry pages), grouped by Base URL"""
    base_url_exp = func.split_part(models.Visit.entry_page, '?', 1)

    entry_pages = db.query(
        base_url_exp.label('entry_page'),
        func.count(models.Visit.id).label('sessions'),
        func.count(func.distinct(models.Visit.visitor_id)).label('unique_visitors')
    ).filter(
        models.Visit.project_id == project_id,
        models.Visit.entry_page.isnot(None)
    ).group_by(base_url_exp).order_by(desc('sessions')).limit(limit).all()
    
    result = []
    for ep in entry_pages:
        base_url = ep[0]
        sessions = ep[1]
        unique_visitors = ep[2]

        # Get best title for this base url
        title = db.query(models.PageView.title).join(models.Visit).filter(
            models.Visit.project_id == project_id,
            func.split_part(models.PageView.url, '?', 1) == base_url,
            models.PageView.title.isnot(None)
        ).order_by(func.length(models.PageView.title)).limit(1).scalar()
        
        title = title or base_url

        # Check bounce rate
        bounced_sessions = db.query(func.count(models.Visit.id)).filter(
            models.Visit.project_id == project_id,
            func.split_part(models.Visit.entry_page, '?', 1) == base_url,
            models.Visit.entry_page == models.Visit.exit_page
        ).scalar() or 0
        
        bounce_rate = (bounced_sessions / sessions * 100) if sessions > 0 else 0
        
        # Get all visits for this entry page base url
        visits = db.query(
            models.Visit.session_id,
            models.Visit.visitor_id,
            models.Visit.visited_at,
            models.Visit.session_duration
        ).filter(
            models.Visit.project_id == project_id,
            func.split_part(models.Visit.entry_page, '?', 1) == base_url
        ).order_by(desc(models.Visit.visited_at)).all()
        
        # Total views in these sessions or of this page?
        # Let's count views of pages matching this base_url (to simulate "hits on this entry page")
        total_page_views = db.query(func.count(models.PageView.id)).join(models.Visit).filter(
            models.Visit.project_id == project_id,
            func.split_part(models.PageView.url, '?', 1) == base_url
        ).scalar() or 0
        
        result.append({
            "page": base_url,
            "title": title,
            "sessions": sessions,
            "unique_visitors": unique_visitors,
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
    """Get pages where visitors leave the site (exit pages), grouped by Base URL"""
    base_url_exp = func.split_part(models.Visit.exit_page, '?', 1)

    exit_pages = db.query(
        base_url_exp.label('exit_page'),
        func.count(models.Visit.id).label('exits'),
        func.count(func.distinct(models.Visit.visitor_id)).label('unique_visitors')
    ).filter(
        models.Visit.project_id == project_id,
        models.Visit.exit_page.isnot(None)
    ).group_by(base_url_exp).order_by(desc('exits')).limit(limit).all()
    
    result = []
    for ep in exit_pages:
        base_url = ep[0]
        exits = ep[1]
        
        # Get best title
        title = db.query(models.PageView.title).join(models.Visit).filter(
            models.Visit.project_id == project_id,
            func.split_part(models.PageView.url, '?', 1) == base_url,
            models.PageView.title.isnot(None)
        ).order_by(func.length(models.PageView.title)).limit(1).scalar()
        
        title = title or base_url
        
        # Calculate exit rate logic 
        # Total views of this base URL
        total_views = db.query(func.count(models.PageView.id)).join(models.Visit).filter(
            models.Visit.project_id == project_id,
            func.split_part(models.PageView.url, '?', 1) == base_url
        ).scalar() or exits
        
        exit_rate = (exits / total_views * 100) if total_views > 0 else 0
        
        # Get all visits for this exit page base
        visits = db.query(
            models.Visit.session_id,
            models.Visit.visitor_id,
            models.Visit.visited_at,
            models.Visit.session_duration
        ).filter(
            models.Visit.project_id == project_id,
            func.split_part(models.Visit.exit_page, '?', 1) == base_url
        ).order_by(desc(models.Visit.visited_at)).all()
        
        result.append({
            "page": base_url,
            "title": title,
            "exits": exits,
            "unique_visitors": ep[2],
            "bounce_rate": exit_rate,  # exit rate
            "total_page_views": total_views,
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
    
    dialect_name = db.bind.dialect.name
    hour_expr = utils.get_truncated_hour_expr(models.PageView.viewed_at, dialect_name)
    
    activity = db.query(
        hour_expr.label('hour'),
        func.count(models.PageView.id).label('views')
    ).join(models.Visit).filter(
        models.Visit.project_id == project_id,
        models.PageView.viewed_at >= time_ago
    ).group_by(
        hour_expr
    ).order_by(hour_expr).all()

    
    return [
        {
            "hour": a[0] if isinstance(a[0], str) else a[0].strftime("%Y-%m-%d %H:%M:%S") if a[0] else None,
            "views": a[1]
        }
        for a in activity
    ]

@router.get("/{project_id}/pages-overview")
def get_pages_overview(project_id: int, limit: int = 10, db: Session = Depends(get_db)):
    """Get all pages data (Activity, Entry, Exit) in one call for Pages View"""
    
    # 1. Most Visited
    most_visited = get_most_visited_pages(project_id, limit, db)
    
    # 2. Entry Pages
    entry_pages = get_entry_pages(project_id, limit, db)
    
    # 3. Exit Pages
    exit_pages = get_exit_pages(project_id, limit, db)
    
    return {
        "most_visited": most_visited,
        "entry_pages": entry_pages,
        "exit_pages": exit_pages
    }