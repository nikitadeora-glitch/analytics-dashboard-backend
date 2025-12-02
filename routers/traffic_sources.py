from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from database import get_db
import models

router = APIRouter()

@router.get("/{project_id}/sources")
def get_traffic_sources(project_id: int, db: Session = Depends(get_db)):
    try:
        sources = db.query(
            models.TrafficSource.source_type,
            models.TrafficSource.source_name,
            func.sum(models.TrafficSource.visit_count).label('count')
        ).filter(
            models.TrafficSource.project_id == project_id
        ).group_by(
            models.TrafficSource.source_type,
            models.TrafficSource.source_name
        ).order_by(desc('count')).all()
        
        total = sum([s[2] for s in sources]) if sources else 0
        
        result = []
        for s in sources:
            source_type = s[0]
            source_name = s[1]
            
            # Calculate bounce rate for this specific source
            # Get all visits that match this traffic source
            visits = db.query(models.Visit).filter(
                models.Visit.project_id == project_id
            ).all()
            
            # Filter visits by matching referrer to source type
            matching_visits = []
            for visit in visits:
                referrer = (visit.referrer or '').lower()
                
                # Match based on source type and name
                if source_type == 'direct' and (referrer == 'direct' or referrer == ''):
                    matching_visits.append(visit)
                elif source_type == 'organic':
                    # Check if referrer contains search engine name
                    if source_name.lower() in referrer:
                        matching_visits.append(visit)
                elif source_type == 'social':
                    # Check if referrer contains social media name
                    if source_name.lower() in referrer:
                        matching_visits.append(visit)
                elif source_type == 'email':
                    if 'mail' in referrer or 'outlook' in referrer or 'gmail' in referrer:
                        matching_visits.append(visit)
                elif source_type == 'referral':
                    if source_name.lower() in referrer:
                        matching_visits.append(visit)
                elif source_type == 'paid':
                    # Check UTM parameters or source name in referrer
                    if source_name.lower() in referrer:
                        matching_visits.append(visit)
            
            # Calculate bounce rate (entry_page == exit_page or exit_page is None)
            total_visits = len(matching_visits)
            bounced_visits = 0
            
            for visit in matching_visits:
                # Bounced if: exit_page is None OR entry_page == exit_page
                if not visit.exit_page or (visit.entry_page and visit.exit_page and visit.entry_page == visit.exit_page):
                    bounced_visits += 1
            
            bounce_rate = round((bounced_visits / total_visits * 100), 1) if total_visits > 0 else 0
            
            result.append({
                "source_type": source_type,
                "source_name": source_name,
                "count": s[2],
                "percentage": round((s[2] / total * 100), 2) if total > 0 else 0,
                "bounce_rate": bounce_rate
            })
        
        return result
    except Exception as e:
        print(f"Error in get_traffic_sources: {e}")
        import traceback
        traceback.print_exc()
        return []

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
