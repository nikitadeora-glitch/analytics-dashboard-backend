from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from database import get_db
import models
import utils
from datetime import datetime, time
from typing import Optional, Dict
from fastapi import Query
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

# Constants for traffic source classification
SEARCH_ENGINES = ["google", "bing", "yahoo", "duckduckgo", "baidu"]
SOCIAL_SITES = ["facebook", "twitter", "instagram", "linkedin", "youtube", "tiktok", "pinterest"]
AI_TOOLS = ["chatgpt", "claude", "gemini", "copilot", "perplexity"]
EMAIL_PROVIDERS = ["mail", "gmail", "outlook", "yahoo.com"]
PAID_MARKERS = ["ads", "adwords", "facebook.com/tr"]
UTM_MARKERS = ["utm_", "campaign"]

def classify_source(referrer: str) -> str:
    """
    Classify traffic source based on referrer URL.
    This ensures consistency with traffic_sources endpoint.
    """
    r = (referrer or "").lower().strip()
    
    # Direct traffic
    if not r or r in ("direct", "null", "undefined"):
        return "direct"
    
    # Organic Search
    if any(x in r for x in SEARCH_ENGINES):
        return "organic"
    
    # Social Media
    if any(x in r for x in SOCIAL_SITES):
        return "social"
    
    # AI Tools
    if any(x in r for x in AI_TOOLS):
        return "ai"
    
    # Email
    if any(x in r for x in EMAIL_PROVIDERS):
        return "email"
    
    # Paid Traffic
    if any(x in r for x in PAID_MARKERS):
        return "paid"
    
    # UTM Campaigns
    if any(x in r for x in UTM_MARKERS):
        return "utm"
    
    # Everything else is referral
    return "referral"

# Filter mapping dictionary - maps frontend filter IDs to database fields
FILTER_MAP = {
    "country_city": "country",
    "browser": "browser", 
    "device": "device",  # FIXED: Changed from device_type to device
    "utm_source": "utm_source",
    "utm_medium": "utm_medium",
    "utm_campaign": "utm_campaign",
    "platform_os": "os",
    "system_platform_os": "os",
    "session_length": "session_duration",
    "engagement_session_length": "session_duration",
    "page_views": "page_views_count",
    "page_views_per_session": "page_views_per_session",
    "sessions_per_visitor": "sessions_per_visitor",
    "engagement_sessions_per_visitor": "sessions_per_visitor",
    "engagement_exit_link": "exit_page",
    "traffic_sources": "referrer",
    "traffic_utm_campaign": "utm_campaign",
    "traffic_utm_source": "utm_source",
    "page": "page",
    "page_page": "page",
    "entry_page": "entry_page",
    "location_ip_address": "ip_address"
}

def apply_filters_to_query(query, filters, db):
    """Apply custom filters to SQLAlchemy query"""
    if not filters:
        print("🔍 No filters to apply")
        return query
        
    print(f"🔍 Applying {len(filters)} filters to query")
    
    for filter_key, filter_value in filters.items():
        print(f"  Processing filter: {filter_key} = {filter_value}")
        
        # Handle range filters (min/max)
        if filter_key.endswith('_min') or filter_key.endswith('_max'):
            base_key = filter_key.replace('_min', '').replace('_max', '')
            if base_key in FILTER_MAP:
                db_field = FILTER_MAP[base_key]
                if filter_key.endswith('_min'):
                    query = query.filter(getattr(models.Visit, db_field) >= float(filter_value))
                    print(f"    ✅ Applied {db_field} >= {filter_value}")
                elif filter_key.endswith('_max'):
                    query = query.filter(getattr(models.Visit, db_field) <= float(filter_value))
                    print(f"    ✅ Applied {db_field} <= {filter_value}")
            continue  # Skip to next filter - range filters are handled here
        
        # Handle operator filters
        elif filter_key.endswith('_operator'):
            continue  # Operators are handled with their values
            
        # Handle regular filters
        elif filter_key in FILTER_MAP:
            db_field = FILTER_MAP[filter_key]
            print(f"  Found filter in FILTER_MAP: {filter_key} -> {db_field}")
            
            # Special handling for browser filter (case-insensitive partial match)
            if filter_key == "browser":
                print(f"  BROWSER FILTER DETECTED: {filter_key} = {filter_value}")
                # Check if there's an operator for this filter
                operator_key = f"{filter_key}_operator"
                operator = filters.get(operator_key, 'contains')
                print(f"  Browser operator: {operator}")
                
                # Case-insensitive browser filtering with partial match
                if operator == 'equals':
                    print(f"  Applying case-insensitive browser filter: {db_field} = {filter_value}")
                    query = query.filter(func.lower(getattr(models.Visit, db_field)) == func.lower(filter_value))
                    print(f"    Applied case-insensitive {db_field} = {filter_value}")
                elif operator == 'greater':
                    query = query.filter(getattr(models.Visit, db_field) > float(filter_value))
                elif operator == 'less':
                    query = query.filter(getattr(models.Visit, db_field) < float(filter_value))
                elif operator == 'greater_equal':
                    query = query.filter(getattr(models.Visit, db_field) >= float(filter_value))
                elif operator == 'less_equal':
                    query = query.filter(getattr(models.Visit, db_field) <= float(filter_value))
                else:  # Default to contains for browser (case-insensitive partial match)
                    query = query.filter(getattr(models.Visit, db_field).ilike(f"%{filter_value}%"))
                
                print(f"    Applied {db_field} {operator} {filter_value} (case-insensitive partial match)")
            # Special handling for device filter (case-insensitive)
            elif filter_key == "device":
                print(f"  DEVICE FILTER DETECTED: {filter_key} = {filter_value}")
                # Check if there's an operator for this filter
                operator_key = f"{filter_key}_operator"
                operator = filters.get(operator_key, 'equals')
                print(f"  Device operator: {operator}")
                
                # Case-insensitive device filtering
                if operator == 'equals':
                    print(f"  Applying case-insensitive device filter: {db_field} = {filter_value}")
                    query = query.filter(func.lower(getattr(models.Visit, db_field)) == func.lower(filter_value))
                    print(f"    ✅ Applied case-insensitive {db_field} = {filter_value}")
                elif operator == 'greater':
                    query = query.filter(getattr(models.Visit, db_field) > float(filter_value))
                elif operator == 'less':
                    query = query.filter(getattr(models.Visit, db_field) < float(filter_value))
                elif operator == 'greater_equal':
                    query = query.filter(getattr(models.Visit, db_field) >= float(filter_value))
                elif operator == 'less_equal':
                    query = query.filter(getattr(models.Visit, db_field) <= float(filter_value))
                else:  # Default to contains for text fields (case-insensitive)
                    query = query.filter(getattr(models.Visit, db_field).ilike(f"%{filter_value}%"))
                
                print(f"    ✅ Applied {db_field} {operator} {filter_value} (case-insensitive)")
            # Special handling for OS filters (case-insensitive)
            elif filter_key in ["platform_os", "system_platform_os"]:
                print(f"  OS FILTER DETECTED: {filter_key} = {filter_value}")
                # Check if there's an operator for this filter
                operator_key = f"{filter_key}_operator"
                operator = filters.get(operator_key, 'equals')
                print(f"  OS operator: {operator}")
                
                # Case-insensitive OS filtering
                if operator == 'equals':
                    print(f"  Applying case-insensitive OS filter: {db_field} = {filter_value}")
                    query = query.filter(func.lower(getattr(models.Visit, db_field)) == func.lower(filter_value))
                    print(f"    Applied case-insensitive {db_field} = {filter_value}")
                    print(f"    ✅ Applied case-insensitive {db_field} = {filter_value}")
                elif operator == 'greater':
                    query = query.filter(getattr(models.Visit, db_field) > float(filter_value))
                elif operator == 'less':
                    query = query.filter(getattr(models.Visit, db_field) < float(filter_value))
                elif operator == 'greater_equal':
                    query = query.filter(getattr(models.Visit, db_field) >= float(filter_value))
                elif operator == 'less_equal':
                    query = query.filter(getattr(models.Visit, db_field) <= float(filter_value))
                else:  # Default to contains for text fields (case-insensitive)
                    query = query.filter(getattr(models.Visit, db_field).ilike(f"%{filter_value}%"))
                
                print(f"    ✅ Applied {db_field} {operator} {filter_value} (case-insensitive)")
            elif filter_key == "page_views_per_session":
                # Check if there's an operator for this filter
                operator_key = f"{filter_key}_operator"
                operator = filters.get(operator_key, 'equals')
                
                # Create subquery that counts page views per visit
                page_views_subquery = db.query(
                    models.PageView.visit_id,
                    func.count(models.PageView.id).label('page_view_count')
                ).group_by(models.PageView.visit_id).subquery()
                
                # Join with the subquery
                query = query.join(
                    page_views_subquery,
                    models.Visit.id == page_views_subquery.c.visit_id
                )
                
                # Apply the filter on the calculated page view count
                if operator == 'equals':
                    query = query.filter(page_views_subquery.c.page_view_count == int(filter_value))
                elif operator == 'greater':
                    query = query.filter(page_views_subquery.c.page_view_count > int(filter_value))
                elif operator == 'less':
                    query = query.filter(page_views_subquery.c.page_view_count < int(filter_value))
                elif operator == 'greater_equal':
                    query = query.filter(page_views_subquery.c.page_view_count >= int(filter_value))
                elif operator == 'less_equal':
                    query = query.filter(page_views_subquery.c.page_view_count <= int(filter_value))
                else:
                    query = query.filter(page_views_subquery.c.page_view_count == int(filter_value))
                
                print(f"    ✅ Applied page_views_per_session {operator} {filter_value}")
            
            # Special handling for sessions_per_visitor (calculated metric)
            elif filter_key == "sessions_per_visitor":
                # Check if there's an operator for this filter
                operator_key = f"{filter_key}_operator"
                operator = filters.get(operator_key, 'equals')
                
                # Create subquery that counts sessions per visitor
                sessions_per_visitor_subquery = db.query(
                    models.Visit.visitor_id,
                    func.count(models.Visit.id).label('session_count')
                ).group_by(models.Visit.visitor_id).subquery()
                
                # Join with the subquery
                query = query.join(
                    sessions_per_visitor_subquery,
                    models.Visit.visitor_id == sessions_per_visitor_subquery.c.visitor_id
                )
                
                # Apply the filter on the calculated session count
                if operator == 'equals':
                    query = query.filter(sessions_per_visitor_subquery.c.session_count == int(filter_value))
                elif operator == 'greater':
                    query = query.filter(sessions_per_visitor_subquery.c.session_count > int(filter_value))
                elif operator == 'less':
                    query = query.filter(sessions_per_visitor_subquery.c.session_count < int(filter_value))
                elif operator == 'greater_equal':
                    query = query.filter(sessions_per_visitor_subquery.c.session_count >= int(filter_value))
                elif operator == 'less_equal':
                    query = query.filter(sessions_per_visitor_subquery.c.session_count <= int(filter_value))
                else:
                    query = query.filter(sessions_per_visitor_subquery.c.session_count == int(filter_value))
                
                print(f"    ✅ Applied sessions_per_visitor {operator} {filter_value}")
            
            # Special handling for engagement_sessions_per_visitor (alias for sessions_per_visitor)
            elif filter_key == "engagement_sessions_per_visitor":
                # Check if there's an operator for this filter
                operator_key = f"{filter_key}_operator"
                operator = filters.get(operator_key, 'equals')
                
                # Create subquery that counts sessions per visitor
                sessions_per_visitor_subquery = db.query(
                    models.Visit.visitor_id,
                    func.count(models.Visit.id).label('session_count')
                ).group_by(models.Visit.visitor_id).subquery()
                
                # Join with the subquery
                query = query.join(
                    sessions_per_visitor_subquery,
                    models.Visit.visitor_id == sessions_per_visitor_subquery.c.visitor_id
                )
                
                # Apply the filter on the calculated session count
                if operator == 'equals':
                    query = query.filter(sessions_per_visitor_subquery.c.session_count == int(filter_value))
                elif operator == 'greater':
                    query = query.filter(sessions_per_visitor_subquery.c.session_count > int(filter_value))
                elif operator == 'less':
                    query = query.filter(sessions_per_visitor_subquery.c.session_count < int(filter_value))
                elif operator == 'greater_equal':
                    query = query.filter(sessions_per_visitor_subquery.c.session_count >= int(filter_value))
                elif operator == 'less_equal':
                    query = query.filter(sessions_per_visitor_subquery.c.session_count <= int(filter_value))
                else:
                    query = query.filter(sessions_per_visitor_subquery.c.session_count == int(filter_value))
                
                print(f"    ✅ Applied engagement_sessions_per_visitor {operator} {filter_value}")
            
            # Special handling for page URL filtering (page, page_page, entry_page, last_page_of_session, engagement_exit_link)
            elif filter_key in ["page", "page_page", "entry_page", "last_page_of_session", "engagement_exit_link"]:
                # Check if there's an operator for this filter
                operator_key = f"{filter_key}_operator"
                operator = filters.get(operator_key, 'contains')
                
                # For page filtering, we need to handle it at the endpoint level since each endpoint has different page fields
                # We'll add a marker that the endpoint will handle
                if hasattr(query, 'page_filter_applied'):
                    query.page_filter_applied = True
                else:
                    query.page_filter_applied = True
                
                print(f"    📝 Page filter {filter_key} {operator} {filter_value} marked for endpoint-level processing")
            
            # Special handling for traffic_sources (classification-based filtering)
            elif filter_key == "traffic_sources":
                # Traffic source filtering requires custom logic since it's based on classification
                # We need to filter visits based on their referrer classification
                
                if filter_value == "direct":
                    # Direct traffic: no referrer or null/undefined
                    query = query.filter(
                        (models.Visit.referrer.is_(None)) | 
                        (models.Visit.referrer == "") |
                        (models.Visit.referrer.in_(["direct", "null", "undefined"]))
                    )
                elif filter_value == "organic":
                    # Organic search: contains search engine domains
                    organic_conditions = []
                    for engine in SEARCH_ENGINES:
                        organic_conditions.append(models.Visit.referrer.ilike(f"%{engine}%"))
                    query = query.filter(func.or_(*organic_conditions))
                elif filter_value == "social":
                    # Social media: contains social media domains
                    social_conditions = []
                    for social in SOCIAL_SITES:
                        social_conditions.append(models.Visit.referrer.ilike(f"%{social}%"))
                    query = query.filter(func.or_(*social_conditions))
                elif filter_value == "ai":
                    # AI tools: contains AI tool domains
                    ai_conditions = []
                    for ai in AI_TOOLS:
                        ai_conditions.append(models.Visit.referrer.ilike(f"%{ai}%"))
                    query = query.filter(func.or_(*ai_conditions))
                elif filter_value == "email":
                    # Email: contains email provider domains
                    email_conditions = []
                    for email in EMAIL_PROVIDERS:
                        email_conditions.append(models.Visit.referrer.ilike(f"%{email}%"))
                    query = query.filter(func.or_(*email_conditions))
                elif filter_value == "paid":
                    # Paid traffic: contains paid markers
                    paid_conditions = []
                    for paid in PAID_MARKERS:
                        paid_conditions.append(models.Visit.referrer.ilike(f"%{paid}%"))
                    query = query.filter(func.or_(*paid_conditions))
                elif filter_value == "utm":
                    # UTM campaigns: contains UTM markers
                    utm_conditions = []
                    for utm in UTM_MARKERS:
                        utm_conditions.append(models.Visit.referrer.ilike(f"%{utm}%"))
                    query = query.filter(func.or_(*utm_conditions))
                elif filter_value == "referral":
                    # Referral: everything else that's not direct and not empty
                    query = query.filter(
                        models.Visit.referrer.isnot(None),
                        models.Visit.referrer != "",
                        ~models.Visit.referrer.in_(["direct", "null", "undefined"])
                    )
                    # Exclude search engines, social, AI tools, email, paid, and UTM
                    exclude_conditions = []
                    all_excludes = SEARCH_ENGINES + SOCIAL_SITES + AI_TOOLS + EMAIL_PROVIDERS + PAID_MARKERS + UTM_MARKERS
                    for exclude in all_excludes:
                        exclude_conditions.append(~models.Visit.referrer.ilike(f"%{exclude}%"))
                    query = query.filter(func.and_(*exclude_conditions))
                
                print(f"    ✅ Applied traffic_sources filter: {filter_value}")
            else:
                # Check if there's an operator for this filter
                operator_key = f"{filter_key}_operator"
                operator = filters.get(operator_key, 'equals')
                
                if operator == 'equals':
                    query = query.filter(getattr(models.Visit, db_field) == filter_value)
                elif operator == 'greater':
                    query = query.filter(getattr(models.Visit, db_field) > float(filter_value))
                elif operator == 'less':
                    query = query.filter(getattr(models.Visit, db_field) < float(filter_value))
                elif operator == 'greater_equal':
                    query = query.filter(getattr(models.Visit, db_field) >= float(filter_value))
                elif operator == 'less_equal':
                    query = query.filter(getattr(models.Visit, db_field) <= float(filter_value))
                else:  # Default to contains for text fields
                    query = query.filter(getattr(models.Visit, db_field).ilike(f"%{filter_value}%"))
                
                print(f"    ✅ Applied {db_field} {operator} {filter_value}")
        else:
            print(f"    ❌ Unknown filter key: {filter_key}")
    
    print(f"🔍 Final query with filters applied")
    return query

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
    limit: Optional[int] = 10,
    offset: Optional[int] = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    # Add all possible filter parameters as query params
    country_city: Optional[str] = Query(None),
    browser: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    utm_source: Optional[str] = Query(None),
    utm_medium: Optional[str] = Query(None),
    utm_campaign: Optional[str] = Query(None),
    traffic_utm_campaign: Optional[str] = Query(None),
    traffic_utm_source: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    platform_os: Optional[str] = Query(None),
    system_platform_os: Optional[str] = Query(None),
    session_length_min: Optional[str] = Query(None),
    session_length_max: Optional[str] = Query(None),
    engagement_session_length_min: Optional[str] = Query(None),
    engagement_session_length_max: Optional[str] = Query(None),
    page_views: Optional[str] = Query(None),
    page_views_per_session: Optional[str] = Query(None),
    sessions_per_visitor: Optional[str] = Query(None),
    engagement_sessions_per_visitor: Optional[str] = Query(None),
    engagement_exit_link: Optional[str] = Query(None),
    traffic_sources: Optional[str] = Query(None),
    page_page: Optional[str] = Query(None),
    page_entry_page: Optional[str] = Query(None),
    location_ip_address: Optional[str] = Query(None),
    # Operator parameters
    country_city_operator: Optional[str] = Query(None),
    browser_operator: Optional[str] = Query(None),
    device_operator: Optional[str] = Query(None),
    utm_source_operator: Optional[str] = Query(None),
    utm_medium_operator: Optional[str] = Query(None),
    utm_campaign_operator: Optional[str] = Query(None),
    traffic_utm_campaign_operator: Optional[str] = Query(None),
    traffic_utm_source_operator: Optional[str] = Query(None),
    language_operator: Optional[str] = Query(None),
    platform_os_operator: Optional[str] = Query(None),
    system_platform_os_operator: Optional[str] = Query(None),
    session_length_operator: Optional[str] = Query(None),
    engagement_session_length_operator: Optional[str] = Query(None),
    page_views_operator: Optional[str] = Query(None),
    page_views_per_session_operator: Optional[str] = Query(None),
    sessions_per_visitor_operator: Optional[str] = Query(None),
    engagement_sessions_per_visitor_operator: Optional[str] = Query(None),
    engagement_exit_link_operator: Optional[str] = Query(None),
    page_page_operator: Optional[str] = Query(None),
    location_ip_address_operator: Optional[str] = Query(None),
):
    """Optimized most visited pages with visit data included"""
    try:
        print(f"🔍 Getting most visited pages for project {project_id}")
        print(f"📅 Date range: {start_date} to {end_date}")
        print(f"📊 Limit: {limit}, Offset: {offset}")
        
        # Collect all filter parameters into a dictionary
        filters = {
            'country_city': country_city,
            'browser': browser,
            'device': device,
            'utm_source': utm_source,
            'utm_medium': utm_medium,
            'utm_campaign': utm_campaign,
            'traffic_utm_campaign': traffic_utm_campaign,
            'traffic_utm_source': traffic_utm_source,
            'language': language,
            'platform_os': platform_os,
            'system_platform_os': system_platform_os,
            'session_length_min': session_length_min,
            'session_length_max': session_length_max,
            'engagement_session_length_min': engagement_session_length_min,
            'engagement_session_length_max': engagement_session_length_max,
            'page_views': page_views,
            'page_views_per_session': page_views_per_session,
            'sessions_per_visitor': sessions_per_visitor,
            'engagement_sessions_per_visitor': engagement_sessions_per_visitor,
            'engagement_exit_link': engagement_exit_link,
            'traffic_sources': traffic_sources,            'page_page': page_page,
            'page_entry_page': page_entry_page,
            'location_ip_address': location_ip_address,
            'country_city_operator': country_city_operator,
            'browser_operator': browser_operator,
            'device_operator': device_operator,
            'utm_source_operator': utm_source_operator,
            'utm_medium_operator': utm_medium_operator,
            'utm_campaign_operator': utm_campaign_operator,
            'traffic_utm_campaign_operator': traffic_utm_campaign_operator,
            'traffic_utm_source_operator': traffic_utm_source_operator,
            'language_operator': language_operator,
            'platform_os_operator': platform_os_operator,
            'system_platform_os_operator': system_platform_os_operator,
            'session_length_operator': session_length_operator,
            'engagement_session_length_operator': engagement_session_length_operator,
            'page_views_operator': page_views_operator,
            'page_views_per_session_operator': page_views_per_session_operator,
            'sessions_per_visitor_operator': sessions_per_visitor_operator,
            'engagement_sessions_per_visitor_operator': engagement_sessions_per_visitor_operator,
            'engagement_exit_link_operator': engagement_exit_link_operator,            'page_page_operator': page_page_operator,
            'location_ip_address_operator': location_ip_address_operator
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        print(f"🔍 Custom filters: {filters}")

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

        # Apply custom filters
        print(f"🔍 DEBUG: Filters being passed to apply_filters_to_query: {filters}")
        query = apply_filters_to_query(query, filters, db)
        
        # Apply page-specific filtering if page_page filter is provided
        if page_page:
            print(f"🔍 Applying page_page filter: {page_page}")
            # For most visited pages, we filter on the base_url_exp which comes from PageView.url
            # This needs to be applied after the main query but before grouping
            query = query.having(func.split_part(models.PageView.url, '?', 1).ilike(f"%{page_page}%"))
            print(f"    ✅ Applied page_page filter to most visited pages")
        
        # Apply page_entry_page filtering if provided
        if page_entry_page:
            print(f"🔍 Applying page_entry_page filter: {page_entry_page}")
            # For most visited pages, we filter on the base_url_exp which comes from PageView.url
            # This needs to be applied after the main query but before grouping
            query = query.having(func.split_part(models.PageView.url, '?', 1).ilike(f"%{page_entry_page}%"))
            print(f"    ✅ Applied page_entry_page filter to most visited pages")
        
        # Apply engagement_exit_link filtering if provided
        if engagement_exit_link:
            print(f"🔍 Applying engagement_exit_link filter: {engagement_exit_link}")
            # For most visited pages, we filter on the base_url_exp which comes from PageView.url
            # This needs to be applied after the main query but before grouping
            query = query.having(func.split_part(models.PageView.url, '?', 1).ilike(f"%{engagement_exit_link}%"))
            print(f"    ✅ Applied engagement_exit_link filter to most visited pages")
        
        # Debug: Check if filters were actually applied
        print(f"🔍 Query after filters applied: {query}")
        print(f"🔍 Filtered query will be executed...")
        
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
            # Simplified bounce rate - use reasonable defaults
            bounce_rate = 35.0 if total_views > 1 else 0.0
            
            # Get actual visits for this page - similar to entry/exit pages
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
                "url": base_url,
                "title": title or base_url,
                "total_views": total_views,
                "unique_sessions": unique_sessions,
                "avg_time_spent": float(avg_time_spent) if avg_time_spent else 0.0,
                "bounce_rate": bounce_rate,
                "visits": visits_for_page  # Add visits data like entry/exit pages
            })

        print(f"✅ Successfully processed {len(result)} pages")
        return {
            "data": result,
            "has_more": len(result) == limit,
            "total_loaded": offset + len(result)
        }

    except Exception as e:
        print(f"❌ Error in get_most_visited_pages: {e}")
        import traceback
        traceback.print_exc()
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
    db: Session = Depends(get_db),
    # Add all possible filter parameters as query params
    country_city: Optional[str] = Query(None),
    browser: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    utm_source: Optional[str] = Query(None),
    utm_medium: Optional[str] = Query(None),
    utm_campaign: Optional[str] = Query(None),
    traffic_utm_campaign: Optional[str] = Query(None),
    traffic_utm_source: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    platform_os: Optional[str] = Query(None),
    system_platform_os: Optional[str] = Query(None),
    session_length_min: Optional[str] = Query(None),
    session_length_max: Optional[str] = Query(None),
    engagement_session_length_min: Optional[str] = Query(None),
    engagement_session_length_max: Optional[str] = Query(None),
    page_views: Optional[str] = Query(None),
    page_views_per_session: Optional[str] = Query(None),
    sessions_per_visitor: Optional[str] = Query(None),
    engagement_sessions_per_visitor: Optional[str] = Query(None),
    engagement_exit_link: Optional[str] = Query(None),
    traffic_sources: Optional[str] = Query(None),
    page_page: Optional[str] = Query(None),
    page_entry_page: Optional[str] = Query(None),
    location_ip_address: Optional[str] = Query(None),
    # Operator parameters
    country_city_operator: Optional[str] = Query(None),
    browser_operator: Optional[str] = Query(None),
    device_operator: Optional[str] = Query(None),
    utm_source_operator: Optional[str] = Query(None),
    utm_medium_operator: Optional[str] = Query(None),
    utm_campaign_operator: Optional[str] = Query(None),
    traffic_utm_campaign_operator: Optional[str] = Query(None),
    traffic_utm_source_operator: Optional[str] = Query(None),
    language_operator: Optional[str] = Query(None),
    platform_os_operator: Optional[str] = Query(None),
    system_platform_os_operator: Optional[str] = Query(None),
    session_length_operator: Optional[str] = Query(None),
    engagement_session_length_operator: Optional[str] = Query(None),
    page_views_operator: Optional[str] = Query(None),
    page_views_per_session_operator: Optional[str] = Query(None),
    sessions_per_visitor_operator: Optional[str] = Query(None),
    engagement_sessions_per_visitor_operator: Optional[str] = Query(None),
    engagement_exit_link_operator: Optional[str] = Query(None),
    page_page_operator: Optional[str] = Query(None),
    location_ip_address_operator: Optional[str] = Query(None),
):
    """Optimized entry pages with chunked loading"""
    try:
        print(f"🔍 Getting entry pages for project {project_id}")
        print(f"📅 Date range: {start_date} to {end_date}")
        
        # Collect all filter parameters into a dictionary
        filters = {
            'country_city': country_city,
            'browser': browser,
            'device': device,
            'utm_source': utm_source,
            'utm_medium': utm_medium,
            'utm_campaign': utm_campaign,
            'traffic_utm_campaign': traffic_utm_campaign,
            'traffic_utm_source': traffic_utm_source,
            'language': language,
            'platform_os': platform_os,
            'system_platform_os': system_platform_os,
            'session_length_min': session_length_min,
            'session_length_max': session_length_max,
            'engagement_session_length_min': engagement_session_length_min,
            'engagement_session_length_max': engagement_session_length_max,
            'page_views': page_views,
            'page_views_per_session': page_views_per_session,
            'sessions_per_visitor': sessions_per_visitor,
            'engagement_sessions_per_visitor': engagement_sessions_per_visitor,
            'engagement_exit_link': engagement_exit_link,
            'traffic_sources': traffic_sources,            'page_page': page_page,
            'page_entry_page': page_entry_page,
            'location_ip_address': location_ip_address,
            'country_city_operator': country_city_operator,
            'browser_operator': browser_operator,
            'device_operator': device_operator,
            'utm_source_operator': utm_source_operator,
            'utm_medium_operator': utm_medium_operator,
            'utm_campaign_operator': utm_campaign_operator,
            'traffic_utm_campaign_operator': traffic_utm_campaign_operator,
            'traffic_utm_source_operator': traffic_utm_source_operator,
            'language_operator': language_operator,
            'platform_os_operator': platform_os_operator,
            'system_platform_os_operator': system_platform_os_operator,
            'session_length_operator': session_length_operator,
            'engagement_session_length_operator': engagement_session_length_operator,
            'page_views_operator': page_views_operator,
            'page_views_per_session_operator': page_views_per_session_operator,
            'sessions_per_visitor_operator': sessions_per_visitor_operator,
            'engagement_sessions_per_visitor_operator': engagement_sessions_per_visitor_operator,
            'engagement_exit_link_operator': engagement_exit_link_operator,            'page_page_operator': page_page_operator,
            'location_ip_address_operator': location_ip_address_operator
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        print(f"🔍 Custom filters: {filters}")

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

        # Apply custom filters
        query = apply_filters_to_query(query, filters, db)
        
        # Apply page-specific filtering if page_page filter is provided
        if page_page:
            print(f"🔍 Applying page_page filter to entry pages: {page_page}")
            # For entry pages, we filter on the entry_page field
            query = query.having(func.split_part(models.Visit.entry_page, '?', 1).ilike(f"%{page_page}%"))
            print(f"    ✅ Applied page_page filter to entry pages")

        # Apply page_entry_page filtering if provided
        if page_entry_page:
            print(f"🔍 Applying page_entry_page filter to entry pages: {page_entry_page}")
            # For entry pages, we filter on the entry_page field
            query = query.having(func.split_part(models.Visit.entry_page, '?', 1).ilike(f"%{page_entry_page}%"))
            print(f"    ✅ Applied page_entry_page filter to entry pages")

        # Apply engagement_exit_link filtering if provided
        if engagement_exit_link:
            print(f"🔍 Applying engagement_exit_link filter to entry pages: {engagement_exit_link}")
            # For entry pages, we filter on the entry_page field
            query = query.having(func.split_part(models.Visit.entry_page, '?', 1).ilike(f"%{engagement_exit_link}%"))
            print(f"    ✅ Applied engagement_exit_link filter to entry pages")

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
    limit: Optional[int] = 10,
    offset: Optional[int] = 0,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db),
    # Add all possible filter parameters as query params
    country_city: Optional[str] = Query(None),
    browser: Optional[str] = Query(None),
    device: Optional[str] = Query(None),
    utm_source: Optional[str] = Query(None),
    utm_medium: Optional[str] = Query(None),
    utm_campaign: Optional[str] = Query(None),
    traffic_utm_campaign: Optional[str] = Query(None),
    traffic_utm_source: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    platform_os: Optional[str] = Query(None),
    system_platform_os: Optional[str] = Query(None),
    session_length_min: Optional[str] = Query(None),
    session_length_max: Optional[str] = Query(None),
    engagement_session_length_min: Optional[str] = Query(None),
    engagement_session_length_max: Optional[str] = Query(None),
    page_views: Optional[str] = Query(None),
    page_views_per_session: Optional[str] = Query(None),
    sessions_per_visitor: Optional[str] = Query(None),
    engagement_sessions_per_visitor: Optional[str] = Query(None),
    engagement_exit_link: Optional[str] = Query(None),
    traffic_sources: Optional[str] = Query(None),
    page_page: Optional[str] = Query(None),
    page_entry_page: Optional[str] = Query(None),
    location_ip_address: Optional[str] = Query(None),
    # Operator parameters
    country_city_operator: Optional[str] = Query(None),
    browser_operator: Optional[str] = Query(None),
    device_operator: Optional[str] = Query(None),
    utm_source_operator: Optional[str] = Query(None),
    utm_medium_operator: Optional[str] = Query(None),
    utm_campaign_operator: Optional[str] = Query(None),
    traffic_utm_campaign_operator: Optional[str] = Query(None),
    traffic_utm_source_operator: Optional[str] = Query(None),
    language_operator: Optional[str] = Query(None),
    platform_os_operator: Optional[str] = Query(None),
    system_platform_os_operator: Optional[str] = Query(None),
    session_length_operator: Optional[str] = Query(None),
    engagement_session_length_operator: Optional[str] = Query(None),
    page_views_operator: Optional[str] = Query(None),
    page_views_per_session_operator: Optional[str] = Query(None),
    sessions_per_visitor_operator: Optional[str] = Query(None),
    engagement_sessions_per_visitor_operator: Optional[str] = Query(None),
    engagement_exit_link_operator: Optional[str] = Query(None),
    page_page_operator: Optional[str] = Query(None),
    location_ip_address_operator: Optional[str] = Query(None),
 ):
    """Simplified exit pages - get last page view from each session"""
    try:
        print(f"🔍 Getting exit pages for project {project_id}")
        print(f"📅 Date range: {start_date} to {end_date}")
        
        # Collect all filter parameters into a dictionary
        filters = {
            'country_city': country_city,
            'browser': browser,
            'device': device,
            'utm_source': utm_source,
            'utm_medium': utm_medium,
            'utm_campaign': utm_campaign,
            'traffic_utm_campaign': traffic_utm_campaign,
            'traffic_utm_source': traffic_utm_source,
            'language': language,
            'platform_os': platform_os,
            'system_platform_os': system_platform_os,
            'session_length_min': session_length_min,
            'session_length_max': session_length_max,
            'engagement_session_length_min': engagement_session_length_min,
            'engagement_session_length_max': engagement_session_length_max,
            'page_views': page_views,
            'page_views_per_session': page_views_per_session,
            'sessions_per_visitor': sessions_per_visitor,
            'engagement_sessions_per_visitor': engagement_sessions_per_visitor,
            'engagement_exit_link': engagement_exit_link,
            'traffic_sources': traffic_sources,            'page_page': page_page,
            'page_entry_page': page_entry_page,
            'location_ip_address': location_ip_address,
            'country_city_operator': country_city_operator,
            'browser_operator': browser_operator,
            'device_operator': device_operator,
            'utm_source_operator': utm_source_operator,
            'utm_medium_operator': utm_medium_operator,
            'utm_campaign_operator': utm_campaign_operator,
            'traffic_utm_campaign_operator': traffic_utm_campaign_operator,
            'traffic_utm_source_operator': traffic_utm_source_operator,
            'language_operator': language_operator,
            'platform_os_operator': platform_os_operator,
            'system_platform_os_operator': system_platform_os_operator,
            'session_length_operator': session_length_operator,
            'engagement_session_length_operator': engagement_session_length_operator,
            'page_views_operator': page_views_operator,
            'page_views_per_session_operator': page_views_per_session_operator,
            'sessions_per_visitor_operator': sessions_per_visitor_operator,
            'engagement_sessions_per_visitor_operator': engagement_sessions_per_visitor_operator,
            'engagement_exit_link_operator': engagement_exit_link_operator,            'page_page_operator': page_page_operator,
            'location_ip_address_operator': location_ip_address_operator
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        print(f"🔍 Custom filters: {filters}")
        
        start_dt, end_dt = normalize_date_range(start_date, end_date)

        # Simple query: Get last page view for each session
        last_page_query = db.query(
            models.PageView.url,
            models.PageView.visit_id,
            models.PageView.viewed_at,
            models.Visit.visitor_id
        ).join(models.Visit).filter(
            models.Visit.project_id == project_id
        )
        
        if start_dt:
            last_page_query = last_page_query.filter(models.Visit.visited_at >= start_dt)
        if end_dt:
            last_page_query = last_page_query.filter(models.Visit.visited_at <= end_dt)
        
        # Apply custom filters
        last_page_query = apply_filters_to_query(last_page_query, filters, db)
        
        # Get all page views and find the last one for each visit
        all_views = last_page_query.order_by(models.PageView.visit_id, models.PageView.viewed_at.desc()).all()
        
        # Group by visit_id and get the last page view for each visit
        visit_last_pages = {}
        for view in all_views:
            if view.visit_id not in visit_last_pages:
                visit_last_pages[view.visit_id] = view
        
        # Count exit pages
        exit_page_counts = {}
        for visit_id, last_view in visit_last_pages.items():
            base_url = last_view.url.split('?')[0] if last_view.url else 'Unknown'
            
            # Apply page_page filter if provided
            if page_page and page_page.lower() not in base_url.lower():
                continue  # Skip this page if it doesn't match the filter
        
            # Apply page_entry_page filter if provided
            if page_entry_page and page_entry_page.lower() not in base_url.lower():
                continue  # Skip this page if it doesn't match the filter
        
            # Apply engagement_exit_link filter if provided
            if engagement_exit_link and engagement_exit_link.lower() not in base_url.lower():
                continue  # Skip this page if it doesn't match the filter
                
            exit_page_counts[base_url] = exit_page_counts.get(base_url, 0) + 1
        
        # Convert to result format
        result = []
        for base_url, count in sorted(exit_page_counts.items(), key=lambda x: x[1], reverse=True):
            if len(result) >= limit:
                break
                
            # Get actual visits for this exit page
            visits_for_page = []
            page_visits = db.query(models.Visit).join(models.PageView).filter(
                models.Visit.project_id == project_id,
                models.PageView.url.like(f"{base_url}%")
            )
            
            if start_dt:
                page_visits = page_visits.filter(models.Visit.visited_at >= start_dt)
            if end_dt:
                page_visits = page_visits.filter(models.Visit.visited_at <= end_dt)
            
            # Apply filters to get the actual visits that exited on this page
            page_visits = apply_filters_to_query(page_visits, filters, db)
            
            # Get visits data
            visits_data = page_visits.order_by(desc(models.Visit.visited_at)).limit(100).all()
            
            for visit in visits_data:
                visits_for_page.append({
                    "session_id": visit.session_id,
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
                "exits": count,
                "unique_visitors": len(set(v.visitor_id for v in visit_last_pages.values() 
                                        if v.url and v.url.split('?')[0] == base_url)),
                "exit_rate": 100.0,  # Simplified
                "bounce_rate": 0.0,   # Simplified
                "total_page_views": count,
                "visits": visits_for_page  # Add actual visits data
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
