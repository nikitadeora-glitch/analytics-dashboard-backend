from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from database import get_db
import models
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/{project_id}/activity")
def get_visitor_activity(project_id: int, limit: int = 50, db: Session = Depends(get_db)):
    visits = db.query(models.Visit).filter(
        models.Visit.project_id == project_id
    ).order_by(desc(models.Visit.visited_at)).limit(limit).all()
    
    result = []
    for v in visits:
        # Get all page views for this visit (ordered by time)
        page_views = db.query(models.PageView).filter(
            models.PageView.visit_id == v.id
        ).order_by(models.PageView.viewed_at).all()
        
        page_views_count = len(page_views)
        
        # Count total sessions for this visitor
        total_sessions = db.query(models.Visit).filter(
            models.Visit.project_id == project_id,
            models.Visit.visitor_id == v.visitor_id
        ).count()
        
        # Build page views list
        page_views_list = [{
            "url": pv.url,
            "title": pv.title,
            "time_spent": pv.time_spent,
            "viewed_at": pv.viewed_at
        } for pv in page_views]
        
        result.append({
            "id": v.id,
            "visitor_id": v.visitor_id,
            "ip_address": v.ip_address,
            "country": v.country,
            "state": v.state,
            "city": v.city,
            "isp": v.isp,
            "device": v.device,
            "browser": v.browser,
            "os": v.os,
            "screen_resolution": v.screen_resolution,
            "language": v.language,
            "timezone": v.timezone,
            "local_time": v.local_time,
            "local_time_formatted": v.local_time_formatted,
            "timezone_offset": v.timezone_offset,
            "referrer": v.referrer,
            "entry_page": v.entry_page,
            "exit_page": v.exit_page,
            "session_duration": v.session_duration,
            "visited_at": v.visited_at,
            "page_views": page_views_count if page_views_count > 0 else 0,
            "page_views_list": page_views_list,
            "total_sessions": total_sessions
        })
    
    return result

@router.get("/{project_id}/path/{visitor_id}")
def get_visitor_path(project_id: int, visitor_id: str, db: Session = Depends(get_db)):
    visit = db.query(models.Visit).filter(
        models.Visit.project_id == project_id,
        models.Visit.visitor_id == visitor_id
    ).first()
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    page_views = db.query(models.PageView).filter(
        models.PageView.visit_id == visit.id
    ).order_by(models.PageView.viewed_at).all()
    
    return {
        "visitor_id": visitor_id,
        "entry_page": visit.entry_page,
        "exit_page": visit.exit_page,
        "path": [{
            "url": pv.url,
            "title": pv.title,
            "time_spent": pv.time_spent,
            "viewed_at": pv.viewed_at
        } for pv in page_views]
    }

@router.get("/{project_id}/visitor-sessions/{visitor_id}")
def get_visitor_all_sessions(project_id: int, visitor_id: str, db: Session = Depends(get_db)):
    """Get all sessions for a specific visitor with complete page journey for each session"""
    # Get all visits/sessions for this visitor
    visits = db.query(models.Visit).filter(
        models.Visit.project_id == project_id,
        models.Visit.visitor_id == visitor_id
    ).order_by(desc(models.Visit.visited_at)).all()
    
    if not visits:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    sessions = []
    for visit in visits:
        # Get all page views for this session
        page_views = db.query(models.PageView).filter(
            models.PageView.visit_id == visit.id
        ).order_by(models.PageView.viewed_at).all()
        
        sessions.append({
            "session_id": visit.id,
            "session_number": visit.session_id,
            "visited_at": visit.visited_at,
            "entry_page": visit.entry_page,
            "exit_page": visit.exit_page,
            "session_duration": visit.session_duration,
            "referrer": visit.referrer,
            "device": visit.device,
            "browser": visit.browser,
            "os": visit.os,
            "country": visit.country,
            "city": visit.city,
            "page_count": len(page_views),
            "page_journey": [{
                "url": pv.url,
                "title": pv.title,
                "time_spent": pv.time_spent,
                "viewed_at": pv.viewed_at
            } for pv in page_views]
        })
    
    return {
        "visitor_id": visitor_id,
        "total_sessions": len(sessions),
        "sessions": sessions
    }

@router.get("/{project_id}/by-page")
def get_visitors_by_page(project_id: int, page_url: str, db: Session = Depends(get_db)):
    """Get all visitors who visited a specific page"""
    # Get all page views for this URL
    page_views = db.query(models.PageView).join(
        models.Visit, models.PageView.visit_id == models.Visit.id
    ).filter(
        models.Visit.project_id == project_id,
        models.PageView.url == page_url
    ).all()
    
    # Get unique visitor IDs
    visitor_ids = list(set([pv.visit.visitor_id for pv in page_views]))
    
    # Get visitor details
    visitors = []
    for visitor_id in visitor_ids:
        visit = db.query(models.Visit).filter(
            models.Visit.project_id == project_id,
            models.Visit.visitor_id == visitor_id
        ).order_by(desc(models.Visit.visited_at)).first()
        
        if visit:
            visitors.append({
                "visitor_id": visitor_id,
                "country": visit.country,
                "city": visit.city,
                "device": visit.device,
                "browser": visit.browser,
                "last_visit": visit.visited_at
            })
    
    return visitors

@router.get("/{project_id}/map")
def get_visitor_map(project_id: int, db: Session = Depends(get_db)):
    locations = db.query(
        models.Visit.country,
        models.Visit.state,
        models.Visit.city,
        models.Visit.latitude,
        models.Visit.longitude,
        func.count(models.Visit.id).label('count')
    ).filter(
        models.Visit.project_id == project_id,
        models.Visit.latitude.isnot(None)
    ).group_by(
        models.Visit.country,
        models.Visit.state,
        models.Visit.city,
        models.Visit.latitude,
        models.Visit.longitude
    ).all()
    
    return [{
        "country": loc[0],
        "state": loc[1],
        "city": loc[2],
        "latitude": loc[3],
        "longitude": loc[4],
        "count": loc[5]
    } for loc in locations]
