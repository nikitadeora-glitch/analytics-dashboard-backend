from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
import models
from datetime import datetime, timedelta
from typing import Optional

router = APIRouter()

@router.get("/{project_id}/sources")
def get_traffic_sources(
    project_id: int,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    try:
        print(f"🔍 Getting traffic sources for project {project_id}")
        print(f"📅 Date range: {start_date} to {end_date}")
        
        # -----------------------------
        # Parse dates with error handling
        # -----------------------------
        start_dt = None
        end_dt = None

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
                print(f"📅 Parsed start_date: {start_dt}")
            except ValueError as e:
                print(f"❌ Error parsing start_date: {e}")
                
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
                print(f"📅 Parsed end_date: {end_dt}")
            except ValueError as e:
                print(f"❌ Error parsing end_date: {e}")

        # -----------------------------
        # Get visits and analyze referrers
        # -----------------------------
        visits_query = db.query(models.Visit).filter(
            models.Visit.project_id == project_id
        )

        # Apply date filtering
        if start_dt:
            visits_query = visits_query.filter(models.Visit.visited_at >= start_dt)
        if end_dt:
            visits_query = visits_query.filter(models.Visit.visited_at <= end_dt)

        visits = visits_query.all()
        print(f"📊 Found {len(visits)} visits in date range")

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
            referrer = (visit.referrer or "").lower().strip()
            
            # Categorize based on referrer
            if not referrer or referrer in ("", "direct", "null", "undefined"):
                source_groups["direct"]["count"] += 1
                source_groups["direct"]["visits"].append(visit)
            elif any(search in referrer for search in ["google", "bing", "yahoo", "duckduckgo", "baidu"]):
                source_groups["organic"]["count"] += 1
                source_groups["organic"]["visits"].append(visit)
            elif any(social in referrer for social in ["facebook", "twitter", "instagram", "linkedin", "youtube", "tiktok", "pinterest"]):
                source_groups["social"]["count"] += 1
                source_groups["social"]["visits"].append(visit)
            elif any(ai in referrer for ai in ["chatgpt", "claude", "gemini", "copilot", "perplexity"]):
                source_groups["ai"]["count"] += 1
                source_groups["ai"]["visits"].append(visit)
            elif any(email in referrer for email in ["mail", "gmail", "outlook", "yahoo.com"]):
                source_groups["email"]["count"] += 1
                source_groups["email"]["visits"].append(visit)
            elif "utm_" in referrer or "campaign" in referrer:
                source_groups["utm"]["count"] += 1
                source_groups["utm"]["visits"].append(visit)
            elif "ads" in referrer or "adwords" in referrer or "facebook.com/tr" in referrer:
                source_groups["paid"]["count"] += 1
                source_groups["paid"]["visits"].append(visit)
            else:
                # Everything else is referral traffic
                source_groups["referral"]["count"] += 1
                source_groups["referral"]["visits"].append(visit)

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
            if data["count"] > 0:  # Only include sources with visits
                # Calculate bounce rate
                bounced = sum(
                    1 for v in data["visits"]
                    if not v.exit_page or v.entry_page == v.exit_page
                )
                bounce_rate = round((bounced / data["count"]) * 100, 1) if data["count"] > 0 else 0

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
    db: Session = Depends(get_db)
):
    try:
        print(f"🔍 Getting traffic source detail for {source_type} in project {project_id}")
        print(f"📅 Date range: {start_date} to {end_date}")
        
        # Parse dates
        start_dt = None
        end_dt = None

        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            print(f"📅 Parsed start_date: {start_dt}")
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            print(f"📅 Parsed end_date: {end_dt}")

        # Get visits for this source type in date range
        visits_query = db.query(models.Visit).filter(
            models.Visit.project_id == project_id
        )

        if start_dt:
            visits_query = visits_query.filter(models.Visit.visited_at >= start_dt)
        if end_dt:
            visits_query = visits_query.filter(models.Visit.visited_at <= end_dt)

        all_visits = visits_query.all()
        print(f"📊 Found {len(all_visits)} total visits in date range")
        
        # Filter visits by source type
        matching_visits = []
        for visit in all_visits:
            referrer = (visit.referrer or "").lower().strip()
            
            if source_type == "direct" and (not referrer or referrer in ("", "direct", "null", "undefined")):
                matching_visits.append(visit)
            elif source_type == "organic" and any(search in referrer for search in ["google", "bing", "yahoo", "duckduckgo", "baidu"]):
                matching_visits.append(visit)
            elif source_type == "social" and any(social in referrer for social in ["facebook", "twitter", "instagram", "linkedin", "youtube", "tiktok", "pinterest"]):
                matching_visits.append(visit)
            elif source_type == "ai" and any(ai in referrer for ai in ["chatgpt", "claude", "gemini", "copilot", "perplexity"]):
                matching_visits.append(visit)
            elif source_type == "email" and any(email in referrer for email in ["mail", "gmail", "outlook", "yahoo.com"]):
                matching_visits.append(visit)
            elif source_type == "utm" and ("utm_" in referrer or "campaign" in referrer):
                matching_visits.append(visit)
            elif source_type == "paid" and ("ads" in referrer or "adwords" in referrer or "facebook.com/tr" in referrer):
                matching_visits.append(visit)
            elif source_type == "referral" and referrer and not any(x in referrer for x in ["google", "bing", "yahoo", "facebook", "twitter", "instagram", "linkedin", "youtube", "mail", "gmail", "outlook", "ads", "adwords", "utm_", "campaign"]):
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
                
                # Check if bounced (no exit page or same as entry page)
                if not visit.exit_page or visit.entry_page == visit.exit_page:
                    daily_data[visit_date]['bounced_sessions'] += 1

        # Calculate bounce rates
        for date_str, data in daily_data.items():
            if data['sessions'] > 0:
                data['bounce_rate'] = round((data['bounced_sessions'] / data['sessions']) * 100, 1)

        # Convert to list and sort by date
        result = list(daily_data.values())
        result.sort(key=lambda x: x['date'])

        print(f"✅ Returning {len(result)} days of data for {source_type}")
        
        return {
            "source_type": source_type,
            "total_sessions": len(matching_visits),
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
def get_exit_links(project_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """Get individual exit link clicks"""
    # Get individual clicks ordered by most recent first
    exit_clicks = db.query(models.ExitLinkClick).filter(
        models.ExitLinkClick.project_id == project_id
    ).order_by(desc(models.ExitLinkClick.clicked_at)).limit(limit).all()
    
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
