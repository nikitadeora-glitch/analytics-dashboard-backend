from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
import models, schemas
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()

@router.get("/{project_id}/summary")
def get_summary(project_id: int, db: Session = Depends(get_db)):
    # Total visits
    total_visits = db.query(models.Visit).filter(models.Visit.project_id == project_id).count()
    
    # Unique visitors
    unique_visitors = db.query(func.count(func.distinct(models.Visit.visitor_id))).filter(
        models.Visit.project_id == project_id
    ).scalar()
    
    # Live visitors (last 5 minutes)
    five_min_ago = datetime.utcnow() - timedelta(minutes=5)
    live_visitors = db.query(func.count(func.distinct(models.Visit.visitor_id))).filter(
        models.Visit.project_id == project_id,
        models.Visit.visited_at >= five_min_ago
    ).scalar()
    
    # Daily stats for last 7 days
    daily_stats = []
    for i in range(6, -1, -1):
        day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        page_views = db.query(models.Visit).filter(
            models.Visit.project_id == project_id,
            models.Visit.visited_at >= day_start,
            models.Visit.visited_at < day_end
        ).count()
        
        unique_visits = db.query(func.count(func.distinct(models.Visit.visitor_id))).filter(
            models.Visit.project_id == project_id,
            models.Visit.visited_at >= day_start,
            models.Visit.visited_at < day_end
        ).scalar() or 0
        
        first_time = db.query(models.Visit).filter(
            models.Visit.project_id == project_id,
            models.Visit.visited_at >= day_start,
            models.Visit.visited_at < day_end,
            models.Visit.is_unique == True
        ).count()
        
        daily_stats.append({
            "date": day_start.strftime("%a, %d %b %Y"),
            "page_views": page_views,
            "unique_visits": unique_visits,
            "first_time_visits": first_time,
            "returning_visits": unique_visits - first_time
        })
    
    # Calculate averages
    total_days = len(daily_stats)
    avg_page_views = sum(d["page_views"] for d in daily_stats) / total_days if total_days > 0 else 0
    avg_unique_visits = sum(d["unique_visits"] for d in daily_stats) / total_days if total_days > 0 else 0
    avg_first_time = sum(d["first_time_visits"] for d in daily_stats) / total_days if total_days > 0 else 0
    avg_returning = sum(d["returning_visits"] for d in daily_stats) / total_days if total_days > 0 else 0
    
    # Top pages
    top_pages = db.query(
        models.Page.url,
        models.Page.title,
        models.Page.total_views
    ).filter(
        models.Page.project_id == project_id
    ).order_by(desc(models.Page.total_views)).limit(5).all()
    
    # Top traffic sources
    top_sources = db.query(
        models.TrafficSource.source_name,
        func.sum(models.TrafficSource.visit_count).label('count')
    ).filter(
        models.TrafficSource.project_id == project_id
    ).group_by(models.TrafficSource.source_name).order_by(desc('count')).limit(5).all()
    
    # Device stats
    device_stats = db.query(
        models.Visit.device,
        func.count(models.Visit.id).label('count')
    ).filter(
        models.Visit.project_id == project_id
    ).group_by(models.Visit.device).all()
    
    return {
        "total_visits": total_visits,
        "unique_visitors": unique_visitors,
        "live_visitors": live_visitors,
        "daily_stats": daily_stats,
        "averages": {
            "page_views": round(avg_page_views, 1),
            "unique_visits": round(avg_unique_visits, 1),
            "first_time_visits": round(avg_first_time, 1),
            "returning_visits": round(avg_returning, 1)
        },
        "top_pages": [{"url": p[0], "title": p[1], "views": p[2]} for p in top_pages],
        "top_sources": [{"source": s[0], "count": s[1]} for s in top_sources],
        "device_stats": {d[0]: d[1] for d in device_stats if d[0]}
    }

@router.get("/test-location/{ip_address}")
def test_location(ip_address: str):
    """Test endpoint to check location detection for any IP"""
    import requests
    
    try:
        response = requests.get(
            f"http://ip-api.com/json/{ip_address}?fields=status,message,country,regionName,city,lat,lon,isp,query", 
            timeout=3
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "ip": ip_address,
                "api_response": data,
                "success": data.get('status') == 'success'
            }
        else:
            return {
                "ip": ip_address,
                "error": f"HTTP {response.status_code}",
                "success": False
            }
    except Exception as e:
        return {
            "ip": ip_address,
            "error": str(e),
            "success": False
        }

@router.post("/{project_id}/pageview/{visit_id}")
def track_pageview(project_id: int, visit_id: int, pageview: schemas.PageViewCreate, db: Session = Depends(get_db)):
    """Track a page view within a visit"""
    
    # Verify visit exists
    visit = db.query(models.Visit).filter(
        models.Visit.id == visit_id,
        models.Visit.project_id == project_id
    ).first()
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    # Get or create page record
    page = db.query(models.Page).filter(
        models.Page.project_id == project_id,
        models.Page.url == pageview.url
    ).first()
    
    if not page:
        page = models.Page(
            project_id=project_id,
            url=pageview.url,
            title=pageview.title,
            total_views=0,
            unique_views=0
        )
        db.add(page)
        db.flush()
    
    # Create page view record
    db_pageview = models.PageView(
        visit_id=visit_id,
        page_id=page.id,
        url=pageview.url,
        title=pageview.title,
        time_spent=pageview.time_spent,
        scroll_depth=pageview.scroll_depth
    )
    db.add(db_pageview)
    
    # Update page stats
    page.total_views += 1
    
    db.commit()
    db.refresh(db_pageview)
    
    return {
        "pageview_id": db_pageview.id,
        "message": "Page view tracked"
    }

@router.post("/{project_id}/exit/{visit_id}")
def track_exit(project_id: int, visit_id: int, exit_data: dict, db: Session = Depends(get_db)):
    """Track exit page and final time spent"""
    
    visit = db.query(models.Visit).filter(
        models.Visit.id == visit_id,
        models.Visit.project_id == project_id
    ).first()
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    # Update exit page
    visit.exit_page = exit_data.get('exit_page')
    
    # Calculate total session duration
    if visit.visited_at:
        session_duration = (datetime.utcnow() - visit.visited_at).total_seconds()
        visit.session_duration = int(session_duration)
    
    db.commit()
    
    return {
        "message": "Exit tracked",
        "session_duration": visit.session_duration
    }

@router.post("/{project_id}/exit-link")
def track_exit_link(project_id: int, link_data: dict, db: Session = Depends(get_db)):
    """Track external link clicks"""
    
    url = link_data.get('url')
    from_page = link_data.get('from_page')
    visitor_id = link_data.get('visitor_id')
    session_id = link_data.get('session_id')
    
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    # Track individual click
    exit_click = models.ExitLinkClick(
        project_id=project_id,
        visitor_id=visitor_id,
        session_id=session_id,
        url=url,
        from_page=from_page,
        clicked_at=datetime.utcnow()
    )
    db.add(exit_click)
    
    # Update aggregated exit link stats
    exit_link = db.query(models.ExitLink).filter(
        models.ExitLink.project_id == project_id,
        models.ExitLink.url == url,
        models.ExitLink.from_page == from_page
    ).first()
    
    if exit_link:
        # Update existing exit link
        exit_link.click_count += 1
        exit_link.last_clicked = datetime.utcnow()
    else:
        # Create new exit link
        exit_link = models.ExitLink(
            project_id=project_id,
            url=url,
            from_page=from_page,
            click_count=1,
            last_clicked=datetime.utcnow()
        )
        db.add(exit_link)
    
    db.commit()
    
    return {
        "message": "Exit link tracked",
        "url": url
    }

@router.post("/{project_id}/track")
def track_visit(project_id: int, visit: schemas.VisitCreate, request: Request, db: Session = Depends(get_db)):
    import requests
    
    # Check if project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get IP address
    ip_address = visit.ip_address or request.client.host
    
    # Skip location lookup for localhost/private IPs
    is_local = ip_address in ['127.0.0.1', 'localhost', '::1'] or ip_address.startswith('192.168.') or ip_address.startswith('10.')
    
    # Fetch location data from IP
    location_data = {}
    if not is_local:
        try:
            # Using ip-api.com (free, no API key needed)
            # Limit: 45 requests per minute
            response = requests.get(
                f"http://ip-api.com/json/{ip_address}?fields=status,message,country,regionName,city,lat,lon,isp,query", 
                timeout=3
            )
            
            print(f"[Location API] IP: {ip_address}, Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"[Location API] Response: {data}")
                
                if data.get('status') == 'success':
                    location_data = {
                        'country': data.get('country'),
                        'state': data.get('regionName'),
                        'city': data.get('city'),
                        'latitude': data.get('lat'),
                        'longitude': data.get('lon'),
                        'isp': data.get('isp')
                    }
                    print(f"[Location API] ✓ Success: {location_data}")
                else:
                    print(f"[Location API] ✗ Failed: {data.get('message', 'Unknown error')}")
            else:
                print(f"[Location API] ✗ HTTP Error: {response.status_code}")
                
        except requests.Timeout:
            print(f"[Location API] ✗ Timeout for IP: {ip_address}")
        except Exception as e:
            print(f"[Location API] ✗ Error: {str(e)}")
    else:
        print(f"[Location API] ⚠ Skipping localhost IP: {ip_address}")
    
    # Check if this session already exists (prevent duplicate tracking)
    if visit.session_id:
        existing_session = db.query(models.Visit).filter(
            models.Visit.project_id == project_id,
            models.Visit.session_id == visit.session_id
        ).first()
        
        if existing_session:
            # Session already tracked, don't create duplicate
            return {
                "visit_id": existing_session.id, 
                "message": "Session already tracked (deduplicated)",
                "is_duplicate": True
            }
    
    # Create visit record
    db_visit = models.Visit(
        project_id=project_id,
        visitor_id=visit.visitor_id,
        session_id=visit.session_id,
        ip_address=ip_address,
        referrer=visit.referrer,
        entry_page=visit.entry_page,
        device=visit.device,
        browser=visit.browser,
        os=visit.os,
        screen_resolution=visit.screen_resolution,
        language=visit.language,
        timezone=visit.timezone,
        local_time=visit.local_time,
        local_time_formatted=visit.local_time_formatted,
        timezone_offset=visit.timezone_offset,
        **location_data
    )
    
    # Check if unique visitor (first time ever)
    existing_visitor = db.query(models.Visit).filter(
        models.Visit.project_id == project_id,
        models.Visit.visitor_id == visit.visitor_id
    ).first()
    db_visit.is_unique = existing_visitor is None
    db_visit.is_new_session = True
    
    db.add(db_visit)
    db.commit()
    db.refresh(db_visit)
    
    # Track traffic source
    if visit.traffic_source and visit.traffic_name:
        # Check if this traffic source already exists
        traffic_source = db.query(models.TrafficSource).filter(
            models.TrafficSource.project_id == project_id,
            models.TrafficSource.source_type == visit.traffic_source,
            models.TrafficSource.source_name == visit.traffic_name
        ).first()
        
        if traffic_source:
            # Update existing traffic source
            traffic_source.visit_count += 1
        else:
            # Create new traffic source
            traffic_source = models.TrafficSource(
                project_id=project_id,
                source_type=visit.traffic_source,
                source_name=visit.traffic_name,
                referrer_url=visit.referrer if visit.referrer != 'direct' else None,
                utm_source=visit.utm_source,
                utm_medium=visit.utm_medium,
                utm_campaign=visit.utm_campaign,
                visit_count=1
            )
            db.add(traffic_source)
        
        db.commit()
    
    return {
        "visit_id": db_visit.id, 
        "message": "Visit tracked",
        "is_duplicate": False,
        "is_unique_visitor": db_visit.is_unique
    }
