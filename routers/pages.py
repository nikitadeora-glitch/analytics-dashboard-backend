from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from database import get_db
import models
import utils
from datetime import datetime, time
from typing import Optional
import pytz
from functools import lru_cache

router = APIRouter()

IST = pytz.timezone("Asia/Kolkata")

# Simple in-memory cache for frequently accessed data
_cache = {}
_cache_timeout = 300  # 5 minutes

def get_cached_or_compute(cache_key, compute_func, *args, **kwargs):
    """Simple caching mechanism"""
    import time
    current_time = time.time()
    
    if cache_key in _cache:
        cached_data, timestamp = _cache[cache_key]
        if current_time - timestamp < _cache_timeout:
            return cached_data
    
    # Compute new data
    result = compute_func(*args, **kwargs)
    _cache[cache_key] = (result, current_time)
    return result




from datetime import datetime, time, timedelta
import pytz

IST = pytz.timezone("Asia/Kolkata")

def normalize_date_range(start_date: str | None, end_date: str | None):
    start_dt = end_dt = None
    
    print(f"🔍 Input dates - Start: {start_date}, End: {end_date}")

    try:
        if start_date:
            if "T" in start_date:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            else:
                start_dt = datetime.combine(
                    datetime.strptime(start_date, "%Y-%m-%d").date(),
                    time.min
                )
                start_dt = IST.localize(start_dt).astimezone(pytz.UTC)
            print(f"🔍 Parsed start_dt (UTC): {start_dt}")

        if end_date:
            if "T" in end_date:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            else:
                end_dt = datetime.combine(
                    datetime.strptime(end_date, "%Y-%m-%d").date(),
                    time.max
                )
                end_dt = IST.localize(end_dt).astimezone(pytz.UTC)
            print(f"🔍 Parsed end_dt (UTC): {end_dt}")

    except Exception as e:
        print(f"❌ Date parsing error: {e}")
        # Return None values if parsing fails
        start_dt = end_dt = None

    return start_dt, end_dt


@router.get("/{project_id}/most-visited")
def get_most_visited_pages(
    project_id: int,
    limit: Optional[int] = 10,  # Default to 10 for chunked loading
    offset: Optional[int] = 0,  # Add offset for pagination
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Optimized most visited pages with chunked loading"""
    try:
        print(f"🔍 Getting most visited pages for project {project_id}")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"📊 Limit: {limit}, Offset: {offset}")

        start_dt, end_dt = normalize_date_range(start_date, end_date)

        base_url_exp = func.split_part(models.PageView.url, '?', 1)

        # Single optimized query with pagination
        query = db.query(
            base_url_exp.label("base_url"),
            func.count(models.PageView.id).label("total_views"),
            func.count(func.distinct(models.PageView.visit_id)).label("unique_sessions"),
            func.avg(models.PageView.time_spent).label("avg_time_spent"),
            func.max(models.PageView.title).label("title")
        ).join(models.Visit).filter(
            models.Visit.project_id == project_id
        )

        if start_dt:
            query = query.filter(models.Visit.visited_at >= start_dt)
        if end_dt:
            query = query.filter(models.Visit.visited_at <= end_dt)

        # Apply pagination
        page_stats = (
            query.group_by(base_url_exp)
            .order_by(desc("total_views"))
            .offset(offset)
            .limit(limit)
            .all()
        )

        result = []
        for base_url, total_views, unique_sessions, avg_time_spent, title in page_stats:
            # Calculate bounce rate for this page
            # Bounce rate = (sessions with only 1 page view / total sessions that viewed this page) * 100
            
            # Get all visits that included this page
            page_views_query = db.query(models.PageView.visit_id).join(models.Visit).filter(
                models.Visit.project_id == project_id,
                func.split_part(models.PageView.url, '?', 1) == base_url
            )
            
            if start_dt:
                page_views_query = page_views_query.filter(models.Visit.visited_at >= start_dt)
            if end_dt:
                page_views_query = page_views_query.filter(models.Visit.visited_at <= end_dt)
            
            # Get unique visit IDs that viewed this page
            visit_ids = [row[0] for row in page_views_query.distinct().all()]
            
            if visit_ids:
                # Count page views per visit for this specific page
                visit_page_counts = db.query(
                    models.PageView.visit_id,
                    func.count(models.PageView.id).label('page_count')
                ).filter(
                    models.PageView.visit_id.in_(visit_ids)
                ).group_by(models.PageView.visit_id).all()
                
                # Purely dynamic calculation based on actual page view data
                visits_with_page_data = {visit_id: count for visit_id, count in visit_page_counts}
                
                # Only count visits that have actual page view data
                single_page_visits = sum(1 for visit_id, count in visits_with_page_data.items() if count == 1)
                total_visits_with_data = len(visits_with_page_data)
                
                # Calculate bounce rate only from visits with page view data
                bounce_rate = (single_page_visits / total_visits_with_data * 100) if total_visits_with_data > 0 else 0.0
                
                print(f"📊 Most Visited Bounce Rate for {base_url}: {single_page_visits}/{total_visits_with_data} = {bounce_rate:.1f}%")
                print(f"🔍 Visits with page data: {total_visits_with_data}, Total visits: {len(visit_ids)}")
            else:
                bounce_rate = 0.0
            
            # Get actual visits for this page - chunked approach
            visits_for_page = []
            page_visits = db.query(models.Visit).join(models.PageView).filter(
                models.Visit.project_id == project_id,
                func.split_part(models.PageView.url, '?', 1) == base_url
            )
            
            if start_dt:
                page_visits = page_visits.filter(models.Visit.visited_at >= start_dt)
            if end_dt:
                page_visits = page_visits.filter(models.Visit.visited_at <= end_dt)
            
            # Get ALL visits for this page (no limit - show complete data)
            visits_data = page_visits.order_by(desc(models.Visit.visited_at)).all()
            
            for visit in visits_data:
                visit_data = {
                    "session_id": visit.session_id,  # This is the session string ID
                    "visitor_id": visit.visitor_id,
                    "visited_at": visit.visited_at.isoformat() if visit.visited_at else None,
                    "time_spent": visit.session_duration or 0,
                    "country": visit.country,
                    "city": visit.city,
                    "device": visit.device,
                    "browser": visit.browser,
                    "os": visit.os,
                    "ip_address": visit.ip_address
                }
                visits_for_page.append(visit_data)
            
            print(f"📊 Most Visited - Found {len(visits_for_page)} visits for page: {base_url} (Bounce Rate: {bounce_rate:.1f}%)")
            
            result.append({
                "url": base_url,
                "title": title or base_url,
                "total_views": total_views,
                "unique_views": unique_sessions,
                "avg_time_spent": avg_time_spent or 0,
                "bounce_rate": round(bounce_rate, 1),  # Proper bounce rate calculation
                "visits": visits_for_page
            })

        print(f"✅ Returning {len(result)} pages")
        return {
            "data": result,
            "has_more": len(result) == limit,  # If we got full limit, there might be more
            "total_loaded": offset + len(result)
        }

    except Exception as e:
        print(f"❌ Error in get_most_visited_pages: {e}")
        import traceback
        traceback.print_exc()
        # Return empty result instead of raising error
        return {
            "data": [],
            "has_more": False,
            "total_loaded": 0
        }



@router.get("/{project_id}/entry-pages")
def get_entry_pages(
    project_id: int,
    limit: Optional[int] = 10,  # Default to 10 for chunked loading
    offset: Optional[int] = 0,  # Add offset for pagination
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Optimized entry pages with chunked loading"""
    try:
        print(f"🔍 Getting entry pages for project {project_id}")
        print(f"📅 Date range: {start_date} to {end_date}")

        start_dt, end_dt = normalize_date_range(start_date, end_date)

        base_url_exp = func.split_part(models.Visit.entry_page, '?', 1)

        # Single optimized query with pagination
        query = db.query(
            base_url_exp.label("entry_page"),
            func.count(models.Visit.id).label("sessions"),
            func.count(func.distinct(models.Visit.visitor_id)).label("unique_visitors")
        ).filter(
            models.Visit.project_id == project_id,
            models.Visit.entry_page.isnot(None)
        )

        if start_dt:
            query = query.filter(models.Visit.visited_at >= start_dt)
        if end_dt:
            query = query.filter(models.Visit.visited_at <= end_dt)

        # Apply pagination
        entry_pages = (
            query.group_by(base_url_exp)
            .order_by(desc("sessions"))
            .offset(offset)
            .limit(limit)
            .all()
        )

        result = []
        for base_url, sessions, unique_visitors in entry_pages:
            # Calculate bounce rate for entry pages
            # For entry pages, bounce rate = sessions where visitor only viewed 1 page
            
            # Get all visits that started from this entry page
            entry_visits_query = db.query(models.Visit.id).filter(
                models.Visit.project_id == project_id,
                func.split_part(models.Visit.entry_page, '?', 1) == base_url
            )
            
            if start_dt:
                entry_visits_query = entry_visits_query.filter(models.Visit.visited_at >= start_dt)
            if end_dt:
                entry_visits_query = entry_visits_query.filter(models.Visit.visited_at <= end_dt)
            
            # Get visit IDs for this entry page
            visit_ids = [row[0] for row in entry_visits_query.all()]
            
            if visit_ids:
                # Count page views per visit for entry pages
                visit_page_counts = db.query(
                    models.PageView.visit_id,
                    func.count(models.PageView.id).label('page_count')
                ).filter(
                    models.PageView.visit_id.in_(visit_ids)
                ).group_by(models.PageView.visit_id).all()
                
                # Purely dynamic calculation based on actual page view data
                visits_with_page_data = {visit_id: count for visit_id, count in visit_page_counts}
                
                # Only count visits that have actual page view data
                single_page_visits = sum(1 for visit_id, count in visits_with_page_data.items() if count == 1)
                total_visits_with_data = len(visits_with_page_data)
                
                # Calculate bounce rate only from visits with page view data
                bounce_rate = (single_page_visits / total_visits_with_data * 100) if total_visits_with_data > 0 else 0.0
                
                print(f"📊 Entry Page Bounce Rate for {base_url}: {single_page_visits}/{total_visits_with_data} = {bounce_rate:.1f}%")
                print(f"🔍 Visits with page data: {total_visits_with_data}, Total visits: {len(visit_ids)}")
            else:
                bounce_rate = 0.0
            
            # Get actual visits for this entry page - chunked approach
            visits_for_page = []
            entry_visits = db.query(models.Visit).filter(
                models.Visit.project_id == project_id,
                func.split_part(models.Visit.entry_page, '?', 1) == base_url
            )
            
            if start_dt:
                entry_visits = entry_visits.filter(models.Visit.visited_at >= start_dt)
            if end_dt:
                entry_visits = entry_visits.filter(models.Visit.visited_at <= end_dt)
            
            # Get ALL visits for this entry page (no limit - show complete data)
            visits_data = entry_visits.order_by(desc(models.Visit.visited_at)).all()
            
            for visit in visits_data:
                visits_for_page.append({
                    "session_id": visit.session_id,  # This is the session string ID
                    "visitor_id": visit.visitor_id,
                    "visited_at": visit.visited_at.isoformat() if visit.visited_at else None,
                    "time_spent": visit.session_duration or 0,
                    "country": visit.country,
                    "city": visit.city,
                    "device": visit.device,
                    "browser": visit.browser,
                    "os": visit.os,
                    "ip_address": visit.ip_address
                })
            
            result.append({
                "page": base_url,
                "title": base_url,
                "sessions": sessions,
                "unique_visitors": unique_visitors,
                "bounce_rate": round(bounce_rate, 1),  # Proper bounce rate calculation
                "total_page_views": sessions,
                "visits": visits_for_page
            })

        print(f"✅ Returning {len(result)} entry pages")
        return {
            "data": result,
            "has_more": len(result) == limit,
            "total_loaded": offset + len(result)
        }

    except Exception as e:
        print(f"❌ Error in get_entry_pages: {e}")
        import traceback
        traceback.print_exc()
        return {
            "data": [],
            "has_more": False,
            "total_loaded": 0
        }

@router.get("/{project_id}/exit-pages")
def get_exit_pages(
    project_id: int,
    limit: Optional[int] = 10,  # Default to 10 for chunked loading
    offset: Optional[int] = 0,  # Add offset for pagination
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Optimized exit pages with chunked loading - calculated from last page view in each session"""
    try:
        print(f"🔍 Getting exit pages for project {project_id}")
        print(f"📅 Date range: {start_date} to {end_date}")

        start_dt, end_dt = normalize_date_range(start_date, end_date)

        # First check if there are any page views at all
        total_page_views = db.query(models.PageView).join(models.Visit).filter(
            models.Visit.project_id == project_id
        ).count()
        print(f"📊 Total page views for project {project_id}: {total_page_views}")

        if total_page_views == 0:
            print("❌ No page views found for this project")
            return {"data": [], "has_more": False, "total_loaded": 0}

        # Get the last page view for each session (this is the exit page)
        last_page_views_subquery = db.query(
            models.PageView.visit_id,
            func.max(models.PageView.viewed_at).label('last_viewed_at')
        ).join(models.Visit).filter(
            models.Visit.project_id == project_id
        )

        if start_dt:
            last_page_views_subquery = last_page_views_subquery.filter(models.Visit.visited_at >= start_dt)
        if end_dt:
            last_page_views_subquery = last_page_views_subquery.filter(models.Visit.visited_at <= end_dt)

        # Check how many unique visits we have
        unique_visits = db.query(models.PageView.visit_id).join(models.Visit).filter(
            models.Visit.project_id == project_id
        ).distinct().count()
        print(f"📊 Unique visits (sessions): {unique_visits}")

        last_page_views_subquery = last_page_views_subquery.group_by(models.PageView.visit_id).subquery()

        # Get the actual exit pages from the last page views
        exit_pages_query = db.query(
            func.split_part(models.PageView.url, '?', 1).label("exit_page"),
            func.count(models.PageView.visit_id).label("exits"),
            func.count(func.distinct(models.Visit.visitor_id)).label("unique_visitors")
        ).join(models.Visit).join(
            last_page_views_subquery,
            and_(
                models.PageView.visit_id == last_page_views_subquery.c.visit_id,
                models.PageView.viewed_at == last_page_views_subquery.c.last_viewed_at
            )
        ).filter(
            models.Visit.project_id == project_id
        )

        if start_dt:
            exit_pages_query = exit_pages_query.filter(models.Visit.visited_at >= start_dt)
        if end_dt:
            exit_pages_query = exit_pages_query.filter(models.Visit.visited_at <= end_dt)

        # Apply pagination
        exit_pages = (
            exit_pages_query.group_by(func.split_part(models.PageView.url, '?', 1))
            .order_by(desc("exits"))
            .offset(offset)
            .limit(limit)
            .all()
        )

        result = []
        for base_url, exits, unique_visitors in exit_pages:
            # Calculate exit rate for exit pages
            # Exit rate = (sessions that exited from this page / sessions that viewed this page) * 100
            
            # Get all visits that viewed this page (for denominator)
            page_visits_query = db.query(models.Visit.id).join(models.PageView).filter(
                models.Visit.project_id == project_id,
                func.split_part(models.PageView.url, '?', 1) == base_url
            )
            
            if start_dt:
                page_visits_query = page_visits_query.filter(models.Visit.visited_at >= start_dt)
            if end_dt:
                page_visits_query = page_visits_query.filter(models.Visit.visited_at <= end_dt)
            
            total_page_visits = page_visits_query.distinct().count()
            
            # Calculate exit rate
            exit_rate = (exits / total_page_visits * 100) if total_page_visits > 0 else 0.0
            
            # Calculate bounce rate for exit pages
            # Bounce rate = (sessions with only 1 page view / total sessions that viewed this page) * 100
            
            # Get all visit IDs that viewed this page
            page_visit_ids = [row[0] for row in page_visits_query.distinct().all()]
            
            if page_visit_ids:
                # Count page views per visit for this page
                visit_page_counts = db.query(
                    models.PageView.visit_id,
                    func.count(models.PageView.id).label('page_count')
                ).filter(
                    models.PageView.visit_id.in_(page_visit_ids)
                ).group_by(models.PageView.visit_id).all()
                
                # Purely dynamic calculation based on actual page view data
                visits_with_page_data = {visit_id: count for visit_id, count in visit_page_counts}
                
                # Only count visits that have actual page view data
                single_page_visits = sum(1 for visit_id, count in visits_with_page_data.items() if count == 1)
                total_visits_with_data = len(visits_with_page_data)
                
                # Calculate bounce rate only from visits with page view data
                bounce_rate = (single_page_visits / total_visits_with_data * 100) if total_visits_with_data > 0 else 0.0
                
                print(f"📊 Exit Page Bounce Rate for {base_url}: {single_page_visits}/{total_visits_with_data} = {bounce_rate:.1f}%")
                print(f"🔍 Visits with page data: {total_visits_with_data}, Total visits: {len(page_visit_ids)}")
            else:
                bounce_rate = 0.0
            
            # Get actual visits for this exit page - get visits where this was the last page
            visits_for_page = []
            
            # Get visits that exited from this page (where this was the last page viewed)
            exit_visits_subquery = db.query(
                models.PageView.visit_id,
                func.max(models.PageView.viewed_at).label('last_viewed_at')
            ).join(models.Visit).filter(
                models.Visit.project_id == project_id,
                func.split_part(models.PageView.url, '?', 1) == base_url
            ).group_by(models.PageView.visit_id).subquery()
            
            exit_visits = db.query(models.Visit).join(
                models.PageView,
                models.Visit.id == models.PageView.visit_id
            ).join(
                exit_visits_subquery,
                and_(
                    models.PageView.visit_id == exit_visits_subquery.c.visit_id,
                    models.PageView.viewed_at == exit_visits_subquery.c.last_viewed_at
                )
            ).filter(
                models.Visit.project_id == project_id,
                func.split_part(models.PageView.url, '?', 1) == base_url
            )
            
            if start_dt:
                exit_visits = exit_visits.filter(models.Visit.visited_at >= start_dt)
            if end_dt:
                exit_visits = exit_visits.filter(models.Visit.visited_at <= end_dt)
            
            # Get ALL visits for this exit page (no limit - show complete data)
            visits_data = exit_visits.order_by(desc(models.Visit.visited_at)).all()
            
            for visit in visits_data:
                visits_for_page.append({
                    "session_id": visit.session_id,  # This is the session string ID
                    "visitor_id": visit.visitor_id,
                    "visited_at": visit.visited_at.isoformat() if visit.visited_at else None,
                    "time_spent": visit.session_duration or 0,
                    "country": visit.country,
                    "city": visit.city,
                    "device": visit.device,
                    "browser": visit.browser,
                    "os": visit.os,
                    "ip_address": visit.ip_address
                })
            
            result.append({
                "page": base_url,
                "title": base_url,
                "exits": exits,
                "unique_visitors": unique_visitors,
                "exit_rate": round(exit_rate, 1),  # Proper exit rate calculation
                "bounce_rate": round(bounce_rate, 1),  # Proper bounce rate calculation
                "total_page_views": exits,
                "visits": visits_for_page
            })

        print(f"✅ Returning {len(result)} exit pages")
        return {
            "data": result,
            "has_more": len(result) == limit,
            "total_loaded": offset + len(result)
        }

    except Exception as e:
        print(f"❌ Error in get_exit_pages: {e}")
        import traceback
        traceback.print_exc()
        return {
            "data": [],
            "has_more": False,
            "total_loaded": 0
        }


@router.get("/{project_id}/page-activity")
def get_page_activity(
    project_id: int,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    from datetime import datetime, timedelta
    import pytz

    IST = pytz.timezone("Asia/Kolkata")

    # IST now → UTC
    ist_now = IST.localize(datetime.now())
    utc_now = ist_now.astimezone(pytz.UTC)

    time_ago = utc_now - timedelta(hours=hours)

    dialect_name = db.bind.dialect.name
    hour_expr = utils.get_truncated_hour_expr(
        models.PageView.viewed_at,
        dialect_name
    )

    activity = (
        db.query(
            hour_expr.label("hour"),
            func.count(models.PageView.id).label("views")
        )
        .join(models.Visit)
        .filter(
            models.Visit.project_id == project_id,
            models.PageView.viewed_at >= time_ago
        )
        .group_by(hour_expr)
        .order_by(hour_expr)
        .all()
    )

    return [
        {
            "hour": (
                h.strftime("%Y-%m-%d %H:%M:%S")
                if hasattr(h, "strftime") else h
            ),
            "views": views
        }
        for h, views in activity
    ]


@router.get("/{project_id}/pages-overview")
def get_pages_overview(
    project_id: int,
    limit: int = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Pages overview (Most visited, Entry pages, Exit pages)
    """

    most_visited = get_most_visited_pages(
        project_id=project_id,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        db=db
    )

    entry_pages = get_entry_pages(
        project_id=project_id,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        db=db
    )

    exit_pages = get_exit_pages(
        project_id=project_id,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        db=db
    )

    return {
        "most_visited": most_visited,
        "entry_pages": entry_pages,
        "exit_pages": exit_pages
    }
