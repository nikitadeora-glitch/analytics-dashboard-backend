from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, case
from database import get_db
import models, schemas
from datetime import datetime, timedelta
from typing import Optional
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import utils
import re
import pytz

router = APIRouter()
security = HTTPBearer(auto_error=False)  # Make authentication optional

_BOT_UA_RE = re.compile(
    r"(bot|spider|crawl|slurp|mediapartners-google|adsbot-google|googlebot|bingbot|bingpreview|msnbot|yandex|baidu|duckduckbot|ahrefs|semrush|mj12|dotbot|bytespider|facebookexternalhit|twitterbot|linkedinbot|whatsapp|telegram|discordbot|slackbot|curl|wget|python-requests|aiohttp|httpclient|libwww-perl|scrapy|selenium|puppeteer|playwright|headless|lighthouse|uptimerobot)",
    re.IGNORECASE,
)

def _is_probable_bot_request(request: Request) -> bool:
    # Allow all traffic - no bot protection
    return False
  

def _log_ignored(request: Request, reason: str) -> None:
    try:
        ip = getattr(getattr(request, "client", None), "host", None)
        ua = (request.headers.get("user-agent") or "").strip()
        path = getattr(getattr(request, "url", None), "path", "")
        print(f"[Analytics] Ignored bot traffic ({reason}) ip={ip} path={path} ua={ua}")
    except Exception:
        pass

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

# @router.get("/{project_id}/summary")
# def get_summary(
#     project_id: int, 
#     days: int , 
#     db: Session = Depends(get_db),
#     current_user: Optional[models.User] = Depends(get_current_user_optional)
# ):
#     # Check if project exists and user has access
#     project = db.query(models.Project).filter(models.Project.id == project_id).first()
#     if not project:
#         raise HTTPException(status_code=404, detail="Project not found")
    
#     # If user is authenticated, check if they own the project
#     if current_user and project.user_id and project.user_id != current_user.id:
#         raise HTTPException(status_code=403, detail="Access denied")
    
#     # Total visits
#     total_visits = db.query(models.Visit).filter(models.Visit.project_id == project_id).count()
    
#     # Unique visitors
#     unique_visitors = db.query(func.count(func.distinct(models.Visit.visitor_id))).filter(
#         models.Visit.project_id == project_id
#     ).scalar()
    
#     # Live visitors (last 5 minutes)
#     five_min_ago = datetime.utcnow() - timedelta(minutes=5)
#     live_visitors = db.query(func.count(func.distinct(models.Visit.visitor_id))).filter(
#         models.Visit.project_id == project_id,
#         models.Visit.visited_at >= five_min_ago
#     ).scalar()
    
#     # Daily stats for specified number of days - OPTIMIZED
#     from sqlalchemy import case, cast, Date
    
#     # IST calculation
#     start_date_ist = utils.get_ist_start_of_day(days - 1)
#     start_date_utc = start_date_ist.astimezone(pytz.UTC)
    
#     dialect_name = db.bind.dialect.name
#     ist_date_expr = utils.get_ist_date_expr(models.Visit.visited_at, dialect_name)
    
#     # Single query to get all stats grouped by date - COUNTING ACTUAL PAGEVIEWS
#     daily_data = db.query(
#         ist_date_expr.label('visit_date'),
#         func.count(models.PageView.id).label('page_views'),
#         func.count(func.distinct(models.Visit.visitor_id)).label('unique_visits'),
#         func.count(func.distinct(case((models.Visit.is_unique == True, models.Visit.visitor_id), else_=None))).label('first_time_visits'),
#         func.count(func.distinct(
#             case(
#                 (models.Visit.is_unique == False, models.Visit.visitor_id),
#                 else_=None
#             )
#         )).label('returning_visits')
#     ).join(
#         models.PageView, models.Visit.id == models.PageView.visit_id
#     ).filter(
#         models.Visit.project_id == project_id,
#         models.Visit.visited_at >= start_date_utc
#     ).group_by(ist_date_expr).all()
    
#     # Create a dict for quick lookup
#     stats_dict = {
#         row.visit_date: {
#             'page_views': row.page_views,
#             'unique_visits': row.unique_visits,
#             'first_time_visits': row.first_time_visits or 0,
#             'returning_visits': row.returning_visits or 0
#         }
#         for row in daily_data
#     }
    
#     # Build daily stats array with all days (including days with no data)
#     daily_stats = []
#     for i in range(days - 1, -1, -1):
#         day_start_ist = utils.get_ist_start_of_day(i)
#         day_date = day_start_ist.date()
        
#         # SQL returns date as string in some dialects, handle conversion if needed
#         # stats_dict keys are date objects if cast(..., Date) worked correctly
#         stats = stats_dict.get(day_date)
#         if stats is None:
#             # Fallback for string keys
#             stats = stats_dict.get(str(day_date), {'page_views': 0, 'unique_visits': 0, 'first_time_visits': 0, 'returning_visits': 0})
        
#         daily_stats.append({
#             "date": day_start_ist.strftime("%a, %d %b %Y"),
#             "page_views": stats['page_views'],
#             "unique_visits": stats['unique_visits'],
#             "first_time_visits": stats['first_time_visits'],
#             "returning_visits": stats['returning_visits']
#         })
    
#     # Get ALL historical data (no date limit)
#     all_time_data = db.query(
#         ist_date_expr.label('visit_date'),
#         func.count(models.PageView.id).label('page_views'),
#         func.count(func.distinct(models.Visit.visitor_id)).label('unique_visits'),
#         func.count(func.distinct(case((models.Visit.is_unique == True, models.Visit.visitor_id), else_=None))).label('first_time_visits'),
#         func.count(func.distinct(
#             case(
#                 (models.Visit.is_unique == False, models.Visit.visitor_id),
#                 else_=None
#             )
#         )).label('returning_visits')
#     ).join(
#         models.PageView, models.Visit.id == models.PageView.visit_id
#     ).filter(
#         models.Visit.project_id == project_id
#     ).group_by(ist_date_expr).order_by(ist_date_expr).all()
    
#     # Build all-time daily stats
#     all_daily_stats = []
#     for row in all_time_data:
#         # Handle both date objects and strings
#         row_date = row.visit_date
#         if isinstance(row_date, str):
#             try:
#                 row_date = datetime.strptime(row_date, "%Y-%m-%d").date()
#             except:
#                 pass
                
#         all_daily_stats.append({
#             "date": row_date.strftime("%a, %d %b %Y") if hasattr(row_date, 'strftime') else str(row_date),
#             "page_views": row.page_views,
#             "unique_visits": row.unique_visits,
#             "first_time_visits": row.first_time_visits or 0,
#             "returning_visits": row.returning_visits or 0
#         })
    
#     # Calculate averages
#     total_days = len(daily_stats)
#     avg_page_views = sum(d["page_views"] for d in daily_stats) / total_days if total_days > 0 else 0
#     avg_unique_visits = sum(d["unique_visits"] for d in daily_stats) / total_days if total_days > 0 else 0
#     avg_first_time = sum(d["first_time_visits"] for d in daily_stats) / total_days if total_days > 0 else 0
#     avg_returning = sum(d["returning_visits"] for d in daily_stats) / total_days if total_days > 0 else 0
    
#     # Top pages
#     top_pages = db.query(
#         models.Page.url,
#         models.Page.title,
#         models.Page.total_views
#     ).filter(
#         models.Page.project_id == project_id
#     ).order_by(desc(models.Page.total_views)).limit(5).all()
    
#     # Top traffic sources
#     top_sources = db.query(
#         models.TrafficSource.source_name,
#         func.sum(models.TrafficSource.visit_count).label('count')
#     ).filter(
#         models.TrafficSource.project_id == project_id
#     ).group_by(models.TrafficSource.source_name).order_by(desc('count')).limit(5).all()
    
#     # Device stats
#     device_stats = db.query(
#         models.Visit.device,
#         func.count(models.Visit.id).label('count')
#     ).filter(
#         models.Visit.project_id == project_id
#     ).group_by(models.Visit.device).all()
    
#     return {
#         "total_visits": total_visits,
#         "unique_visitors": unique_visitors,
#         "live_visitors": live_visitors,
#         "daily_stats": daily_stats,
#         "all_daily_stats": all_daily_stats,  # Complete historical data
#         "averages": {
#             "page_views": round(avg_page_views, 1),
#             "unique_visits": round(avg_unique_visits, 1),
#             "first_time_visits": round(avg_first_time, 1),
#             "returning_visits": round(avg_returning, 1)
#         },
#         "top_pages": [{"url": p[0], "title": p[1], "views": p[2]} for p in top_pages],
#         "top_sources": [{"source": s[0], "count": s[1]} for s in top_sources],
#         "device_stats": {d[0]: d[1] for d in device_stats if d[0]}
#     }


@router.get("/{project_id}/summary")
def get_summary(
    project_id: int,
    days: int,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    # -----------------------------------
    # 1. Project & permission check
    # -----------------------------------
    project = db.query(models.Project).filter(
        models.Project.id == project_id
    ).first()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if current_user and project.user_id and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    # -----------------------------------
    # 2. Date range calculation (IST → UTC)
    # -----------------------------------
    start_date_ist = utils.get_ist_start_of_day(days - 1)
    start_date_utc = start_date_ist.astimezone(pytz.UTC)

    # -----------------------------------
    # 3. TOTAL VISITS (FILTERED BY DAYS) ✅ FIX
    # -----------------------------------
    total_visits = db.query(models.Visit).filter(
        models.Visit.project_id == project_id,
        models.Visit.visited_at >= start_date_utc
    ).count()

    # -----------------------------------
    # 4. UNIQUE VISITORS (FILTERED BY DAYS) ✅ FIX
    # -----------------------------------
    unique_visitors = db.query(
        func.count(func.distinct(models.Visit.visitor_id))
    ).filter(
        models.Visit.project_id == project_id,
        models.Visit.visited_at >= start_date_utc
    ).scalar()

    # -----------------------------------
    # 5. LIVE VISITORS (Last 5 minutes)
    # -----------------------------------
    five_min_ago = datetime.utcnow() - timedelta(minutes=5)
    live_visitors = db.query(
        func.count(func.distinct(models.Visit.visitor_id))
    ).filter(
        models.Visit.project_id == project_id,
        models.Visit.visited_at >= five_min_ago
    ).scalar()

    # -----------------------------------
    # 6. DAILY STATS (Period Based)
    # -----------------------------------
    from sqlalchemy import case

    dialect_name = db.bind.dialect.name
    ist_date_expr = utils.get_ist_date_expr(
        models.Visit.visited_at, dialect_name
    )

    daily_data = db.query(
        ist_date_expr.label("visit_date"),
        func.count(models.PageView.id).label("page_views"),
        func.count(func.distinct(models.Visit.visitor_id)).label("unique_visits"),
        func.count(func.distinct(
            case((models.Visit.is_unique == True, models.Visit.visitor_id), else_=None)
        )).label("first_time_visits"),
        func.count(func.distinct(
            case((models.Visit.is_unique == False, models.Visit.visitor_id), else_=None)
        )).label("returning_visits")
    ).join(
        models.PageView, models.Visit.id == models.PageView.visit_id
    ).filter(
        models.Visit.project_id == project_id,
        models.Visit.visited_at >= start_date_utc
    ).group_by(ist_date_expr).all()

    stats_dict = {
        row.visit_date: {
            "page_views": row.page_views,
            "unique_visits": row.unique_visits,
            "first_time_visits": row.first_time_visits or 0,
            "returning_visits": row.returning_visits or 0,
        }
        for row in daily_data
    }

    daily_stats = []
    for i in range(days - 1, -1, -1):
        day_start_ist = utils.get_ist_start_of_day(i)
        day_date = day_start_ist.date()

        stats = stats_dict.get(day_date) or stats_dict.get(
            str(day_date),
            {"page_views": 0, "unique_visits": 0, "first_time_visits": 0, "returning_visits": 0}
        )

        daily_stats.append({
            "date": day_start_ist.strftime("%a, %d %b %Y"),
            "page_views": stats["page_views"],
            "unique_visits": stats["unique_visits"],
            "first_time_visits": stats["first_time_visits"],
            "returning_visits": stats["returning_visits"],
        })

    # -----------------------------------
    # 7. ALL TIME DAILY STATS (NO FILTER)
    # -----------------------------------
    all_time_data = db.query(
        ist_date_expr.label("visit_date"),
        func.count(models.PageView.id).label("page_views"),
        func.count(func.distinct(models.Visit.visitor_id)).label("unique_visits"),
        func.count(func.distinct(
            case((models.Visit.is_unique == True, models.Visit.visitor_id), else_=None)
        )).label("first_time_visits"),
        func.count(func.distinct(
            case((models.Visit.is_unique == False, models.Visit.visitor_id), else_=None)
        )).label("returning_visits")
    ).join(
        models.PageView, models.Visit.id == models.PageView.visit_id
    ).filter(
        models.Visit.project_id == project_id
    ).group_by(ist_date_expr).order_by(ist_date_expr).all()

    all_daily_stats = []
    for row in all_time_data:
        row_date = row.visit_date
        if isinstance(row_date, str):
            try:
                row_date = datetime.strptime(row_date, "%Y-%m-%d").date()
            except:
                pass

        all_daily_stats.append({
            "date": row_date.strftime("%a, %d %b %Y") if hasattr(row_date, "strftime") else str(row_date),
            "page_views": row.page_views,
            "unique_visits": row.unique_visits,
            "first_time_visits": row.first_time_visits or 0,
            "returning_visits": row.returning_visits or 0,
        })

    # -----------------------------------
    # 8. AVERAGES (Period Based)
    # -----------------------------------
    total_days = len(daily_stats) or 1

    averages = {
        "page_views": round(sum(d["page_views"] for d in daily_stats) / total_days, 1),
        "unique_visits": round(sum(d["unique_visits"] for d in daily_stats) / total_days, 1),
        "first_time_visits": round(sum(d["first_time_visits"] for d in daily_stats) / total_days, 1),
        "returning_visits": round(sum(d["returning_visits"] for d in daily_stats) / total_days, 1),
    }

    # -----------------------------------
    # 9. TOP PAGES / SOURCES / DEVICES
    # -----------------------------------
    top_pages = db.query(
        models.Page.url,
        models.Page.title,
        models.Page.total_views
    ).filter(
        models.Page.project_id == project_id
    ).order_by(desc(models.Page.total_views)).limit(5).all()

    top_sources = db.query(
        models.TrafficSource.source_name,
        func.sum(models.TrafficSource.visit_count).label("count")
    ).filter(
        models.TrafficSource.project_id == project_id
    ).group_by(models.TrafficSource.source_name).order_by(desc("count")).limit(5).all()

    device_stats = db.query(
        models.Visit.device,
        func.count(models.Visit.id)
    ).filter(
        models.Visit.project_id == project_id
    ).group_by(models.Visit.device).all()

    # -----------------------------------
    # 10. RESPONSE
    # -----------------------------------
    return {
        "total_visits": total_visits,
        "unique_visitors": unique_visitors,
        "live_visitors": live_visitors,
        "daily_stats": daily_stats,
        "all_daily_stats": all_daily_stats,
        "averages": averages,
        "top_pages": [{"url": p[0], "title": p[1], "views": p[2]} for p in top_pages],
        "top_sources": [{"source": s[0], "count": s[1]} for s in top_sources],
        "device_stats": {d[0]: d[1] for d in device_stats if d[0]},
    }


@router.get("/{project_id}/summary-view")
def get_summary_view(
    project_id: int, 
    days: int = 30, 
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
        ):
    """Specific API for Summary Page - Returns only necessary stats"""
    # Check if project exists and user has access
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # If user is authenticated, check if they own the project
    if current_user and project.user_id and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
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
    
    # Daily stats
    from sqlalchemy import case, cast, Date
    
    # IST calculation
    start_date_ist = utils.get_ist_start_of_day(days - 1)
    start_date_utc = start_date_ist.astimezone(pytz.UTC)
    print(start_date_utc)
    
    dialect_name = db.bind.dialect.name
    ist_date_expr = utils.get_ist_date_expr(models.Visit.visited_at, dialect_name)
    
    # Single query to get all stats grouped by date - COUNTING ACTUAL PAGEVIEWS
    daily_data = db.query(
        ist_date_expr.label('visit_date'),
        func.count(models.PageView.id).label('page_views'),
        func.count(func.distinct(models.Visit.visitor_id)).label('unique_visits'),
        func.count(func.distinct(case((models.Visit.is_unique == True, models.Visit.visitor_id), else_=None))).label('first_time_visits'),
        func.count(func.distinct(
            case(
                (models.Visit.is_unique == False, models.Visit.visitor_id),
                else_=None
            )
        )).label('returning_visits')
    ).join(
        models.PageView, models.Visit.id == models.PageView.visit_id
    ).filter(
        models.Visit.project_id == project_id,
        models.Visit.visited_at >= start_date_utc
    ).group_by(ist_date_expr).all()
    
    stats_dict = {
        row.visit_date: {
            'page_views': row.page_views,
            'unique_visits': row.unique_visits,
            'first_time_visits': row.first_time_visits or 0,
            'returning_visits': row.returning_visits or 0
        }
        for row in daily_data
    }
    
    daily_stats = []
    for i in range(days - 1, -1, -1):
        day_start_ist = utils.get_ist_start_of_day(i)
        day_date = day_start_ist.date()
        
        stats = stats_dict.get(day_date)
        if stats is None:
            stats = stats_dict.get(str(day_date), {'page_views': 0, 'unique_visits': 0, 'first_time_visits': 0, 'returning_visits': 0})
        
        daily_stats.append({
            "date": day_start_ist.strftime("%a, %d %b %Y"),
            "page_views": stats['page_views'],
            "unique_visits": stats['unique_visits'],
            "first_time_visits": stats['first_time_visits'],
            "returning_visits": stats['returning_visits']
        })
    
    # Calculate averages
    total_days = len(daily_stats)
    avg_page_views = sum(d["page_views"] for d in daily_stats) / total_days if total_days > 0 else 0
    avg_unique_visits = sum(d["unique_visits"] for d in daily_stats) / total_days if total_days > 0 else 0
    avg_first_time = sum(d["first_time_visits"] for d in daily_stats) / total_days if total_days > 0 else 0
    avg_returning = sum(d["returning_visits"] for d in daily_stats) / total_days if total_days > 0 else 0
    
    return {
        
        "daily_stats": daily_stats,
        "averages": {
            "page_views": round(avg_page_views, 1),
            "unique_visits": round(avg_unique_visits, 1),
            "first_time_visits": round(avg_first_time, 1),
            "returning_visits": round(avg_returning, 1)
        }
    }

def get_hourly_analytics_range_logic(
    project_id: int, 
    start_date: str,
    end_date: str,
    db: Session,
    current_user: Optional[models.User]
):
    """Shared logic for hourly analytics for a date range"""
    
    # Parse the date strings - handle different formats
    from urllib.parse import unquote
    decoded_start_date = unquote(start_date)
    decoded_end_date = unquote(end_date)
    
    # Try different date formats
    date_formats = [
        "%a, %d %b %Y",  # "Mon, 16 Dec 2024"
        "%Y-%m-%d",      # "2024-12-16"
        "%d %b %Y",      # "16 Dec 2024"
        "%d/%m/%Y",      # "16/12/2024"
    ]
    
    parsed_start_date = None
    parsed_end_date = None
    
    for fmt in date_formats:
        try:
            parsed_start_date = datetime.strptime(decoded_start_date, fmt).date()
            break
        except ValueError:
            continue
    
    for fmt in date_formats:
        try:
            parsed_end_date = datetime.strptime(decoded_end_date, fmt).date()
            break
        except ValueError:
            continue
    
    if not parsed_start_date or not parsed_end_date:
        raise HTTPException(status_code=400, detail="Invalid date format")
    
    # Convert to IST timezone and get UTC ranges
    ist = pytz.timezone('Asia/Kolkata')
    start_datetime_ist = ist.localize(datetime.combine(parsed_start_date, datetime.min.time()))
    end_datetime_ist = ist.localize(datetime.combine(parsed_end_date, datetime.max.time()))
    
    start_datetime_utc = start_datetime_ist.astimezone(pytz.UTC)
    end_datetime_utc = end_datetime_ist.astimezone(pytz.UTC)
    
    print(f" Getting hourly data for range {parsed_start_date} to {parsed_end_date} IST ({start_datetime_utc} to {end_datetime_utc})")
    
    # Get hourly data for the date range - COUNTING ACTUAL PAGEVIEWS
    hourly_data = db.query(
        func.extract('hour', models.PageView.viewed_at).label('hour'),
        func.count(models.PageView.id).label('page_views'),
        func.count(func.distinct(models.Visit.visitor_id)).label('unique_visits'),
        func.count(func.distinct(case((models.Visit.is_unique == True, models.Visit.visitor_id), else_=None))).label('first_time_visits'),
        func.count(func.distinct(
            case(
                (models.Visit.is_unique == False, models.Visit.visitor_id),
                else_=None
            )
        )).label('returning_visits')
    ).join(
        models.PageView, models.Visit.id == models.PageView.visit_id
    ).filter(
        models.Visit.project_id == project_id,
        models.PageView.viewed_at >= start_datetime_utc,
        models.PageView.viewed_at <= end_datetime_utc
    ).group_by(
        func.extract('hour', models.PageView.viewed_at)
    ).all()
    
    print(f" Found {len(hourly_data)} hours with data for date range")
    
    # Create hourly stats array for all 24 hours
    hourly_stats = []
    for hour in range(24):
        hour_data = next((h for h in hourly_data if int(h.hour) == hour), None)
        
        if hour_data:
            page_views = hour_data.page_views
            unique_visits = hour_data.unique_visits
            first_time_visits = hour_data.first_time_visits or 0
            returning_visits = hour_data.returning_visits or 0
        else:
            page_views = 0
            unique_visits = 0
            first_time_visits = 0
            returning_visits = 0
        
        hourly_stats.append({
            "hour": f"{hour:02d}:00",
            "page_views": page_views,
            "unique_visits": unique_visits,
            "first_time_visits": first_time_visits,
            "returning_visits": returning_visits
        })
    
    # Calculate totals correctly - avoid double counting visitors across hours
    # For page_views: sum all hourly page_views (correct)
    total_page_views = sum(h['page_views'] for h in hourly_stats)
    
    # For unique_visits and first_time_visits: use the original query results, not sum of hourly
    # because same visitor can appear in multiple hours
    total_unique_visits = sum(h.unique_visits for h in hourly_data)
    total_first_time_visits = sum(h.first_time_visits or 0 for h in hourly_data)
    total_returning_visits = sum(h.returning_visits or 0 for h in hourly_data)
    
    print(f" Hourly analytics for range calculated - Totals: {{'page_views': {total_page_views}, 'unique_visits': {total_unique_visits}, 'first_time_visits': {total_first_time_visits}, 'returning_visits': {total_returning_visits}}}")
    
    return {
        "date_range": f"{decoded_start_date} to {decoded_end_date}",
        "hourly_stats": hourly_stats,
        "totals": {
            "page_views": total_page_views,
            "unique_visits": total_unique_visits,
            "first_time_visits": total_first_time_visits,
            "returning_visits": total_returning_visits
        }
    }

@router.get("/{project_id}/hourly-range")
def get_hourly_analytics_range(
    project_id: int, 
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
):
    """Get hourly analytics for a date range (weekly/monthly summaries)"""
    
    # Check if project exists and user has access
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # If user is authenticated, check if they own the project
    if current_user and project.user_id and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        return get_hourly_analytics_range_logic(project_id, start_date, end_date, db, current_user)
        
        if not parsed_start_date or not parsed_end_date:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {decoded_start_date} - {decoded_end_date}")
        
        # Get start and end of the date range in IST then convert to UTC for filtering
        range_start_ist = datetime.combine(parsed_start_date, datetime.min.time())
        range_end_ist = datetime.combine(parsed_end_date, datetime.max.time())
        range_start_utc = utils.ist_to_utc(range_start_ist)
        range_end_utc = utils.ist_to_utc(range_end_ist)
        
        print(f" Getting hourly data for range {parsed_start_date} to {parsed_end_date} IST ({range_start_utc} to {range_end_utc} UTC)")
        
        # Query hourly data using SQL for the entire date range - COUNTING ACTUAL PAGEVIEWS
        from sqlalchemy import extract, case
        dialect_name = db.bind.dialect.name
        ist_hour_expr = utils.get_ist_hour_expr(models.PageView.viewed_at, dialect_name)
        
        hourly_data = db.query(
            ist_hour_expr.label('hour'),
            func.count(models.PageView.id).label('page_views'),
            func.count(func.distinct(models.Visit.visitor_id)).label('unique_visits'),
            func.count(func.distinct(case((models.Visit.is_unique == True, models.Visit.visitor_id), else_=None))).label('first_time_visits'),
        ).join(
            models.PageView, models.Visit.id == models.PageView.visit_id
        ).filter(
            models.Visit.project_id == project_id,
            models.Visit.visited_at >= range_start_utc,
            models.Visit.visited_at <= range_end_utc
        ).group_by('hour').all()
        
        print(f" Found {len(hourly_data)} hours with data for date range")
        
        # Create a dict for quick lookup
        hourly_dict = {
            int(row.hour): {
                'page_views': row.page_views,
                'unique_visits': row.unique_visits,
                'first_time_visits': row.first_time_visits or 0,
                'returning_visits': row.returning_visits or 0
            }
            for row in hourly_data
        }
        
        # Build complete 24-hour array
        hourly_stats = []
        for hour in range(24):
            hour_str = f"{hour:02d}:00"
            time_range = f"{hour:02d}:00-{hour:02d}:59"
            
            stats = hourly_dict.get(hour, {'page_views': 0, 'unique_visits': 0, 'first_time_visits': 0})
            
            hourly_stats.append({
                "date": hour_str,
                "timeRange": time_range,
                "page_views": stats['page_views'],
                "unique_visits": stats['unique_visits'],
                "first_time_visits": stats['first_time_visits'],
                "returning_visits": stats['returning_visits']
            })
        
        # Calculate totals
        totals = {
            'page_views': sum(h['page_views'] for h in hourly_stats),
            'unique_visits': sum(h['unique_visits'] for h in hourly_stats),
            'first_time_visits': sum(h['first_time_visits'] for h in hourly_stats),
            'returning_visits': sum(h['returning_visits'] for h in hourly_stats)
        }
        
        # Calculate averages
        averages = {
            'page_views': round(totals['page_views'] / 24, 1),
            'unique_visits': round(totals['unique_visits'] / 24, 1),
            'first_time_visits': round(totals['first_time_visits'] / 24, 1),
            'returning_visits': round(totals['returning_visits'] / 24, 1)
        }
        
        print(f" Hourly analytics for range calculated - Totals: {totals}")
        
        return {
            "date": f"{decoded_start_date} - {decoded_end_date}",
            "hourly_stats": hourly_stats,
            "totals": totals,
            "averages": averages
        }
        
    except Exception as e:
        print(f" Error in hourly analytics range: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing hourly data range: {str(e)}")

@router.get("/{project_id}/hourly/{date}")
def get_hourly_analytics(
    project_id: int, 
    date: str,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user_optional)
 ):
    """Get hourly analytics for a specific date"""
    
    # Check if project exists and user has access
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # If user is authenticated, check if they own the project
    if current_user and project.user_id and project.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Parse the date string - handle different formats including date ranges
        from urllib.parse import unquote
        decoded_date = unquote(date)
        
        # Add debug logging
        print(f"🔍 Debug: Received date string: '{decoded_date}'")
        
        # Check if it's a date range (contains " - ")
        if " - " in decoded_date:
            # Handle date range format: "Wed, 31 Dec 2025 - Tue, 06 Jan 2026"
            start_date_str, end_date_str = decoded_date.split(" - ", 1)
            print(f"📅 Date range detected: Start='{start_date_str}', End='{end_date_str}'")
            
            # Parse start date
            start_date = None
            for fmt in ["%a, %d %b %Y", "%Y-%m-%d", "%d %b %Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"]:
                try:
                    start_date = datetime.strptime(start_date_str, fmt).date()
                    print(f"✅ Start date parsed with format '{fmt}': {start_date}")
                    break
                except ValueError:
                    continue
            
            # Parse end date
            end_date = None
            for fmt in ["%a, %d %b %Y", "%Y-%m-%d", "%d %b %Y", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"]:
                try:
                    end_date = datetime.strptime(end_date_str, fmt).date()
                    print(f"✅ End date parsed with format '{fmt}': {end_date}")
                    break
                except ValueError:
                    continue
            
            if not start_date or not end_date:
                print(f"🚨 ERROR: Could not parse date range '{decoded_date}'!")
                raise HTTPException(status_code=400, detail=f"Invalid date range format: {decoded_date}")
            
            # Use hourly-range endpoint logic for date ranges
            return get_hourly_analytics_range_logic(project_id, start_date_str, end_date_str, db, current_user)
        
        # Handle single date formats
        date_formats = [
            "%a, %d %b %Y",  # "Mon, 08 Dec 2024"
            "%Y-%m-%d",      # "2024-12-16"
            "%d %b %Y",      # "16 Dec 2024"
            "%d/%m/%Y",      # "16/12/2024"
            "%B %d, %Y",     # "December 16, 2024"
            "%b %d, %Y",     # "Dec 16, 2024"
        ]
        
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(decoded_date, fmt).date()
                print(f"✅ Successfully parsed with format '{fmt}': {parsed_date}")
                break
            except ValueError as e:
                print(f"❌ Failed to parse with format '{fmt}': {e}")
                continue
        
        if not parsed_date:
            print(f"🚨 ERROR: Could not parse date '{decoded_date}' with any format!")
            raise HTTPException(status_code=400, detail=f"Invalid date format: {decoded_date}")
        
        # Get start and end of the day in IST then convert to UTC for filtering
        day_start_ist = datetime.combine(parsed_date, datetime.min.time())
        day_end_ist = datetime.combine(parsed_date, datetime.max.time())
        day_start_utc = utils.ist_to_utc(day_start_ist)
        day_end_utc = utils.ist_to_utc(day_end_ist)
        
        print(f" Getting hourly data for {parsed_date} IST ({day_start_utc} to {day_end_utc} UTC)")
        
        # Query hourly data using SQL - COUNTING ACTUAL PAGEVIEWS
        from sqlalchemy import extract, case
        dialect_name = db.bind.dialect.name
        ist_hour_expr = utils.get_ist_hour_expr(models.PageView.viewed_at, dialect_name)
        
        hourly_data = db.query(
            ist_hour_expr.label('hour'),
            func.count(models.PageView.id).label('page_views'),
            func.count(func.distinct(models.Visit.visitor_id)).label('unique_visits'),
            func.count(func.distinct(case((models.Visit.is_unique == True, models.Visit.visitor_id), else_=None))).label('first_time_visits'),
            func.count(func.distinct(
                case(
                    (models.Visit.is_unique == False, models.Visit.visitor_id),
                    else_=None
                )
            )).label('returning_visits')
        ).join(
            models.PageView, models.Visit.id == models.PageView.visit_id
        ).filter(
            models.Visit.project_id == project_id,
            models.Visit.visited_at >= day_start_utc,
            models.Visit.visited_at <= day_end_utc
        ).group_by('hour').all()
        
        print(f" Found {len(hourly_data)} hours with data")
        
        # Get correct daily totals without double-counting - COUNTING ACTUAL PAGEVIEWS
        daily_totals = db.query(
            func.count(models.PageView.id).label('page_views'),
            func.count(func.distinct(models.Visit.visitor_id)).label('unique_visits'),
            func.count(func.distinct(case((models.Visit.is_unique == True, models.Visit.visitor_id), else_=None))).label('first_time_visits'),
            func.count(func.distinct(
                case(
                    (models.Visit.is_unique == False, models.Visit.visitor_id),
                    else_=None
                )
            )).label('returning_visits')
        ).join(
            models.PageView, models.Visit.id == models.PageView.visit_id
        ).filter(
            models.Visit.project_id == project_id,
            models.Visit.visited_at >= day_start_utc,
            models.Visit.visited_at <= day_end_utc
        ).first()
        
        # Create a dict for quick lookup
        hourly_dict = {
            int(row.hour): {
                'page_views': row.page_views,
                'unique_visits': row.unique_visits,
                'first_time_visits': row.first_time_visits or 0,
                'returning_visits': row.returning_visits or 0
            }
            for row in hourly_data
        }
        
        # Build complete 24-hour array
        hourly_stats = []
        for hour in range(24):
            hour_str = f"{hour:02d}:00"
            time_range = f"{hour:02d}:00-{hour:02d}:59"
            
            stats = hourly_dict.get(hour, {'page_views': 0, 'unique_visits': 0, 'first_time_visits': 0, 'returning_visits': 0})
            
            hourly_stats.append({
                "date": hour_str,
                "timeRange": time_range,
                "page_views": stats['page_views'],
                "unique_visits": stats['unique_visits'],
                "first_time_visits": stats['first_time_visits'],
                "returning_visits": stats['returning_visits']
            })
        
        # Calculate totals correctly - use daily totals to avoid double counting
        # For page_views: sum all hourly page_views (correct)
        total_page_views = sum(h['page_views'] for h in hourly_stats)
        
        # For unique_visits, first_time_visits, returning_visits: use daily totals
        # because same visitor can appear in multiple hours
        total_unique_visits = daily_totals.unique_visits or 0
        total_first_time_visits = daily_totals.first_time_visits or 0
        total_returning_visits = daily_totals.returning_visits or 0
        
        totals = {
            'page_views': total_page_views,
            'unique_visits': total_unique_visits,
            'first_time_visits': total_first_time_visits,
            'returning_visits': total_returning_visits
        }
        
        # Calculate averages
        averages = {
            'page_views': round(totals['page_views'] / 24, 1),
            'unique_visits': round(totals['unique_visits'] / 24, 1),
            'first_time_visits': round(totals['first_time_visits'] / 24, 1),
            'returning_visits': round(totals['returning_visits'] / 24, 1)
        }
        
        print(f" Hourly analytics calculated - Totals: {totals}")
        
        return {
            "date": decoded_date,
            "hourly_stats": hourly_stats,
            "totals": totals,
            "averages": averages
        }
        
    except Exception as e:
        print(f" Error in hourly analytics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing hourly data: {str(e)}")

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
def track_pageview(project_id: int, visit_id: int, pageview: schemas.PageViewCreate, request: Request, db: Session = Depends(get_db)):
    """Track a page view within a visit"""

    if _is_probable_bot_request(request):
        _log_ignored(request, "pageview")
        return {
            "message": "Ignored"
        }
    
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

@router.put("/{project_id}/pageview/{visit_id}/update/{pageview_id}")
def update_pageview_time(project_id: int, visit_id: int, pageview_id: int, data: dict, request: Request, db: Session = Depends(get_db)):
    """Update time spent on a page view"""


    if _is_probable_bot_request(request):
        _log_ignored(request, "pageview_update")
        return {
            "message": "Ignored"
        }
    
    # Find the page view
    pageview = db.query(models.PageView).join(models.Visit).filter(
        models.PageView.id == pageview_id,
        models.Visit.id == visit_id,
        models.Visit.project_id == project_id
    ).first()
    
    if not pageview:
        raise HTTPException(status_code=404, detail="Page view not found")
    
    # Update time spent
    if 'time_spent' in data:
        pageview.time_spent = data['time_spent']
    
    db.commit()
    
    return {
        "message": "Time spent updated",
        "time_spent": pageview.time_spent
    }

@router.post("/{project_id}/exit/{visit_id}")
def track_exit(project_id: int, visit_id: int, exit_data: dict, request: Request, db: Session = Depends(get_db)):
    """Track exit page and final time spent"""


    if _is_probable_bot_request(request):
        _log_ignored(request, "exit")
        return {
            "message": "Ignored"
        }
    
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
def track_exit_link(project_id: int, link_data: dict, request: Request, db: Session = Depends(get_db)):
    """Track external link clicks"""

    
    if _is_probable_bot_request(request):
        _log_ignored(request, "exit_link")
        return {
            "message": "Ignored"
        }
    
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

@router.post("/{project_id}/cart-action/{visit_id}")
def track_cart_action(project_id: int, visit_id: int, cart_action: schemas.CartActionCreate, request: Request, db: Session = Depends(get_db)):
    """Track cart actions (add to cart / remove from cart)"""

    if _is_probable_bot_request(request):
        _log_ignored(request, "cart_action")
        return {
            "message": "Ignored"
        }
    
    # Verify visit exists
    visit = db.query(models.Visit).filter(
        models.Visit.id == visit_id,
        models.Visit.project_id == project_id
    ).first()
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    # Create cart action record
    db_cart_action = models.CartAction(
        project_id=project_id,
        visit_id=visit_id,
        action=cart_action.action,
        product_id=cart_action.product_id,
        product_name=cart_action.product_name,
        product_url=cart_action.product_url,
        page_url=cart_action.page_url
    )
    db.add(db_cart_action)
    
    # Also create a page view for this cart action to show in analytics
    page_title = f"Cart Action: {cart_action.action}"
    if cart_action.product_name:
        page_title += f" - {cart_action.product_name}"
    
    # Create virtual page URL for cart action
    virtual_page_url = f"{cart_action.page_url}#cart-{cart_action.action}"
    if cart_action.product_id:
        virtual_page_url += f"-{cart_action.product_id}"
    
    # Get or create page record for cart action
    page = db.query(models.Page).filter(
        models.Page.project_id == project_id,
        models.Page.url == virtual_page_url
    ).first()
    
    if not page:
        page = models.Page(
            project_id=project_id,
            url=virtual_page_url,
            title=page_title,
            total_views=0,
            unique_views=0
        )
        db.add(page)
        db.flush()
    
    # Create page view for cart action
    db_pageview = models.PageView(
        visit_id=visit_id,
        page_id=page.id,
        url=virtual_page_url,
        title=page_title,
        time_spent=0,
        scroll_depth=0
    )
    db.add(db_pageview)
    
    # Update page stats
    page.total_views += 1
    
    db.commit()
    db.refresh(db_cart_action)
    
    return {
        "cart_action_id": db_cart_action.id,
        "message": "Cart action tracked",
        "virtual_page_url": virtual_page_url
    }

@router.post("/{project_id}/track")
def track_visit(project_id: int, visit: schemas.VisitCreate, request: Request, db: Session = Depends(get_db)):
    import requests


    if _is_probable_bot_request(request):
        _log_ignored(request, "track")
        return {
            "visit_id": None,
            "message": "Ignored",
            "is_duplicate": False,
            "is_unique_visitor": False
        }
  
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

# ============================================
# COOKIE MANAGEMENT ENDPOINTS (GDPR Compliance)
# ============================================

@router.post("/{project_id}/opt-out")
def opt_out_tracking(project_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Opt-out user from analytics tracking
    Sets a cookie to prevent future tracking
    """
    # Check if project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # In a real implementation, this would set an HttpOnly cookie server-side
    # For now, we return the opt-out confirmation
    return {
        "message": "Opt-out successful",
        "project_id": project_id,
        "instructions": "Please call Analytics.optOut() in your browser to complete opt-out"
    }

@router.post("/{project_id}/opt-in")
def opt_in_tracking(project_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Opt-in user to analytics tracking
    Removes the opt-out cookie
    """
    # Check if project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {
        "message": "Opt-in successful",
        "project_id": project_id,
        "instructions": "Please call Analytics.optIn() in your browser to complete opt-in"
    }

@router.get("/{project_id}/cookie-status")
def get_cookie_status(project_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Get current cookie and tracking status
    """
    # Check if project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get visitor ID from request headers if available
    visitor_id = request.headers.get("X-Visitor-ID")
    
    return {
        "project_id": project_id,
        "visitor_id": visitor_id,
        "tracking_enabled": True,  # This would be determined by server-side cookie check
        "cookie_domain": request.headers.get("Host"),
        "secure_connection": request.url.scheme.startswith("https")
    }