import geoip2.database
from user_agents import parse
from typing import Optional
import os

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
