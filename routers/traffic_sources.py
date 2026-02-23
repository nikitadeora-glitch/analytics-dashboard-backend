from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from sqlalchemy import func, desc

from database import get_db

import models

from datetime import datetime, timedelta

from typing import Optional

from pytz import timezone



# Local date normalization function to avoid circular dependency

def normalize_date_range(start_date: str | None, end_date: str | None):

    """

    Normalize date range to IST calendar days, then convert to UTC for database queries.

    This ensures consistency across all endpoints.

    """

    start_dt = end_dt = None

    

    print(f"🔍 Input dates - Start: {start_date}, End: {end_date}")



    try:

        if start_date:

            if "T" in start_date:

                # ISO format with time - parse as UTC

                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))

            else:

                # YYYY-MM-DD format - set to start of day in IST

                ist = timezone("Asia/Kolkata")

                start_dt = ist.localize(datetime.strptime(start_date, "%Y-%m-%d").replace(hour=0, minute=0, second=0))

            

            # Convert to UTC for database

            if start_dt.tzinfo is not None:

                start_dt = start_dt.astimezone(timezone("UTC"))



        if end_date:

            if "T" in end_date:

                # ISO format with time - parse as UTC

                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

            else:

                # YYYY-MM-DD format - set to end of day in IST

                ist = timezone("Asia/Kolkata")

                end_dt = ist.localize(datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59))

            

            # Convert to UTC for database

            if end_dt.tzinfo is not None:

                end_dt = end_dt.astimezone(timezone("UTC"))



        print(f"🔍 Normalized dates - Start: {start_dt}, End: {end_dt}")

        return start_dt, end_dt



    except Exception as e:

        print(f"❌ Date normalization error: {e}")

        return None, None



router = APIRouter()



# ================================

# UNIFIED TRAFFIC SOURCE CLASSIFICATION

# ================================



# Constants for classification

SEARCH_ENGINES = ["google", "bing", "yahoo", "duckduckgo", "baidu"]

SOCIAL_SITES = ["facebook", "twitter", "instagram", "linkedin", "youtube", "tiktok", "pinterest"]

AI_TOOLS = ["chatgpt", "claude", "gemini", "copilot", "perplexity"]

EMAIL_PROVIDERS = ["mail", "gmail", "outlook", "yahoo.com"]

PAID_MARKERS = ["ads", "adwords", "facebook.com/tr"]

UTM_MARKERS = ["utm_", "campaign"]

# Filter mapping dictionary - maps frontend filter IDs to database fields
FILTER_MAP = {
    "country_city": "country",
    "browser": "browser", 
    "device": "device_type",
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
    "traffic_utm_medium": "utm_medium",
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
            
            # Special handling for page_views_per_session (calculated metric)
            if filter_key == "page_views_per_session":
                # Check if there's an operator for this filter
                operator_key = f"{filter_key}_operator"
                operator = filters.get(operator_key, 'equals')
                
                # Create subquery that counts page views per visit
                from sqlalchemy import select
                page_views_subquery = select(
                    models.PageView.visit_id,
                    func.count(models.PageView.id).label('page_view_count')
                ).group_by(models.PageView.visit_id).subquery()
                
                # Join with the subquery
                query = query.outerjoin(
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
            
            # Special handling for engagement_sessions_per_visitor (calculated metric)
            elif filter_key == "engagement_sessions_per_visitor":
                # Check if there's an operator for this filter
                operator_key = f"{filter_key}_operator"
                operator = filters.get(operator_key, 'equals')
                
                # Create subquery that counts sessions per visitor
                from sqlalchemy import select
                sessions_per_visitor_subquery = select(
                    models.Visit.visitor_id,
                    func.count(models.Visit.id).label('session_count')
                ).group_by(models.Visit.visitor_id).subquery()
                
                # Join with the subquery
                query = query.outerjoin(
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


def classify_source(referrer: str) -> str:

    """

    Single source of truth for traffic source classification.

    This ensures consistency between summary and detail APIs.

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



@router.get("/{project_id}/sources")

def get_traffic_sources(

    project_id: int,

    start_date: Optional[str] = None,

    end_date: Optional[str] = None,

    traffic_sources: Optional[str] = None,

    country_city: Optional[str] = None,

    location_ip_address: Optional[str] = None,

    system_platform_os: Optional[str] = None,

    engagement_session_length_min: Optional[int] = None,

    engagement_session_length_max: Optional[int] = None,

    engagement_session_length_operator: Optional[str] = None,

    engagement_sessions_per_visitor: Optional[int] = None,

    engagement_sessions_per_visitor_operator: Optional[str] = None,

    page_views_per_session: Optional[int] = None,

    page_views_per_session_operator: Optional[str] = None,

    utm_source: Optional[str] = None,

    utm_medium: Optional[str] = None,

    utm_campaign: Optional[str] = None,

    traffic_utm_source: Optional[str] = None,

    traffic_utm_medium: Optional[str] = None,

    traffic_utm_campaign: Optional[str] = None,

    db: Session = Depends(get_db)

    ):

    try:

        print(f"🔍 Getting traffic sources for project {project_id}")

        print(f"📅 Date range: {start_date} to {end_date}")

        if traffic_sources:
            print(f"🎯 Traffic sources filter: {traffic_sources}")

        if country_city:
            print(f"🌍 Country/City filter: {country_city}")

        if location_ip_address:
            print(f"🌐 IP Address filter: {location_ip_address}")

        if system_platform_os:
            print(f"💻 OS filter: {system_platform_os}")

        

        # -----------------------------

        # Parse dates using same normalization as reports

        # -----------------------------

        start_dt = None

        end_dt = None



        if start_date and end_date:

            try:

                print(f"🌐 Raw dates from frontend: start_date={start_date}, end_date={end_date}")

                

                # Use the same date normalization as reports endpoint

                start_dt, end_dt = normalize_date_range(start_date, end_date)

                

                print(f"🌐 Backend date filtering (IST normalized): {start_dt} to {end_dt}")

            except ValueError as e:

                print(f"❌ Date parsing error: {e}")

                # Continue without date filtering if parsing fails



        # -----------------------------

        # Get visits and analyze referrers

        # -----------------------------

        visits_query = db.query(models.Visit).filter(

            models.Visit.project_id == project_id

        )



        # Apply date filtering

        if start_dt and end_dt:

            visits_query = visits_query.filter(

                models.Visit.visited_at >= start_dt,

                models.Visit.visited_at <= end_dt

            )

        # Apply custom filters using the unified filter function
        filter_params = {
            'country_city': country_city,
            'location_ip_address': location_ip_address,
            'system_platform_os': system_platform_os,
            'engagement_session_length_min': engagement_session_length_min,
            'engagement_session_length_max': engagement_session_length_max,
            'engagement_session_length_operator': engagement_session_length_operator,
            'engagement_sessions_per_visitor': engagement_sessions_per_visitor,
            'engagement_sessions_per_visitor_operator': engagement_sessions_per_visitor_operator,
            'page_views_per_session': page_views_per_session,
            'page_views_per_session_operator': page_views_per_session_operator,
            'utm_source': utm_source,
            'utm_medium': utm_medium,
            'utm_campaign': utm_campaign,
            'traffic_utm_source': traffic_utm_source,
            'traffic_utm_medium': traffic_utm_medium,
            'traffic_utm_campaign': traffic_utm_campaign
        }
        
        # Remove None values
        filter_params = {k: v for k, v in filter_params.items() if v is not None}
        
        if filter_params:
            visits_query = apply_filters_to_query(visits_query, filter_params, db)



        visits = visits_query.all()

        print(f"📊 Found {len(visits)} visits in date range with engagement and page views filters")



        if not visits:

            print("⚠️ No visits found in the specified date range")

            return []



        # -----------------------------

        # Categorize visits by traffic source

        # -----------------------------

        source_groups = {

            "direct": {"count": 0, "visits": []},

            "organic": {"count": 0, "visits": []},

            "social": {"count": 0, "visits": []},

            "referral": {"count": 0, "visits": []},

            "email": {"count": 0, "visits": []},

            "paid": {"count": 0, "visits": []},

            "ai": {"count": 0, "visits": []},

            "utm": {"count": 0, "visits": []}

        }



        for visit in visits:

            source_type = classify_source(visit.referrer)

            source_groups[source_type]["count"] += 1

            source_groups[source_type]["visits"].append(visit)



        print(f"🎯 Categorized visits:")

        for source_type, data in source_groups.items():

            print(f"   {source_type}: {data['count']} visits")



        # -----------------------------

        # Calculate bounce rates and build result

        # -----------------------------

        result = []

        total_visits = len(visits)



        source_names = {

            "direct": "Direct Traffic",

            "organic": "Organic Search", 

            "social": "Organic Social",

            "referral": "Website Referrals",

            "email": "Email",

            "paid": "Paid Traffic",

            "ai": "AI Chatbot",

            "utm": "UTM Campaigns"

        }



        for source_type, data in source_groups.items():

            # Apply traffic_sources filter if specified
            if traffic_sources and source_type != traffic_sources:
                continue

            if data["count"] > 0:  # Only include sources with visits

                # Calculate bounce rate - more realistic logic

                bounced = 0

                for v in data["visits"]:

                    # Method 1: Same entry and exit page (definite bounce)

                    if v.entry_page and v.exit_page and v.entry_page == v.exit_page:

                        bounced += 1

                    # Method 2: Very short session duration (definite bounce)

                    elif v.session_duration and v.session_duration <= 30:

                        bounced += 1

                    # Method 3: Skip "no exit page" cases (likely tracking issues)

                    # Only count as definite bounce when we have clear evidence

                # Calculate bounce rate - no hardcoded thresholds

                # Use whatever data is available in the filtered date range

                total_visits = len(data["visits"])

                bounce_rate = round((bounced / total_visits) * 100, 1) if total_visits > 0 else 0



                result.append({

                    "source_type": source_type,

                    "source_name": source_names.get(source_type, source_type.title()),

                    "count": data["count"],

                    "percentage": round((data["count"] / total_visits) * 100, 2) if total_visits > 0 else 0,

                    "bounce_rate": bounce_rate

                })



        # Sort by count descending

        result.sort(key=lambda x: x["count"], reverse=True)

        

        print(f"✅ Returning {len(result)} traffic source results")

        for r in result:

            print(f"   {r['source_name']}: {r['count']} visits ({r['percentage']}%, {r['bounce_rate']}% bounce)")



        return result



    except Exception as e:

        print(f"❌ Traffic source error: {e}")

        import traceback

        traceback.print_exc()

        return []





@router.get("/{project_id}/source-detail/{source_type}")

def get_traffic_source_detail(

    project_id: int,

    source_type: str,

    start_date: Optional[str] = None,

    end_date: Optional[str] = None,

    country_city: Optional[str] = None,

    location_ip_address: Optional[str] = None,

    system_platform_os: Optional[str] = None,

    engagement_session_length_min: Optional[int] = None,

    engagement_session_length_max: Optional[int] = None,

    engagement_session_length_operator: Optional[str] = None,

    engagement_sessions_per_visitor: Optional[int] = None,

    engagement_sessions_per_visitor_operator: Optional[str] = None,

    page_views_per_session: Optional[int] = None,

    page_views_per_session_operator: Optional[str] = None,

    utm_source: Optional[str] = None,

    utm_medium: Optional[str] = None,

    utm_campaign: Optional[str] = None,

    traffic_utm_source: Optional[str] = None,

    traffic_utm_medium: Optional[str] = None,

    traffic_utm_campaign: Optional[str] = None,

    db: Session = Depends(get_db)

):

    try:

        print(f"🔍 Getting traffic source detail for {source_type} in project {project_id}")

        print(f"📅 Date range: {start_date} to {end_date}")

        if country_city:
            print(f"🌍 Country/City filter: {country_city}")

        if location_ip_address:
            print(f"🌐 IP Address filter: {location_ip_address}")

        if system_platform_os:
            print(f"💻 OS filter: {system_platform_os}")

        

        # Parse dates using same normalization as reports

        start_dt = None

        end_dt = None



        if start_date and end_date:

            try:

                print(f"🌐 Raw dates from frontend: start_date={start_date}, end_date={end_date}")

                

                # Use the same date normalization as reports endpoint

                start_dt, end_dt = normalize_date_range(start_date, end_date)

                

                print(f"🌐 Backend date filtering (IST normalized): {start_dt} to {end_dt}")

            except ValueError as e:

                print(f"❌ Date parsing error: {e}")

                # Continue without date filtering if parsing fails



        # Get visits for this source type in date range

        visits_query = db.query(models.Visit).filter(

            models.Visit.project_id == project_id

        )



        if start_dt and end_dt:

            visits_query = visits_query.filter(

                models.Visit.visited_at >= start_dt,

                models.Visit.visited_at <= end_dt

            )

        # Apply custom filters using the unified filter function
        filter_params = {
            'country_city': country_city,
            'location_ip_address': location_ip_address,
            'system_platform_os': system_platform_os,
            'engagement_session_length_min': engagement_session_length_min,
            'engagement_session_length_max': engagement_session_length_max,
            'engagement_session_length_operator': engagement_session_length_operator,
            'engagement_sessions_per_visitor': engagement_sessions_per_visitor,
            'engagement_sessions_per_visitor_operator': engagement_sessions_per_visitor_operator,
            'page_views_per_session': page_views_per_session,
            'page_views_per_session_operator': page_views_per_session_operator,
            'utm_source': utm_source,
            'utm_medium': utm_medium,
            'utm_campaign': utm_campaign,
            'traffic_utm_source': traffic_utm_source,
            'traffic_utm_medium': traffic_utm_medium,
            'traffic_utm_campaign': traffic_utm_campaign
        }
        
        # Remove None values
        filter_params = {k: v for k, v in filter_params.items() if v is not None}
        
        if filter_params:
            visits_query = apply_filters_to_query(visits_query, filter_params, db)

        all_visits = visits_query.all()

        print(f"📊 Found {len(all_visits)} total visits in date range with engagement and page views filters")

        

        # Filter visits by source type using unified classification

        matching_visits = []

        for visit in all_visits:

            classified_source = classify_source(visit.referrer)

            if classified_source == source_type:

                matching_visits.append(visit)



        print(f"📊 Found {len(matching_visits)} matching visits for {source_type}")



        # Group visits by date for daily breakdown

        daily_data = {}

        

        # Calculate date range for iteration

        if start_dt and end_dt:

            current_date = start_dt.date()

            end_date_obj = end_dt.date()

        else:

            # Default to last 30 days if no dates provided

            end_date_obj = datetime.now().date()

            current_date = end_date_obj - timedelta(days=29)



        # Initialize all dates with zero values

        while current_date <= end_date_obj:

            date_str = current_date.strftime('%Y-%m-%d')

            daily_data[date_str] = {

                'date': date_str,

                'sessions': 0,

                'bounced_sessions': 0,

                'bounce_rate': 0

            }

            current_date += timedelta(days=1)



        # Fill in actual data

        for visit in matching_visits:

            visit_date = visit.visited_at.date().strftime('%Y-%m-%d')

            if visit_date in daily_data:

                daily_data[visit_date]['sessions'] += 1

                

                # Check if bounced (improved logic for tracking issues)

                # Only count as bounce if we have reliable data

                is_bounced = False

                

                # Method 1: Same entry and exit page (definite bounce)

                if visit.entry_page and visit.exit_page and visit.entry_page == visit.exit_page:

                    is_bounced = True

                # Method 2: Very short session duration (definite bounce)

                elif visit.session_duration and visit.session_duration <= 30:

                    is_bounced = True

                # Method 3: No exit page but OLD data (before tracking broke)

                elif not visit.exit_page and visit.visited_at and visit.visited_at < datetime(2025, 1, 20):

                    is_bounced = True

                # Method 4: No exit page in NEW data - DON'T count as bounce (tracking issue)

                elif not visit.exit_page and visit.visited_at and visit.visited_at >= datetime(2025, 1, 20):

                    # Skip bounce calculation for recent data due to tracking issues

                    continue

                if is_bounced:

                    daily_data[visit_date]['bounced_sessions'] += 1



        # Calculate bounce rates

        for date_str, data in daily_data.items():

            if data['sessions'] > 0:

                if data['bounce_rate'] == 0 and data['sessions'] > 0:

                    # Check if this is recent data with tracking issues

                    date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()

                    if date_obj >= datetime(2025, 1, 20).date():

                        # Show "N/A" for recent data due to tracking issues

                        data['bounce_rate'] = None

                    else:

                        # Keep 0% for old data (genuine 0% bounce)

                        data['bounce_rate'] = 0.0



        # Convert to list and sort by date

        result = list(daily_data.values())

        result.sort(key=lambda x: x['date'])



        print(f"✅ Returning {len(result)} days of data for {source_type}")

        

        return {

            "source_type": source_type,

            "total_sessions": len(matching_visits),

            "start_date": start_date,

            "end_date": end_date,

            "daily_data": result

        }



    except Exception as e:

        print(f"❌ Traffic source detail error: {e}")

        import traceback

        traceback.print_exc()

        return {"source_type": source_type, "total_sessions": 0, "daily_data": []}





@router.get("/{project_id}/traffic-overview")

def get_traffic_overview(project_id: int, db: Session = Depends(get_db)):

    """Dedicated endpoint for Traffic Sources Page"""

    # Reuse the same logic but exposed on a specific route for the page

    # This allows future customization specifically for this page without breaking others

    return get_traffic_sources(project_id, db)



@router.get("/{project_id}/keywords")

def get_keywords(project_id: int, limit: int = 20, db: Session = Depends(get_db)):

    keywords = db.query(models.Keyword).filter(

        models.Keyword.project_id == project_id

    ).order_by(desc(models.Keyword.count)).limit(limit).all()

    

    return [{

        "keyword": k.keyword,

        "search_engine": k.search_engine,

        "count": k.count,

        "last_seen": k.last_seen

    } for k in keywords]



@router.get("/{project_id}/referrers")

def get_referrers(project_id: int, db: Session = Depends(get_db)):

    referrers = db.query(

        models.Visit.referrer,

        func.count(models.Visit.id).label('count')

    ).filter(

        models.Visit.project_id == project_id,

        models.Visit.referrer.isnot(None)

    ).group_by(models.Visit.referrer).order_by(desc('count')).limit(20).all()

    

    return [{"referrer": r[0], "count": r[1]} for r in referrers]



@router.get("/{project_id}/exit-links")

def get_exit_links(

    project_id: int, 

    start_date: Optional[str] = None, 

    end_date: Optional[str] = None,

    limit: int = 100,
    
    # Filter parameters
    country_city: Optional[str] = None,
    traffic_sources: Optional[str] = None,
    page_page: Optional[str] = None,
    entry_page: Optional[str] = None,
    page_entry_page: Optional[str] = None,
    
    # OS filters
    platform_os: Optional[str] = None,
    system_platform_os: Optional[str] = None,
    
    # Engagement filters
    engagement_session_length: Optional[str] = None,
    engagement_session_length_min: Optional[int] = None,
    engagement_session_length_max: Optional[int] = None,
    engagement_session_length_operator: Optional[str] = None,
    engagement_page_views: Optional[str] = None,
    engagement_page_views_min: Optional[int] = None,
    engagement_page_views_max: Optional[int] = None,
    engagement_page_views_operator: Optional[str] = None,
    engagement_bounce_rate: Optional[str] = None,
    engagement_exit_link: Optional[str] = None,
    engagement_sessions_per_visitor: Optional[int] = None,
    engagement_sessions_per_visitor_operator: Optional[str] = None,
    page_views_per_session: Optional[int] = None,
    page_views_per_session_operator: Optional[str] = None,
    
    # System filters
    browser: Optional[str] = None,
    device: Optional[str] = None,
    location_ip_address: Optional[str] = None,

    db: Session = Depends(get_db)

):

    """Get individual exit link clicks"""

    # Build base query

    query = db.query(models.ExitLinkClick).filter(

        models.ExitLinkClick.project_id == project_id

    )

    

    # Add date filtering if parameters are provided

    if start_date and end_date:

        try:

            # Parse ISO datetime strings from frontend

            from datetime import datetime

            start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))

            end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

            

            query = query.filter(

                models.ExitLinkClick.clicked_at >= start_datetime,

                models.ExitLinkClick.clicked_at <= end_datetime

            )

            print(f"📅 Exit Links - Filtering by date range: {start_datetime} to {end_datetime}")

        except ValueError as e:

            print(f"❌ Exit Links - Date parsing error: {e}")

            # Try fallback to date-only parsing

            try:

                start_datetime = datetime.strptime(start_date.split('T')[0], "%Y-%m-%d")

                end_datetime = datetime.strptime(end_date.split('T')[0], "%Y-%m-%d") + timedelta(days=1)

                

                query = query.filter(

                    models.ExitLinkClick.clicked_at >= start_datetime,

                    models.ExitLinkClick.clicked_at < end_datetime

                )

                print(f"📅 Exit Links - Using fallback date parsing: {start_datetime} to {end_datetime}")

            except ValueError as e2:

                print(f"❌ Exit Links - Fallback date parsing also failed: {e2}")

                # Continue without date filtering if dates are invalid

    # Apply additional filters
    print(f"🔍 Exit Links - Applying filters - country_city: {country_city}, traffic_sources: {traffic_sources}")
    print(f"🔍 Exit Links - Page filters - page_page: {page_page}, entry_page: {entry_page}, page_entry_page: {page_entry_page}")
    print(f"🔍 Exit Links - Engagement filters - engagement_exit_link: {engagement_exit_link}, engagement_sessions_per_visitor: {engagement_sessions_per_visitor}, page_views_per_session: {page_views_per_session}")
    print(f"🔍 Exit Links - Session length filters - engagement_session_length_min: {engagement_session_length_min}, engagement_session_length_max: {engagement_session_length_max}, engagement_session_length_operator: {engagement_session_length_operator}")
    print(f"🔍 Exit Links - System filters - browser: {browser}, device: {device}, location_ip_address: {location_ip_address}")
    
    # Join with Visit model to get filter fields
    query = query.join(models.Visit, 
        (models.ExitLinkClick.visitor_id == models.Visit.visitor_id) & 
        (models.ExitLinkClick.session_id == models.Visit.session_id) &
        (models.ExitLinkClick.project_id == models.Visit.project_id)
    )
    
    # IP Address filter
    if location_ip_address:
        query = query.filter(models.Visit.ip_address.like(f'%{location_ip_address}%'))
        print(f"🔍 Exit Links - Applied IP address filter: {location_ip_address}")
    
    # Entry page filter (page_entry_page parameter)
    if page_entry_page:
        query = query.filter(models.Visit.entry_page.like(f'%{page_entry_page}%'))
        print(f"🔍 Exit Links - Applied entry page filter: {page_entry_page}")
    
    # Country/City filter
    if country_city:
        if ',' in country_city:
            # Country,City format
            parts = country_city.split(',', 1)
            country_filter = parts[0].strip()
            city_filter = parts[1].strip() if len(parts) > 1 else None
            
            if city_filter:
                query = query.filter(
                    models.Visit.country == country_filter,
                    models.Visit.city == city_filter
                )
                print(f"🔍 Exit Links - Applied country and city filter: {country_filter}, {city_filter}")
            else:
                query = query.filter(models.Visit.country == country_filter)
                print(f"🔍 Exit Links - Applied country filter: {country_filter}")
        else:
            # Just country
            query = query.filter(models.Visit.country == country_city)
            print(f"🔍 Exit Links - Applied country filter: {country_city}")
    
    # Browser filter
    if browser:
        query = query.filter(models.Visit.browser.like(f'%{browser}%'))
        print(f"🔍 Exit Links - Applied browser filter: {browser}")
    
    # Device filter
    if device:
        query = query.filter(models.Visit.device.like(f'%{device}%'))
        print(f"🔍 Exit Links - Applied device filter: {device}")
    
    # Traffic sources filter (using referrer field from Visit)
    if traffic_sources:
        query = query.filter(models.Visit.referrer.like(f'%{traffic_sources}%'))
        print(f"🔍 Exit Links - Applied traffic sources filter: {traffic_sources}")
    
    # Page filter (using from_page from ExitLinkClick)
    if page_page:
        query = query.filter(models.ExitLinkClick.from_page.like(f'%{page_page}%'))
        print(f"🔍 Exit Links - Applied page filter: {page_page}")
    
    # Entry page filter (using entry_page from Visit)
    if entry_page:
        query = query.filter(models.Visit.entry_page.like(f'%{entry_page}%'))
        print(f"🔍 Exit Links - Applied entry page filter: {entry_page}")
    
    # Platform OS filter (using os field from Visit)
    if platform_os:
        query = query.filter(models.Visit.os.like(f'%{platform_os}%'))
        print(f"🔍 Exit Links - Applied platform OS filter: {platform_os}")
    
    # System platform OS filter (using os field from Visit)
    if system_platform_os:
        query = query.filter(models.Visit.os.like(f'%{system_platform_os}%'))
        print(f"🔍 Exit Links - Applied system platform OS filter: {system_platform_os}")
    
    # Engagement exit link filter (using exit_page from Visit)
    if engagement_exit_link:
        query = query.filter(models.Visit.exit_page.like(f'%{engagement_exit_link}%'))
        print(f"🔍 Exit Links - Applied engagement exit link filter: {engagement_exit_link}")
    
    # Sessions per visitor filter
    if engagement_sessions_per_visitor is not None:
        # This is a complex filter that requires counting sessions per visitor
        # We'll need to use a subquery to count sessions per visitor
        from sqlalchemy import func
        
        # Create a subquery to count sessions per visitor
        sessions_per_visitor_subquery = db.query(
            models.Visit.visitor_id,
            func.count(models.Visit.id).label('session_count')
        ).filter(
            models.Visit.project_id == project_id
        ).group_by(models.Visit.visitor_id).subquery()
        
        # Join with the subquery
        query = query.join(
            sessions_per_visitor_subquery,
            models.ExitLinkClick.visitor_id == sessions_per_visitor_subquery.c.visitor_id
        )
        
        # Apply the filter based on operator
        if engagement_sessions_per_visitor_operator == 'equals':
            query = query.filter(sessions_per_visitor_subquery.c.session_count == engagement_sessions_per_visitor)
        elif engagement_sessions_per_visitor_operator == 'greater_than':
            query = query.filter(sessions_per_visitor_subquery.c.session_count > engagement_sessions_per_visitor)
        elif engagement_sessions_per_visitor_operator == 'less_than':
            query = query.filter(sessions_per_visitor_subquery.c.session_count < engagement_sessions_per_visitor)
        elif engagement_sessions_per_visitor_operator == 'greater_than_or_equal':
            query = query.filter(sessions_per_visitor_subquery.c.session_count >= engagement_sessions_per_visitor)
        elif engagement_sessions_per_visitor_operator == 'less_than_or_equal':
            query = query.filter(sessions_per_visitor_subquery.c.session_count <= engagement_sessions_per_visitor)
        else:
            # Default to equals if no operator specified
            query = query.filter(sessions_per_visitor_subquery.c.session_count == engagement_sessions_per_visitor)
        
        print(f"🔍 Exit Links - Applied sessions per visitor filter: {engagement_sessions_per_visitor} ({engagement_sessions_per_visitor_operator})")
    
    # Page views per session filter
    if page_views_per_session is not None:
        # This is a complex filter that requires counting page views per session
        # We'll need to use a subquery to count page views per session
        from sqlalchemy import func
        
        # Create a subquery to count page views per session
        page_views_per_session_subquery = db.query(
            models.Visit.session_id,
            func.count(models.PageView.id).label('page_view_count')
        ).join(
            models.PageView, models.Visit.id == models.PageView.visit_id
        ).filter(
            models.Visit.project_id == project_id
        ).group_by(models.Visit.session_id).subquery()
        
        # Join with the subquery
        query = query.join(
            page_views_per_session_subquery,
            models.ExitLinkClick.session_id == page_views_per_session_subquery.c.session_id
        )
        
        # Apply filter based on operator
        if page_views_per_session_operator == 'equals':
            query = query.filter(page_views_per_session_subquery.c.page_view_count == page_views_per_session)
        elif page_views_per_session_operator == 'greater_than':
            query = query.filter(page_views_per_session_subquery.c.page_view_count > page_views_per_session)
        elif page_views_per_session_operator == 'less_than':
            query = query.filter(page_views_per_session_subquery.c.page_view_count < page_views_per_session)
        elif page_views_per_session_operator == 'greater_than_or_equal':
            query = query.filter(page_views_per_session_subquery.c.page_view_count >= page_views_per_session)
        elif page_views_per_session_operator == 'less_than_or_equal':
            query = query.filter(page_views_per_session_subquery.c.page_view_count <= page_views_per_session)
        else:
            # Default to equals if no operator specified
            query = query.filter(page_views_per_session_subquery.c.page_view_count == page_views_per_session)
        
        print(f"🔍 Exit Links - Applied page views per session filter: {page_views_per_session} ({page_views_per_session_operator})")
    
    # Session length range filter
    if engagement_session_length_min is not None or engagement_session_length_max is not None:
        # This filter uses the session_duration field from Visit model
        if engagement_session_length_min is not None and engagement_session_length_max is not None:
            # Both min and max provided - use between
            query = query.filter(
                models.Visit.session_duration >= engagement_session_length_min,
                models.Visit.session_duration <= engagement_session_length_max
            )
            print(f"🔍 Exit Links - Applied session length range filter: {engagement_session_length_min} to {engagement_session_length_max}")
        elif engagement_session_length_min is not None:
            # Only min provided - use greater than or equal
            operator = engagement_session_length_operator or 'greater_than_or_equal'
            if operator == 'greater_than':
                query = query.filter(models.Visit.session_duration > engagement_session_length_min)
            else:  # default to greater_than_or_equal
                query = query.filter(models.Visit.session_duration >= engagement_session_length_min)
            print(f"🔍 Exit Links - Applied session length min filter: {engagement_session_length_min} ({operator})")
        elif engagement_session_length_max is not None:
            # Only max provided - use less than or equal
            operator = engagement_session_length_operator or 'less_than_or_equal'
            if operator == 'less_than':
                query = query.filter(models.Visit.session_duration < engagement_session_length_max)
            else:  # default to less_than_or_equal
                query = query.filter(models.Visit.session_duration <= engagement_session_length_max)
            print(f"🔍 Exit Links - Applied session length max filter: {engagement_session_length_max} ({operator})")
        elif engagement_session_length is not None:
            # Single value filter - use exact match or operator
            operator = engagement_session_length_operator or 'equals'
            if operator == 'equals':
                query = query.filter(models.Visit.session_duration == engagement_session_length)
            elif operator == 'greater_than':
                query = query.filter(models.Visit.session_duration > engagement_session_length)
            elif operator == 'less_than':
                query = query.filter(models.Visit.session_duration < engagement_session_length)
            elif operator == 'greater_than_or_equal':
                query = query.filter(models.Visit.session_duration >= engagement_session_length)
            elif operator == 'less_than_or_equal':
                query = query.filter(models.Visit.session_duration <= engagement_session_length)
            else:
                # Default to equals
                query = query.filter(models.Visit.session_duration == engagement_session_length)
            print(f"🔍 Exit Links - Applied session length filter: {engagement_session_length} ({operator})")

    # Get individual clicks ordered by most recent first

    exit_clicks = query.order_by(desc(models.ExitLinkClick.clicked_at)).limit(limit).all()

    

    # Return individual click entries

    return [{

        "id": click.id,

        "url": click.url,

        "from_page": click.from_page,

        "visitor_id": click.visitor_id,

        "session_id": click.session_id,

        "clicked_at": click.clicked_at

    } for click in exit_clicks]



@router.get("/{project_id}/exit-links-summary")

def get_exit_links_summary(project_id: int, db: Session = Depends(get_db)):

    """Get aggregated exit link statistics"""

    exit_links = db.query(models.ExitLink).filter(

        models.ExitLink.project_id == project_id

    ).order_by(desc(models.ExitLink.click_count)).limit(20).all()

    

    return [{

        "url": el.url,

        "from_page": el.from_page,

        "click_count": el.click_count,

        "last_clicked": el.last_clicked

    } for el in exit_links]

