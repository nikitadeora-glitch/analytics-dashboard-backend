from datetime import datetime, timedelta
from sqlalchemy import func, Date, cast
import os
import geoip2.database
from user_agents import parse
from typing import Optional

def get_ist_now():
    """Get current time in IST"""
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

def get_ist_start_of_day(days_ago=0):
    """Get start of day in IST (00:00:00)"""
    ist_now = get_ist_now()
    ist_day = ist_now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days_ago)
    return ist_day

def ist_to_utc(dt: datetime):
    """Convert IST datetime to UTC"""
    return dt - timedelta(hours=5, minutes=30)

def get_ist_date_expr(column, dialect_name):
    """SQLAlchemy expression to get IST date from UTC column"""
    if dialect_name == 'sqlite':
        return func.date(column, '+330 minutes')
    else:
        # Postgres - assuming the column is UTC timestamp without timezone
        return cast(func.timezone('Asia/Kolkata', func.timezone('UTC', column)), Date)

def get_ist_hour_expr(column, dialect_name):
    """SQLAlchemy expression to get IST hour from UTC column"""
    if dialect_name == 'sqlite':
        return func.strftime('%H', column, '+330 minutes')
    else:
        # Postgres
        from sqlalchemy import extract
        return extract('hour', func.timezone('Asia/Kolkata', func.timezone('UTC', column)))

def get_truncated_hour_expr(column, dialect_name):
    """SQLAlchemy expression to get IST truncated hour from UTC column"""
    if dialect_name == 'sqlite':
        return func.strftime('%Y-%m-%d %H:00:00', column, '+330 minutes')
    else:
        # Postgres
        return func.date_trunc('hour', func.timezone('Asia/Kolkata', func.timezone('UTC', column)))


def get_location_from_ip(ip_address: str) -> dict:
    """Get location data from IP address using GeoIP2"""
    try:
        geoip_path = os.getenv("GEOIP_DB_PATH", "./GeoLite2-City.mmdb")
        if not os.path.exists(geoip_path):
            return {}
        
        with geoip2.database.Reader(geoip_path) as reader:
            response = reader.city(ip_address)
            return {
                "country": response.country.name,
                "state": response.subdivisions.most_specific.name if response.subdivisions else None,
                "city": response.city.name,
                "latitude": response.location.latitude,
                "longitude": response.location.longitude
            }
    except Exception:
        return {}

def parse_user_agent(user_agent_string: str) -> dict:
    """Parse user agent string to extract device, browser, and OS info"""
    ua = parse(user_agent_string)
    return {
        "device": "Mobile" if ua.is_mobile else "Tablet" if ua.is_tablet else "Desktop",
        "browser": f"{ua.browser.family} {ua.browser.version_string}",
        "os": f"{ua.os.family} {ua.os.version_string}"
    }

def classify_traffic_source(referrer: Optional[str], utm_source: Optional[str] = None) -> dict:
    """Classify traffic source based on referrer and UTM parameters"""
    if utm_source:
        return {"type": "campaign", "name": utm_source}
    
    if not referrer:
        return {"type": "direct", "name": "Direct"}
    
    referrer_lower = referrer.lower()
    
    # Social media
    social_platforms = {
        "facebook.com": "Facebook",
        "instagram.com": "Instagram",
        "twitter.com": "Twitter",
        "linkedin.com": "LinkedIn",
        "pinterest.com": "Pinterest"
    }
    
    for domain, name in social_platforms.items():
        if domain in referrer_lower:
            return {"type": "social", "name": name}
    
    # Search engines
    search_engines = {
        "google.com": "Google",
        "bing.com": "Bing",
        "yahoo.com": "Yahoo",
        "duckduckgo.com": "DuckDuckGo"
    }
    
    for domain, name in search_engines.items():
        if domain in referrer_lower:
            return {"type": "organic", "name": name}
    
    return {"type": "referral", "name": referrer}
