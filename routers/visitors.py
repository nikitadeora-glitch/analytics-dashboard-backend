from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from sqlalchemy import desc, func

from database import get_db

import models

from datetime import datetime, timedelta

import utils

from typing import Optional

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from pytz import timezone



router = APIRouter()

security = HTTPBearer(auto_error=False)



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



@router.get("/{project_id}/activity")

def get_visitor_activity(

    project_id: int, 

    limit: int = 1000, 

    db: Session = Depends(get_db),

    current_user: Optional[models.User] = Depends(get_current_user_optional)

):

    """Get visitor activity - if user is authenticated, check ownership, otherwise allow access (for backward compatibility)"""

    # Check if project exists

    project = db.query(models.Project).filter(models.Project.id == project_id).first()

    if not project:

        raise HTTPException(status_code=404, detail="Project not found")

    

    # If user is authenticated, check if they own the project

    if current_user and project.user_id and project.user_id != current_user.id:

        raise HTTPException(status_code=403, detail="Access denied")

    

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

def get_visitor_activity_view(

    project_id: int, 

    start_date: Optional[str] = None,

    end_date: Optional[str] = None,

    limit: Optional[int] = None,

    db: Session = Depends(get_db),

    current_user: Optional[models.User] = Depends(get_current_user_optional)

):

    """Dedicated endpoint for Visitor Activity Page with date filtering"""

    try:

        print(f"🔍 Getting visitor activity view for project {project_id}")

        print(f"📅 Date range: {start_date} to {end_date}")

        print(f"📊 Limit: {limit}")

        

        # Check if project exists

        project = db.query(models.Project).filter(models.Project.id == project_id).first()

        if not project:

            raise HTTPException(status_code=404, detail="Project not found")

        

        # If user is authenticated, check if they own the project

        if current_user and project.user_id and project.user_id != current_user.id:

            raise HTTPException(status_code=403, detail="Access denied")

        

        # Build query with date filtering

        query = db.query(models.Visit).filter(models.Visit.project_id == project_id)

        

        # Apply date filtering if provided

        if start_date and end_date:

            try:

                # Parse dates - handle both YYYY-MM-DD and ISO formats

                if 'T' in start_date:

                    # ISO format with time

                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

                else:

                    # YYYY-MM-DD format - set to start of day in IST

                    ist = timezone('Asia/Kolkata')

                    start_dt = ist.localize(datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0))

                    start_dt = start_dt.astimezone(timezone('UTC'))

                

                if 'T' in end_date:

                    # ISO format with time

                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

                else:

                    # YYYY-MM-DD format - set to end of day in IST

                    ist = timezone('Asia/Kolkata')

                    end_dt = ist.localize(datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59))

                    end_dt = end_dt.astimezone(timezone('UTC'))

                

                print(f"🔍 Backend date filtering: {start_dt} to {end_dt}")

                

                query = query.filter(

                    models.Visit.visited_at >= start_dt,

                    models.Visit.visited_at <= end_dt

                )

            except ValueError as e:

                print(f"❌ Date parsing error: {e}")

                # Continue without date filtering if parsing fails

                pass

        

        # Get all visits filtered by date range - apply limit only if provided

        if limit is not None:

            visits = query.order_by(desc(models.Visit.visited_at)).limit(limit).all()

        else:

            visits = query.order_by(desc(models.Visit.visited_at)).all()

        

        print(f"🔍 Backend: Returning {len(visits)} visits (limit: {limit})")

        

        # Pre-load page views for all visits to avoid N+1 queries

        visit_ids = [v.id for v in visits]

        page_views_map = {}

        if visit_ids:

            page_views = db.query(models.PageView).filter(

                models.PageView.visit_id.in_(visit_ids)

            ).order_by(models.PageView.viewed_at).all()

            

            # Group page views by visit_id

            for pv in page_views:

                if pv.visit_id not in page_views_map:

                    page_views_map[pv.visit_id] = []

                page_views_map[pv.visit_id].append(pv)

        

        # Get session counts for all visitors in one query

        visitor_ids = list(set([v.visitor_id for v in visits]))

        session_counts = {}

        if visitor_ids:

            session_counts_query = db.query(

                models.Visit.visitor_id,

                func.count(models.Visit.id).label('session_count')

            ).filter(

                models.Visit.project_id == project_id,

                models.Visit.visitor_id.in_(visitor_ids)

            ).group_by(models.Visit.visitor_id).all()

            

            for visitor_id, count in session_counts_query:

                session_counts[visitor_id] = count

        

        result = []

        for v in visits:

            page_views = page_views_map.get(v.id, [])

            page_views_count = len(page_views)

            

            # Get session count for this visitor

            total_sessions = session_counts.get(v.visitor_id, 0)

            

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

        

        print(f"✅ Successfully returning {len(result)} visitor records")

        return result



    except HTTPException:

        # Re-raise HTTP exceptions (404, 403, etc.)

        raise

    except Exception as e:

        print(f"❌ Error in get_visitor_activity_view: {e}")

        import traceback

        traceback.print_exc()

        # Return empty list instead of raising error

        return []



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





@router.get("/{project_id}/geographic-data")

def get_geographic_data(

    project_id: int,

    start_date: Optional[str] = None,

    end_date: Optional[str] = None,

    db: Session = Depends(get_db),

    current_user: Optional[models.User] = Depends(get_current_user_optional)

):

    """Get geographic distribution data with date filtering for Reports page"""

    try:

        print(f"🌍 Getting geographic data for project {project_id}")

        print(f"📅 Date range: {start_date} to {end_date}")

        

        # Check if project exists

        project = db.query(models.Project).filter(models.Project.id == project_id).first()

        if not project:

            raise HTTPException(status_code=404, detail="Project not found")

        

        # If user is authenticated, check if they own the project

        if current_user and project.user_id and project.user_id != current_user.id:

            raise HTTPException(status_code=403, detail="Access denied")

        

        # Build query with date filtering

        query = db.query(models.Visit).filter(models.Visit.project_id == project_id)

        

        # Apply date filtering if provided

        if start_date and end_date:

            try:

                # Parse dates - handle both YYYY-MM-DD and ISO formats

                if 'T' in start_date:

                    # ISO format with time

                    start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

                else:

                    # YYYY-MM-DD format - set to start of day in IST

                    ist = timezone('Asia/Kolkata')

                    start_dt = ist.localize(datetime.strptime(start_date, '%Y-%m-%d').replace(hour=0, minute=0, second=0))

                    start_dt = start_dt.astimezone(timezone('UTC'))

                

                if 'T' in end_date:

                    # ISO format with time

                    end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

                else:

                    # YYYY-MM-DD format - set to end of day in IST

                    ist = timezone('Asia/Kolkata')

                    end_dt = ist.localize(datetime.strptime(end_date, '%Y-%m-%d').replace(hour=23, minute=59, second=59))

                    end_dt = end_dt.astimezone(timezone('UTC'))

                

                print(f"🌍 Backend date filtering: {start_dt} to {end_dt}")

                

                query = query.filter(

                    models.Visit.visited_at >= start_dt,

                    models.Visit.visited_at <= end_dt

                )

            except ValueError as e:

                print(f"❌ Date parsing error: {e}")

                # Continue without date filtering if parsing fails

                pass

        

        # Get geographic distribution

        locations = query.filter(

            models.Visit.country.isnot(None)

        ).with_entities(

            models.Visit.country,

            models.Visit.state,

            models.Visit.city,

            func.count(models.Visit.id).label('count')

        ).group_by(

            models.Visit.country,

            models.Visit.state,

            models.Visit.city

        ).order_by(func.count(models.Visit.id).desc()).all()

        

        print(f"🌍 Found {len(locations)} geographic locations")

        

        result = []

        for country, state, city, count in locations:

            result.append({

                "country": country or "Unknown",

                "state": state or "",

                "city": city or "",

                "count": count

            })

        

        print(f"✅ Returning {len(result)} geographic records")

        return result



    except HTTPException:

        # Re-raise HTTP exceptions (404, 403, etc.)

        raise

    except Exception as e:

        print(f"❌ Error in get_geographic_data: {e}")

        import traceback

        traceback.print_exc()

        # Return empty list instead of raising error

        return []

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

    ).order_by(desc(models.Visit.visited_at)).limit(1000).all()

    

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



@router.get("/{project_id}/visitor-detail/{visitor_id}")

def get_visitor_detail(project_id: int, visitor_id: str, db: Session = Depends(get_db)):

    """

    StatCounter-style visitor detail endpoint.

    Returns complete visitor profile with all sessions and navigation paths.

    """

    try:

        print(f"🔍 Getting visitor detail for project {project_id}, visitor {visitor_id}")

        

        # Check if project exists

        project = db.query(models.Project).filter(models.Project.id == project_id).first()

        if not project:

            raise HTTPException(status_code=404, detail="Project not found")

        

        # Get visitor's most recent visit for profile info

        latest_visit = db.query(models.Visit).filter(

            models.Visit.project_id == project_id,

            models.Visit.visitor_id == visitor_id

        ).order_by(desc(models.Visit.visited_at)).first()

        

        if not latest_visit:

            raise HTTPException(status_code=404, detail="Visitor not found")

        

        # Count total sessions for this visitor

        total_sessions = db.query(models.Visit).filter(

            models.Visit.project_id == project_id,

            models.Visit.visitor_id == visitor_id

        ).count()

        

        # Get all sessions for this visitor

        sessions = db.query(models.Visit).filter(

            models.Visit.project_id == project_id,

            models.Visit.visitor_id == visitor_id

        ).order_by(desc(models.Visit.visited_at)).all()

        

        # Get all page views for all sessions

        visit_ids = [s.id for s in sessions]

        page_views_map = {}

        if visit_ids:

            page_views = db.query(models.PageView).filter(

                models.PageView.visit_id.in_(visit_ids)

            ).order_by(models.PageView.viewed_at).all()

            

            for pv in page_views:

                if pv.visit_id not in page_views_map:

                    page_views_map[pv.visit_id] = []

                page_views_map[pv.visit_id].append({

                    "url": pv.url,

                    "title": pv.title,

                    "timestamp": pv.viewed_at.strftime("%H:%M:%S") if pv.viewed_at else "",

                    "viewed_at": pv.viewed_at

                })

        

        # Build sessions response

        sessions_data = []

        for session in sessions:

            session_page_views = page_views_map.get(session.id, [])

            sessions_data.append({

                "session_id": str(session.id),

                "start_time": session.visited_at.isoformat() if session.visited_at else "",

                "duration": session.session_duration or 0,

                "referrer": session.referrer or "",

                "entry_page": session.entry_page or "",

                "exit_page": session.exit_page or "",

                "pageviews": session_page_views

            })

        

        # Build visitor profile

        visitor_profile = {

            "visitor_id": visitor_id,

            "ip": latest_visit.ip_address or "",

            "isp": latest_visit.isp or "",

            "country": latest_visit.country or "",

            "city": latest_visit.city or "",

            "lat": latest_visit.latitude or 0.0,

            "lng": latest_visit.longitude or 0.0,

            "device": latest_visit.device or "",

            "os": latest_visit.os or "",

            "browser": latest_visit.browser or "",

            "resolution": latest_visit.screen_resolution or "",

            "returning_visits": total_sessions - 1,  # Subtract 1 to exclude current session

            "first_seen": latest_visit.visited_at.isoformat() if latest_visit.visited_at else ""

        }

        

        response = {

            "visitor": visitor_profile,

            "sessions": sessions_data

        }

        

        print(f"✅ Successfully returning visitor detail with {len(sessions_data)} sessions")

        return response

        

    except HTTPException:

        raise

    except Exception as e:

        print(f"❌ Error in get_visitor_detail: {e}")

        import traceback

        traceback.print_exc()

        raise HTTPException(status_code=500, detail="Internal server error")



@router.post("/{project_id}/bulk-sessions")

def get_bulk_visitor_sessions(project_id: int, visitor_ids: list[str], db: Session = Depends(get_db)):

    """OPTIMIZED: Get sessions for multiple visitors in a single request"""

    if not visitor_ids or len(visitor_ids) == 0:

        return {}

    

    # Limit to prevent abuse - Removed as per user request for full data

    # visitor_ids = visitor_ids[:100]

    

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