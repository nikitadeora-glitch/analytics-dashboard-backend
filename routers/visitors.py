from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from database import get_db
import models
from datetime import datetime, timedelta
import utils

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

@router.get("/{project_id}/activity-view")
def get_visitor_activity_view(project_id: int, limit: int = 50, db: Session = Depends(get_db)):
    """Dedicated endpoint for Visitor Activity Page"""
    # Simply calls the existing logic for now, but provides a unique route for the page
    return get_visitor_activity(project_id, limit, db)

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

@router.get("/{project_id}/debug-data")
def debug_project_data(project_id: int, db: Session = Depends(get_db)):
    """Debug endpoint to check what data exists"""
    # Check all projects
    all_projects = db.query(models.Visit.project_id).distinct().all()
    
    # Check data for this specific project
    total_visits = db.query(models.Visit).filter(models.Visit.project_id == project_id).count()
    
    # Get sample visits
    sample_visits = db.query(models.Visit).filter(models.Visit.project_id == project_id).limit(5).all()
    
    # Get all unique entry pages
    entry_pages = db.query(models.Visit.entry_page).filter(
        models.Visit.project_id == project_id,
        models.Visit.entry_page.isnot(None)
    ).distinct().all()
    
    return {
        "all_project_ids": [p[0] for p in all_projects],
        "requested_project_id": project_id,
        "total_visits_in_project": total_visits,
        "sample_visits": [
            {
                "id": v.id,
                "visitor_id": v.visitor_id,
                "entry_page": v.entry_page,
                "visited_at": str(v.visited_at)
            } for v in sample_visits
        ],
        "all_entry_pages": [ep[0] for ep in entry_pages if ep[0]]
    }

@router.get("/{project_id}/by-page")
def get_visitors_by_page(project_id: int, page_url: str, db: Session = Depends(get_db)):
    # Debug: First check if we have any visits for this project
    total_visits = db.query(models.Visit).filter(models.Visit.project_id == project_id).count()
    print(f"DEBUG: Total visits for project {project_id}: {total_visits}")
    
    # Debug: Check what entry_pages exist
    entry_pages = db.query(models.Visit.entry_page).filter(models.Visit.project_id == project_id).distinct().all()
    print(f"DEBUG: Available entry pages: {[ep[0] for ep in entry_pages]}")
    print(f"DEBUG: Looking for page_url: '{page_url}'")
    
    # Try exact match first
    exact_visits = db.query(models.Visit).filter(
        models.Visit.project_id == project_id,
        models.Visit.entry_page == page_url
    ).all()
    print(f"DEBUG: Exact match results: {len(exact_visits)}")
    
    # Try ILIKE match
    visits = db.query(models.Visit).filter(
        models.Visit.project_id == project_id,
        models.Visit.entry_page.ilike(f"%{page_url}%")
    ).all()
    print(f"DEBUG: ILIKE match results: {len(visits)}")

    return {
        "debug_info": {
            "total_visits_in_project": total_visits,
            "available_entry_pages": [ep[0] for ep in entry_pages],
            "search_term": page_url,
            "exact_matches": len(exact_visits),
            "ilike_matches": len(visits)
        },
        "visitors": [
            {
                "visitor_id": v.visitor_id,
                "country": v.country,
                "city": v.city,
                "device": v.device,
                "browser": v.browser,
                "last_visit": v.visited_at,
                "entry_page": v.entry_page
            }
            for v in visits
        ]
    }


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

@router.get("/{project_id}/map-view")
def get_map_view(
    project_id: int, 
    days: int = 30, 
    db: Session = Depends(get_db)
):
    """
    Dedicated endpoint for Visitor Map Page.
    Supports filtering by days and returns aggregated location data.
    """
    start_date_ist = utils.get_ist_start_of_day(days - 1)
    start_date_utc = utils.ist_to_utc(start_date_ist)
    
    locations = db.query(
        models.Visit.country,
        models.Visit.state,
        models.Visit.city,
        models.Visit.latitude,
        models.Visit.longitude,
        func.count(models.Visit.id).label('count')
    ).filter(
        models.Visit.project_id == project_id,
        models.Visit.latitude.isnot(None),
        models.Visit.visited_at >= start_date_utc
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

@router.get("/{project_id}/visitors-at-location")
def get_visitors_at_location(
    project_id: int,
    lat: float,
    lng: float,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """
    Fetch detailed visitor info for a specific map pin (location).
    Results are ordered by most recent visit.
    """
    start_date_ist = utils.get_ist_start_of_day(days - 1)
    start_date_utc = utils.ist_to_utc(start_date_ist)
    
    # Use strict float matching since we pass back values we got from the DB.
    # In production, a small epsilon correlation might be safer.
    visits = db.query(models.Visit).filter(
        models.Visit.project_id == project_id,
        models.Visit.latitude == lat,
        models.Visit.longitude == lng,
        models.Visit.visited_at >= start_date_utc
    ).order_by(desc(models.Visit.visited_at)).limit(50).all()
    
    result = []
    for v in visits:
        # Count returning visits
        returning_count = db.query(models.Visit).filter(
            models.Visit.project_id == project_id,
            models.Visit.visitor_id == v.visitor_id
        ).count()
        
        result.append({
            "visitor_id": v.visitor_id,
            "ip_address": v.ip_address,
            "isp": v.isp,
            "visited_at": v.visited_at,
            "session_duration": v.session_duration,
            "browser": v.browser,
            "os": v.os,
            "screen_resolution": v.screen_resolution,
            "city": v.city,
            "state": v.state,
            "country": v.country,
            "returning_visits": returning_count,
            "entry_page": v.entry_page,
            "exit_page": v.exit_page,
            "referrer": v.referrer
        })
    
    return result

@router.post("/{project_id}/bulk-sessions")
def get_bulk_visitor_sessions(project_id: int, visitor_ids: list[str], db: Session = Depends(get_db)):
    """OPTIMIZED: Get sessions for multiple visitors in a single request"""
    if not visitor_ids or len(visitor_ids) == 0:
        return {}
    
    # Limit to prevent abuse
    visitor_ids = visitor_ids[:10]
    
    # Get all visits for these visitors in one query
    visits = db.query(models.Visit).filter(
        models.Visit.project_id == project_id,
        models.Visit.visitor_id.in_(visitor_ids)
    ).order_by(desc(models.Visit.visited_at)).all()
    
    # Get all page views for these visits in one query
    visit_ids = [v.id for v in visits]
    page_views = db.query(models.PageView).filter(
        models.PageView.visit_id.in_(visit_ids)
    ).order_by(models.PageView.viewed_at).all()
    
    # Group page views by visit_id
    page_views_by_visit = {}
    for pv in page_views:
        if pv.visit_id not in page_views_by_visit:
            page_views_by_visit[pv.visit_id] = []
        page_views_by_visit[pv.visit_id].append({
            "url": pv.url,
            "title": pv.title,
            "time_spent": pv.time_spent,
            "viewed_at": pv.viewed_at
        })
    
    # Group visits by visitor_id
    result = {}
    for visit in visits:
        visitor_id = visit.visitor_id
        if visitor_id not in result:
            result[visitor_id] = {
                "visitor_id": visitor_id,
                "total_sessions": 0,
                "sessions": []
            }
        
        result[visitor_id]["total_sessions"] += 1
        result[visitor_id]["sessions"].append({
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
            "page_count": len(page_views_by_visit.get(visit.id, [])),
            "page_journey": page_views_by_visit.get(visit.id, [])
        })
    
    return result
