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

security = HTTPBearer(auto_error=False)



@router.get("/countries")
def get_all_countries(db: Session = Depends(get_db)):
    """
    Get all unique countries from the visits table
    """
    try:
        # Query all distinct countries
        countries = db.query(models.Visit.country)\
                     .filter(models.Visit.country.isnot(None))\
                     .filter(models.Visit.country != '')\
                     .distinct()\
                     .order_by(models.Visit.country)\
                     .all()
        
        # Extract country names from tuples
        country_list = [country[0] for country in countries if country[0]]
        
        return {
            "countries": country_list,
            "count": len(country_list)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching countries: {str(e)}")


@router.get("/country-cities")
def get_country_cities(db: Session = Depends(get_db)):
    """
    Get all unique country-city combinations from the visits table
    """
    try:
        # Query all distinct country-city combinations
        country_cities = db.query(
                models.Visit.country,
                models.Visit.city
            )\
            .filter(models.Visit.country.isnot(None))\
            .filter(models.Visit.country != '')\
            .distinct()\
            .order_by(models.Visit.country, models.Visit.city)\
            .all()
        
        # Group by country
        result = {}
        for country, city in country_cities:
            if country and country not in result:
                result[country] = []
            if city and city not in result[country]:
                result[country].append(city)
        
        return {
            "country_cities": result,
            "count": len(result)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching country cities: {str(e)}")


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

    # Filter parameters
    country_city: Optional[str] = None,
    traffic_sources: Optional[str] = None,
    page_page: Optional[str] = None,
    entry_page: Optional[str] = None,
    page_entry_page: Optional[str] = None,
    ip_address: Optional[str] = None,
    location_ip_address: Optional[str] = None,
    platform_os: Optional[str] = None,
    system_platform_os: Optional[str] = None,
    engagement_session_length: Optional[str] = None,
    engagement_session_length_min: Optional[str] = None,
    engagement_session_length_max: Optional[str] = None,
    engagement_session_length_operator: Optional[str] = None,
    page_views_per_session: Optional[str] = None,
    page_views_per_session_operator: Optional[str] = None,
    sessions_per_visitor: Optional[str] = None,
    sessions_per_visitor_operator: Optional[str] = None,
    engagement_sessions_per_visitor: Optional[str] = None,
    engagement_sessions_per_visitor_operator: Optional[str] = None,
    utm_campaign: Optional[str] = None,
    utm_source: Optional[str] = None,
    utm_medium: Optional[str] = None,
    exit_link: Optional[str] = None,
    engagement_exit_link: Optional[str] = None,
    
    # System filters
    browser: Optional[str] = None,
    device: Optional[str] = None,

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

        

        # Apply date filtering if provided - use same logic as reports endpoint

        if start_date and end_date:

            try:

                print(f"🔍 Raw dates from frontend: start_date={start_date}, end_date={end_date}")

                # Use the same date normalization as reports endpoint

                start_dt, end_dt = normalize_date_range(start_date, end_date)

                print(f"🔍 Backend date filtering (IST normalized): {start_dt} to {end_dt}")

                print(f"🔍 Date range in UTC: {start_dt.isoformat()} to {end_dt.isoformat()}")

                query = query.filter(

                    models.Visit.visited_at >= start_dt,

                    models.Visit.visited_at <= end_dt

                )

                # Check how many records match the filter

                count = query.count()

                print(f"📊 Records after date filtering: {count}")

            except ValueError as e:

                print(f"❌ Date parsing error: {e}")

                # Continue without date filtering if parsing fails

                pass

        
        # Apply additional filters
        print(f"🔍 Applying filters - country_city: {country_city}, traffic_sources: {traffic_sources}, page_entry_page: {page_entry_page}")
        print(f"🔍 OS filters - platform_os: {platform_os}, system_platform_os: {system_platform_os}")
        print(f"🔍 System filters - browser: {browser}, device: {device}")
        print(f"🔍 Session length params - min: {engagement_session_length_min}, max: {engagement_session_length_max}, operator: {engagement_session_length_operator}")
        
        # Country/City filter
        if country_city:
            if ',' in country_city:
                # Country,City format
                parts = country_city.split(',', 1)
                country_filter = parts[0].strip()
                city_filter = parts[1].strip() if len(parts) > 1 else None
                
                query = query.filter(models.Visit.country == country_filter)
                if city_filter:
                    query = query.filter(models.Visit.city == city_filter)
            else:
                # Country only
                query = query.filter(models.Visit.country == country_city)
        
        # Traffic sources filter
        if traffic_sources:
            if traffic_sources == 'direct':
                query = query.filter(models.Visit.referrer == 'direct')
            elif traffic_sources == 'organic':
                query = query.filter(models.Visit.referrer.like('%google%') | 
                                       models.Visit.referrer.like('%bing%') | 
                                       models.Visit.referrer.like('%yahoo%'))
            elif traffic_sources == 'referral':
                query = query.filter(models.Visit.referrer != 'direct',
                                       ~models.Visit.referrer.like('%google%'),
                                       ~models.Visit.referrer.like('%bing%'),
                                       ~models.Visit.referrer.like('%yahoo%'))
            elif traffic_sources == 'social':
                query = query.filter(models.Visit.referrer.like('%facebook%') | 
                                       models.Visit.referrer.like('%twitter%') | 
                                       models.Visit.referrer.like('%linkedin%') |
                                       models.Visit.referrer.like('%instagram%'))
        
        # Page filters
        if page_page:
            query = query.filter(models.Visit.entry_page.like(f'%{page_page}%'))
        
        if entry_page:
            query = query.filter(models.Visit.entry_page.like(f'%{entry_page}%'))
        
        if page_entry_page:
            print(f"🔍 Applying page_entry_page filter: {page_entry_page}")
            query = query.filter(models.Visit.entry_page.like(f'%{page_entry_page}%'))
        
        # IP Address filter
        if ip_address:
            query = query.filter(models.Visit.ip_address.like(f'%{ip_address}%'))
        
        # Location IP Address filter
        if location_ip_address:
            query = query.filter(models.Visit.ip_address.like(f'%{location_ip_address}%'))
            print(f"🔍 Applied location_ip_address filter: {location_ip_address}")
        
        # Platform/OS filter - handle both platform_os and system_platform_os parameters
        os_filter = platform_os or system_platform_os
        if os_filter:
            query = query.filter(models.Visit.os.like(f'%{os_filter}%'))
            print(f"🔍 Applied OS filter: {os_filter}")
        
        # Browser filter
        if browser:
            query = query.filter(models.Visit.browser.like(f'%{browser}%'))
            print(f"🔍 Applied browser filter: {browser}")
        
        # Device filter
        if device:
            query = query.filter(models.Visit.device.like(f'%{device}%'))
            print(f"🔍 Applied device filter: {device}")
        
        # UTM filters
        if utm_campaign:
            query = query.filter(models.Visit.utm_campaign.like(f'%{utm_campaign}%'))
        
        if utm_source:
            query = query.filter(models.Visit.utm_source.like(f'%{utm_source}%'))
        
        if utm_medium:
            query = query.filter(models.Visit.utm_medium.like(f'%{utm_medium}%'))
        
        # Exit link filters
        if exit_link or engagement_exit_link:
            exit_link_filter = exit_link or engagement_exit_link
            print(f"🔍 Applying exit link filter: {exit_link_filter}")
            
            # Subquery to find visits that have exit link clicks matching the filter
            exit_link_subquery = db.query(models.ExitLinkClick.visitor_id)\
                .filter(models.ExitLinkClick.project_id == project_id)\
                .filter(models.ExitLinkClick.url.like(f'%{exit_link_filter}%'))\
                .distinct()\
                .subquery()
            
            # Filter visits to only include those with matching exit link clicks
            query = query.filter(models.Visit.visitor_id.in_(exit_link_subquery))
            print(f"🔍 Applied exit link filter: {exit_link_filter}")
        
        # Session length filters (engagement_session_length_min/max/operator)
        if engagement_session_length_min and engagement_session_length_operator:
            try:
                min_duration = int(engagement_session_length_min)
                
                if engagement_session_length_operator == 'equals':
                    # If both min and max are provided with equals operator, treat as range
                    if engagement_session_length_max:
                        max_duration = int(engagement_session_length_max)
                        query = query.filter(models.Visit.session_duration >= min_duration,
                                           models.Visit.session_duration <= max_duration)
                        print(f"🔍 Applied session length filter (equals with range): {min_duration} to {max_duration} seconds")
                    else:
                        # Single value equals
                        query = query.filter(models.Visit.session_duration == min_duration)
                        print(f"🔍 Applied session length filter: equals {min_duration} seconds")
                elif engagement_session_length_operator == 'greater_than':
                    query = query.filter(models.Visit.session_duration > min_duration)
                    print(f"🔍 Applied session length filter: greater_than {min_duration} seconds")
                elif engagement_session_length_operator == 'less_than':
                    query = query.filter(models.Visit.session_duration < min_duration)
                    print(f"🔍 Applied session length filter: less_than {min_duration} seconds")
                elif engagement_session_length_operator == 'range' and engagement_session_length_max:
                    max_duration = int(engagement_session_length_max)
                    query = query.filter(models.Visit.session_duration >= min_duration,
                                       models.Visit.session_duration <= max_duration)
                    print(f"🔍 Applied session length filter: range {min_duration} to {max_duration} seconds")
                else:
                    print(f"❌ Unsupported session length operator: {engagement_session_length_operator}")
            except ValueError:
                print(f"❌ Invalid session length value: {engagement_session_length_min}")
        elif engagement_session_length_min and engagement_session_length_max:
            # Fallback to range filter if no operator specified
            try:
                min_duration = int(engagement_session_length_min)
                max_duration = int(engagement_session_length_max)
                query = query.filter(models.Visit.session_duration >= min_duration,
                                   models.Visit.session_duration <= max_duration)
                print(f"🔍 Applied session length range filter: {min_duration} to {max_duration} seconds")
            except ValueError:
                print(f"❌ Invalid session length values: {engagement_session_length_min}, {engagement_session_length_max}")
        
        # Page views per session filter
        if page_views_per_session and page_views_per_session_operator:
            try:
                page_views_count = int(page_views_per_session)
                
                # Subquery to count page views per visit
                page_views_subquery = db.query(
                    models.PageView.visit_id,
                    func.count(models.PageView.id).label('page_views_count')
                ).group_by(models.PageView.visit_id).subquery()
                
                # Join with the subquery
                query = query.join(page_views_subquery, models.Visit.id == page_views_subquery.c.visit_id)
                
                if page_views_per_session_operator == 'equals':
                    query = query.filter(page_views_subquery.c.page_views_count == page_views_count)
                elif page_views_per_session_operator == 'greater_than':
                    query = query.filter(page_views_subquery.c.page_views_count > page_views_count)
                elif page_views_per_session_operator == 'less_than':
                    query = query.filter(page_views_subquery.c.page_views_count < page_views_count)
                print(f"🔍 Applied page views filter: {page_views_per_session_operator} {page_views_count}")
            except ValueError:
                print(f"❌ Invalid page views value: {page_views_per_session}")
        
        # Sessions per visitor filter  
        if sessions_per_visitor and sessions_per_visitor_operator:
            try:
                sessions_count = int(sessions_per_visitor)
                if sessions_per_visitor_operator == 'equals':
                    # Subquery for session count per visitor
                    subquery = db.query(models.Visit.visitor_id,
                                     func.count(models.Visit.id).label('session_count'))\
                                 .filter(models.Visit.project_id == project_id)\
                                 .group_by(models.Visit.visitor_id)\
                                 .subquery()
                    query = query.join(subquery, models.Visit.visitor_id == subquery.c.visitor_id)\
                             .filter(subquery.c.session_count == sessions_count)
                elif sessions_per_visitor_operator == 'greater_than':
                    subquery = db.query(models.Visit.visitor_id,
                                     func.count(models.Visit.id).label('session_count'))\
                                 .filter(models.Visit.project_id == project_id)\
                                 .group_by(models.Visit.visitor_id)\
                                 .subquery()
                    query = query.join(subquery, models.Visit.visitor_id == subquery.c.visitor_id)\
                             .filter(subquery.c.session_count > sessions_count)
                elif sessions_per_visitor_operator == 'less_than':
                    subquery = db.query(models.Visit.visitor_id,
                                     func.count(models.Visit.id).label('session_count'))\
                                 .filter(models.Visit.project_id == project_id)\
                                 .group_by(models.Visit.visitor_id)\
                                 .subquery()
                    query = query.join(subquery, models.Visit.visitor_id == subquery.c.visitor_id)\
                             .filter(subquery.c.session_count < sessions_count)
                print(f"🔍 Applied sessions per visitor filter: {sessions_per_visitor_operator} {sessions_count}")
            except ValueError:
                print(f"❌ Invalid sessions per visitor value: {sessions_per_visitor}")
        
        # Engagement sessions per visitor filter  
        if engagement_sessions_per_visitor and engagement_sessions_per_visitor_operator:
            try:
                sessions_count = int(engagement_sessions_per_visitor)
                if engagement_sessions_per_visitor_operator == 'equals':
                    # Subquery for session count per visitor
                    subquery = db.query(models.Visit.visitor_id,
                                     func.count(models.Visit.id).label('session_count'))\
                                 .filter(models.Visit.project_id == project_id)\
                                 .group_by(models.Visit.visitor_id)\
                                 .subquery()
                    query = query.join(subquery, models.Visit.visitor_id == subquery.c.visitor_id)\
                             .filter(subquery.c.session_count == sessions_count)
                elif engagement_sessions_per_visitor_operator == 'greater_than':
                    subquery = db.query(models.Visit.visitor_id,
                                     func.count(models.Visit.id).label('session_count'))\
                                 .filter(models.Visit.project_id == project_id)\
                                 .group_by(models.Visit.visitor_id)\
                                 .subquery()
                    query = query.join(subquery, models.Visit.visitor_id == subquery.c.visitor_id)\
                             .filter(subquery.c.session_count > sessions_count)
                elif engagement_sessions_per_visitor_operator == 'less_than':
                    subquery = db.query(models.Visit.visitor_id,
                                     func.count(models.Visit.id).label('session_count'))\
                                 .filter(models.Visit.project_id == project_id)\
                                 .group_by(models.Visit.visitor_id)\
                                 .subquery()
                    query = query.join(subquery, models.Visit.visitor_id == subquery.c.visitor_id)\
                             .filter(subquery.c.session_count < sessions_count)
                print(f"🔍 Applied engagement sessions per visitor filter: {engagement_sessions_per_visitor_operator} {sessions_count}")
            except ValueError:
                print(f"❌ Invalid engagement sessions per visitor value: {engagement_sessions_per_visitor}")
        

        # Get all visits filtered by date range and other filters - apply limit only if provided
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

        

        # Get session counts for all visitors in one query with same date filtering

        visitor_ids = list(set([v.visitor_id for v in visits]))

        session_counts = {}

        if visitor_ids:

            session_counts_query = db.query(

                models.Visit.visitor_id,

                func.count(models.Visit.id).label('session_count')

            ).filter(

                models.Visit.project_id == project_id,

                models.Visit.visitor_id.in_(visitor_ids)

            )

            # Apply the same date filtering to session counts
            if start_date and end_date:
                try:
                    # Use the same date normalization as reports endpoint
                    start_dt, end_dt = normalize_date_range(start_date, end_date)
                    
                    session_counts_query = session_counts_query.filter(
                        models.Visit.visited_at >= start_dt,
                        models.Visit.visited_at <= end_dt
                    )
                except ValueError as e:
                    print(f"❌ Date parsing error in session counts: {e}")
                    # Continue without date filtering if parsing fails
                    pass

            session_counts_query = session_counts_query.group_by(models.Visit.visitor_id).all()
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

            "session_number": f"#{visit.session_id}",

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

            "total_sessions": len(sessions) + 1,  # Current session count

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

        

        # Apply date filtering if provided - use same logic as reports endpoint

        if start_date and end_date:

            try:

                print(f"🌍 Raw dates from frontend: start_date={start_date}, end_date={end_date}")

                # Use the same date normalization as reports endpoint

                start_dt, end_dt = normalize_date_range(start_date, end_date)

                print(f"🌍 Backend date filtering (IST normalized): {start_dt} to {end_dt}")

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
    country_city: Optional[str] = None,
    browser: Optional[str] = None,
    device: Optional[str] = None,
    platform_os: Optional[str] = None,
    system_platform_os: Optional[str] = None,
    page_views_per_session: Optional[str] = None,
    page_views_per_session_min: Optional[int] = None,
    page_views_per_session_max: Optional[int] = None,
    page_views_per_session_operator: Optional[str] = None,
    engagement_session_length: Optional[str] = None,
    engagement_session_length_min: Optional[int] = None,
    engagement_session_length_max: Optional[int] = None,
    engagement_session_length_operator: Optional[str] = None,
    engagement_sessions_per_visitor: Optional[str] = None,
    engagement_sessions_per_visitor_operator: Optional[str] = None,
    traffic_sources: Optional[str] = None,
    page_page: Optional[str] = None,
    page_entry_page: Optional[str] = None,
    location_ip_address: Optional[str] = None,
    engagement_exit_link: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Dedicated endpoint for Visitor Map Page.
    Supports filtering by days and returns aggregated location data.
    """
    
    print(f" get_map_view called with:")
    print(f"  - project_id: {project_id}")
    print(f"  - days: {days}")
    print(f"  - country_city: {country_city}")
    print(f"  - browser: {browser}")
    print(f"  - device: {device}")
    print(f"  - platform_os: {platform_os}")
    print(f"  - system_platform_os: {system_platform_os}")
    print(f"  - engagement_sessions_per_visitor: {engagement_sessions_per_visitor}")
    print(f"  - engagement_sessions_per_visitor_operator: {engagement_sessions_per_visitor_operator}")
    print(f"  - traffic_sources: {traffic_sources}")
    print(f"  - page_page: {page_page}")
    print(f"  - page_entry_page: {page_entry_page}")
    print(f"  - location_ip_address: {location_ip_address}")
    print(f"  - engagement_exit_link: {engagement_exit_link}")

    start_date_ist = utils.get_ist_start_of_day(days - 1)
    start_date_utc = utils.ist_to_utc(start_date_ist)

    # Build base query with filters
    query = db.query(
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
    )

    # Apply filters
    if country_city:
        query = query.filter(models.Visit.country == country_city)
    
    if browser:
        query = query.filter(models.Visit.browser == browser)
    
    if device:
        query = query.filter(models.Visit.device == device)
    
    # Handle both platform_os and system_platform_os parameters
    os_filter = platform_os or system_platform_os
    if os_filter:
        query = query.filter(models.Visit.os == os_filter)
    
    if traffic_sources:
        query = query.filter(models.Visit.referrer.like(f'%{traffic_sources}%'))
    
    if page_page:
        query = query.filter(
            (models.Visit.entry_page.like(f'%{page_page}%')) |
            (models.Visit.exit_page.like(f'%{page_page}%'))
        )
    
    if page_entry_page:
        query = query.filter(models.Visit.entry_page.like(f'%{page_entry_page}%'))
    
    # Handle page_views_per_session filter with operator
    if page_views_per_session and page_views_per_session_operator:
        try:
            page_views_count = int(page_views_per_session)
            
            # Subquery to count page views per visit
            page_views_subquery = db.query(
                models.PageView.visit_id,
                func.count(models.PageView.id).label('page_views_count')
            ).group_by(models.PageView.visit_id).subquery()
            
            # Join with the subquery
            query = query.join(page_views_subquery, models.Visit.id == page_views_subquery.c.visit_id)
            
            if page_views_per_session_operator == 'equals':
                query = query.filter(page_views_subquery.c.page_views_count == page_views_count)
            elif page_views_per_session_operator == 'greater_than':
                query = query.filter(page_views_subquery.c.page_views_count > page_views_count)
            elif page_views_per_session_operator == 'less_than':
                query = query.filter(page_views_subquery.c.page_views_count < page_views_count)
            print(f" Applied page views filter: {page_views_per_session_operator} {page_views_count}")
        except ValueError:
            print(f" Invalid page views value: {page_views_per_session}")
    
    # Handle legacy page_views_per_session range filters (for backward compatibility)
    elif page_views_per_session_min is not None:
        query = query.filter(models.Visit.page_views >= page_views_per_session_min)
    
    if page_views_per_session_max is not None:
        query = query.filter(models.Visit.page_views <= page_views_per_session_max)
    
    # Handle engagement_session_length range filters
    if engagement_session_length_min is not None:
        query = query.filter(models.Visit.session_duration >= engagement_session_length_min)
    
    if engagement_session_length_max is not None:
        query = query.filter(models.Visit.session_duration <= engagement_session_length_max)

    # Handle engagement_sessions_per_visitor filter with operator
    if engagement_sessions_per_visitor and engagement_sessions_per_visitor_operator:
        try:
            sessions_count = int(engagement_sessions_per_visitor)
            
            # Subquery to count sessions per visitor
            sessions_subquery = db.query(
                models.Visit.visitor_id,
                func.count(models.Visit.id).label('sessions_count')
            ).filter(
                models.Visit.project_id == project_id,
                models.Visit.visited_at >= start_date_utc
            ).group_by(models.Visit.visitor_id).subquery()
            
            # Join with the subquery
            query = query.join(sessions_subquery, models.Visit.visitor_id == sessions_subquery.c.visitor_id)
            
            if engagement_sessions_per_visitor_operator == 'equals':
                query = query.filter(sessions_subquery.c.sessions_count == sessions_count)
            elif engagement_sessions_per_visitor_operator == 'greater_than':
                query = query.filter(sessions_subquery.c.sessions_count > sessions_count)
            elif engagement_sessions_per_visitor_operator == 'less_than':
                query = query.filter(sessions_subquery.c.sessions_count < sessions_count)
            print(f" Applied sessions per visitor filter: {engagement_sessions_per_visitor_operator} {sessions_count}")
        except ValueError:
            print(f" Invalid sessions per visitor value: {engagement_sessions_per_visitor}")

    # Handle location_ip_address filter
    if location_ip_address:
        query = query.filter(models.Visit.ip_address.like(f'%{location_ip_address}%'))

    # Handle engagement_exit_link filter
    if engagement_exit_link:
        print(f" Applying engagement_exit_link filter: {engagement_exit_link}")
        
        # Subquery to find visits that have exit link clicks matching the filter
        exit_link_subquery = db.query(models.ExitLinkClick.visitor_id)\
            .filter(models.ExitLinkClick.project_id == project_id)\
            .filter(models.ExitLinkClick.clicked_at >= start_date_utc)\
            .filter(models.ExitLinkClick.url.like(f'%{engagement_exit_link}%'))\
            .distinct()\
            .subquery()
        
        # Filter visits to only include those with matching exit link clicks
        query = query.filter(models.Visit.visitor_id.in_(exit_link_subquery))
        print(f" Applied engagement_exit_link filter: {engagement_exit_link}")

    locations = query.group_by(
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

            # Calculate exit_page from the last pageview if exit_page is empty
            calculated_exit_page = session.exit_page or ""
            if not calculated_exit_page and session_page_views:
                # Get the last pageview URL as exit page
                last_pageview = session_page_views[-1]
                calculated_exit_page = last_pageview.get("url", "")

            sessions_data.append({

                "session_id": str(session.id),

                "start_time": session.visited_at.isoformat() if session.visited_at else "",

                "duration": session.session_duration or 0,

                "referrer": session.referrer or "",

                "entry_page": session.entry_page or "",

                "exit_page": calculated_exit_page,

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


@router.get("/{project_id}/visitor-detail-by-ip/{ip_address}")

def get_visitor_detail_by_ip(project_id: int, ip_address: str, db: Session = Depends(get_db)):

    """

    Get visitor details by IP address.

    Returns complete visitor profile with all sessions and navigation paths for the given IP address.

    """

    try:

        print(f"🔍 Getting visitor detail for project {project_id}, IP {ip_address}")

        

        # Check if project exists

        project = db.query(models.Project).filter(models.Project.id == project_id).first()

        if not project:

            raise HTTPException(status_code=404, detail="Project not found")

        

        # Get visitor's most recent visit for this IP address

        latest_visit = db.query(models.Visit).filter(

            models.Visit.project_id == project_id,

            models.Visit.ip_address == ip_address

        ).order_by(desc(models.Visit.visited_at)).first()

        

        if not latest_visit:

            raise HTTPException(status_code=404, detail="No visitor found with this IP address")

        

        # Use the visitor_id from the latest visit

        visitor_id = latest_visit.visitor_id

        

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

                    "time_spent": pv.time_spent or 0

                })

        

        # Build sessions data with page views

        sessions_data = []

        for session in sessions:

            session_page_views = page_views_map.get(session.id, [])

            # Calculate exit_page from the last pageview if exit_page is empty
            calculated_exit_page = session.exit_page or ""
            if not calculated_exit_page and session_page_views:
                # Get the last pageview URL as exit page
                last_pageview = session_page_views[-1]
                calculated_exit_page = last_pageview.get("url", "")

            session_data = {

                "session_id": session.id,

                "start_time": session.visited_at.isoformat() if session.visited_at else "",

                "duration": session.duration or 0,

                "referrer": session.referrer or "",

                "entry_page": session.entry_page or "",

                "exit_page": calculated_exit_page,

                "pageviews": session_page_views

            }

            sessions_data.append(session_data)

        

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

        

        print(f"✅ Successfully returning visitor detail by IP with {len(sessions_data)} sessions")

        return response

        

    except HTTPException:

        raise

    except Exception as e:

        print(f"❌ Error in get_visitor_detail_by_ip: {e}")

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