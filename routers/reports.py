from fastapi import APIRouter, Depends, Response, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
import models
from datetime import datetime, timedelta
import csv
import io
import utils
import pytz
router = APIRouter()

# ---------------------------------------
# ISO datetime safe parser
# ---------------------------------------
# IST = pytz.timezone("Asia/Kolkata")
# def parse_iso_datetime(value: str):
#     try:
#         return datetime.fromisoformat(
#             value.strip().replace("Z", "+00:00")
#         )
#     except Exception:
#         raise HTTPException(
#             status_code=400,
#             detail=f"Invalid datetime format: {value}"
#         )
import pytz
from datetime import datetime, timedelta
from fastapi import HTTPException

IST = pytz.timezone("Asia/Kolkata")

def parse_iso_datetime(value: str) -> datetime:
    try:
        dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        # ensure tz-aware
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)
        return dt
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid datetime format: {value}")
        
# def normalize_date_range(start_date: str, end_date: str):
    """
    Frontend sends rolling timestamps.
    Backend converts them into FULL CALENDAR DAYS (IST),
    for 1 day, 7 days, or any custom range.
    """

    # 1. Parse frontend UTC timestamps
    start_utc = parse_iso_datetime(start_date)
    end_utc = parse_iso_datetime(end_date)

    # 2. Convert to IST
    start_ist = start_utc.astimezone(IST)
    end_ist = end_utc.astimezone(IST)
    day_gap = (end_ist.date() - start_ist.date()).days
    print("days gap")
    print(day_gap)

    # 3. Calculate number of calendar days selected
    days_count = (end_ist.date() - start_ist.date()).days + 1

    # 4. Always anchor on END DATE (calendar logic)
    end_day = end_ist.date()
    start_day = end_day - timedelta(days=day_gap-1)

    # 5. Normalize to full IST days
    start_ist = datetime.combine(
        start_day,
        datetime.min.time(),
        tzinfo=IST
    )

    end_ist = datetime.combine(
        end_day,
        datetime.max.time(),
        tzinfo=IST
    )

    # 6. Convert back to UTC for DB query
    return (
        start_ist.astimezone(pytz.UTC),
        end_ist.astimezone(pytz.UTC)
    )

# def normalize_date_range(start_date: str, end_date: str):
#     """
#     Frontend sends rolling timestamps (UTC).
#     Backend converts them to FULL CALENDAR DAYS (IST) inclusive.
#     """

#     start_utc = parse_iso_datetime(start_date)
#     end_utc = parse_iso_datetime(end_date)

#     # Convert to IST
#     start_ist = start_utc.astimezone(IST)
#     end_ist = end_utc.astimezone(IST)

#     # inclusive calendar days count
#     days_count = (end_ist.date() - start_ist.date()).days + 1
#     if days_count < 1:
#         raise HTTPException(status_code=400, detail="Invalid date range (end before start)")

#     # Anchor to end-day (IST), and stretch to full days
#     end_day = end_ist.date()
#     start_day = end_day - timedelta(days=days_count - 1)

#     # IMPORTANT: pytz requires localize()
#     start_ist_full = IST.localize(datetime.combine(start_day, datetime.min.time()))
#     end_ist_full = IST.localize(datetime.combine(end_day, datetime.max.time()))

#     return (
#         start_ist_full.astimezone(pytz.UTC),
#         end_ist_full.astimezone(pytz.UTC),
#     )


from datetime import datetime, time
import pytz

IST = pytz.timezone("Asia/Kolkata")

from datetime import datetime, time
import pytz

IST = pytz.timezone("Asia/Kolkata")

def normalize_date_range(start_date_str: str, end_date_str: str):
    # Parse ISO string (frontend sends UTC Z)
    start_utc = datetime.fromisoformat(start_date_str.replace("Z", "+00:00"))
    end_utc = datetime.fromisoformat(end_date_str.replace("Z", "+00:00"))

    # Convert to IST
    start_ist = start_utc.astimezone(IST)
    end_ist = end_utc.astimezone(IST)

    # FORCE FULL DAY RANGE (VERY IMPORTANT)
    start_ist = datetime.combine(start_ist.date(), time.min).replace(tzinfo=IST)
    end_ist = datetime.combine(end_ist.date(), time.max).replace(tzinfo=IST)

    # Convert back to UTC for DB
    return start_ist.astimezone(pytz.UTC), end_ist.astimezone(pytz.UTC)




# ---------------------------------------
# EXPORT CSV
# ---------------------------------------
@router.get("/{project_id}/export/csv")
def export_csv(project_id: int, days: int = 30, db: Session = Depends(get_db)):
    start_date_ist = utils.get_ist_start_of_day(days - 1)
    start_date_utc = utils.ist_to_utc(start_date_ist)
    
    visits = db.query(models.Visit).filter(
        models.Visit.project_id == project_id,
        models.Visit.visited_at >= start_date_utc
    ).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Visitor ID', 'IP Address', 'Country', 'State', 'City',
        'Device', 'Browser', 'OS', 'Referrer', 'Entry Page',
        'Exit Page', 'Session Duration', 'Visited At'
    ])
    
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

# ---------------------------------------
# SUMMARY REPORT (FIXED)
# ---------------------------------------
# @router.get("/{project_id}/summary-report")
# def get_summary_report(
#     project_id: int,
#     start_date: str | None = None,
#     end_date: str | None = None,
#     db: Session = Depends(get_db)
#     ):
#     query = db.query(models.Visit).filter(
#         models.Visit.project_id == project_id
#     )
#     print(" i am in api")
#     if start_date:
#         print("i am under start date")
#         start_dt = parse_iso_datetime(start_date)
#         print(query.count())
#         query = query.filter(models.Visit.visited_at >= start_dt)
#         print(query.count())

#     if end_date:
#         print("i am under end date")
#         end_dt = parse_iso_datetime(end_date)
#         print(query.count())
#         query = query.filter(models.Visit.visited_at <= end_dt)
#         print(query.count())

#     total_visits = query.count()
#     unique_visitors = query.with_entities(
#         func.count(func.distinct(models.Visit.visitor_id))
#     ).scalar()

#     countries = query.with_entities(
#         models.Visit.country,
#         func.count(models.Visit.id).label("count")
#     ).group_by(models.Visit.country).all()

#     return {
#         "project_id": project_id,
#         "period": {
#             "start": start_date,
#             "end": end_date
#         },
#         "total_visits": total_visits,
#         "unique_visitors": unique_visitors,
#         "countries": [
#             {"country": c.country, "count": c.count} for c in countries
#         ]
#     }



# @router.get("/{project_id}/summary-report")
# def get_summary_report(
#     project_id: int,
#     start_date: str | None = None,
#     end_date: str | None = None,
#     db: Session = Depends(get_db)
#     ):
#     query = db.query(models.Visit).filter(
#         models.Visit.project_id == project_id
#     )

#     # Apply DAY-BASED date filter (IST aligned)
#     if start_date and end_date:
#         start_dt, end_dt = normalize_date_range(start_date, end_date)
#         print(start_dt)
#         print(end_dt)

#         query = query.filter(
#             models.Visit.visited_at >= start_dt,
#             models.Visit.visited_at <= end_dt
#         )

#     # Total visits (VISITS, not pageviews)
#     total_visits = query.count()

#     # Unique visitors
#     unique_visitors = query.with_entities(
#         func.count(func.distinct(models.Visit.visitor_id))
#     ).scalar()

#     # Country breakdown (same filtered data)
#     countries = query.with_entities(
#         models.Visit.country,
#         func.count(models.Visit.id).label("count")
#     ).group_by(models.Visit.country).all()

#     return {
#         "project_id": project_id,
#         "period": {
#             "start": start_date,
#             "end": end_date
#         },
#         "total_visits": total_visits,
#         "unique_visitors": unique_visitors,
#         "countries": [
#             {"country": c.country, "count": c.count}
#             for c in countries
#         ]
#     }


@router.get("/{project_id}/summary-report")
def get_summary_report(
    project_id: int,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Visit).filter(
        models.Visit.project_id == project_id
    )

    if start_date and end_date:
        start_dt, end_dt = normalize_date_range(start_date, end_date)

        print("FILTER START (UTC):", start_dt)
        print("FILTER END   (UTC):", end_dt)

        query = query.filter(
            models.Visit.visited_at >= start_dt,
            models.Visit.visited_at <= end_dt
        )

    total_visits = query.count()

    unique_visitors = query.with_entities(
        func.count(func.distinct(models.Visit.visitor_id))
    ).scalar()

    countries = query.with_entities(
        models.Visit.country,
        func.count(models.Visit.id).label("count")
    ).group_by(models.Visit.country).all()

    return {
        "project_id": project_id,
        "period": {
            "start": start_date,
            "end": end_date
        },
        "total_visits": total_visits,
        "unique_visitors": unique_visitors,
        "countries": [
            {"country": c.country or "Unknown", "count": c.count} 
            for c in countries if c.country
        ]
    }
