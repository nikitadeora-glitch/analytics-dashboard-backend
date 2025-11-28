from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from database import get_db
import models
from datetime import datetime, timedelta
import csv
import io

router = APIRouter()

@router.get("/{project_id}/export/csv")
def export_csv(project_id: int, days: int = 30, db: Session = Depends(get_db)):
    time_ago = datetime.utcnow() - timedelta(days=days)
    
    visits = db.query(models.Visit).filter(
        models.Visit.project_id == project_id,
        models.Visit.visited_at >= time_ago
    ).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Visitor ID', 'IP Address', 'Country', 'State', 'City',
        'Device', 'Browser', 'OS', 'Referrer', 'Entry Page',
        'Exit Page', 'Session Duration', 'Visited At'
    ])
    
    # Data
    for v in visits:
        writer.writerow([
            v.visitor_id, v.ip_address, v.country, v.state, v.city,
            v.device, v.browser, v.os, v.referrer, v.entry_page,
            v.exit_page, v.session_duration, v.visited_at
        ])
    
    output.seek(0)
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=analytics_{project_id}.csv"}
    )

@router.get("/{project_id}/summary-report")
def get_summary_report(project_id: int, start_date: str = None, end_date: str = None, db: Session = Depends(get_db)):
    from sqlalchemy import func
    
    query = db.query(models.Visit).filter(models.Visit.project_id == project_id)
    
    if start_date:
        query = query.filter(models.Visit.visited_at >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(models.Visit.visited_at <= datetime.fromisoformat(end_date))
    
    total_visits = query.count()
    unique_visitors = query.with_entities(func.count(func.distinct(models.Visit.visitor_id))).scalar()
    
    # Country breakdown
    countries = db.query(
        models.Visit.country,
        func.count(models.Visit.id).label('count')
    ).filter(
        models.Visit.project_id == project_id
    ).group_by(models.Visit.country).all()
    
    return {
        "project_id": project_id,
        "period": {"start": start_date, "end": end_date},
        "total_visits": total_visits,
        "unique_visitors": unique_visitors,
        "countries": [{"country": c[0], "count": c[1]} for c in countries]
    }
