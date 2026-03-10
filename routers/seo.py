from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import os
import sys
import requests
import json
from datetime import datetime, timedelta
import urllib.parse

from database import get_db
from models import SEOConnection, SEOToken, Project, User

router = APIRouter()

# Pydantic models
class SelectSiteRequest(BaseModel):
    site_url: str

class SiteResponse(BaseModel):
    sites: List[str]

class OverviewResponse(BaseModel):
    line: List[dict]
    donut: List[dict]
    metrics: dict
    table: List[dict]

# Google OAuth configuration
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
SEO_OAUTH_REDIRECT_URI = os.getenv("SEO_OAUTH_REDIRECT_URI", "http://localhost:8000/api/seo/oauth/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Dynamic port detection for development
import socket
def get_server_port():
    """Try to detect the current server port"""
    # For development, we'll use a common approach
    # Check if we're running on a different port than configured
    if "8001" in str(os.getenv("PORT", "")) or os.getenv("ENVIRONMENT") == "development":
        return "8001"
    return "8000"

# Auto-correct redirect URI for development
if "localhost:8000" in SEO_OAUTH_REDIRECT_URI and get_server_port() == "8001":
    SEO_OAUTH_REDIRECT_URI = SEO_OAUTH_REDIRECT_URI.replace(":8000", ":8001")
    print(f"🔧 Auto-corrected redirect URI for port 8001: {SEO_OAUTH_REDIRECT_URI}")

# Enhanced configuration validation
print("=== SEO OAUTH CONFIGURATION CHECK ===")
print(f"CLIENT ID: {'SET' if GOOGLE_CLIENT_ID else 'NOT SET'}")
print(f"CLIENT SECRET: {'SET' if GOOGLE_CLIENT_SECRET else 'NOT SET'}")
print(f"REDIRECT URI: {SEO_OAUTH_REDIRECT_URI}")
print(f"FRONTEND URL: {FRONTEND_URL}")

# Check if redirect URI is properly configured
# Skip validation during testing or CI/CD
is_test_environment = (
    os.getenv("ENVIRONMENT") == "test" or
    os.getenv("CI") is not None or
    os.getenv("PYTEST_CURRENT_TEST") is not None or
    "pytest" in sys.modules
)

if not is_test_environment:
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        print("❌ ERROR: Google OAuth credentials not configured")
        print("Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in environment variables")
        raise HTTPException(status_code=500, detail="Google OAuth credentials not configured")

# Validate redirect URI format
if not SEO_OAUTH_REDIRECT_URI.startswith(("http://localhost", "https://")):
    print("⚠️  WARNING: Redirect URI should be a valid HTTP/HTTPS URL")
    
if SEO_OAUTH_REDIRECT_URI.endswith("/"):
    print("⚠️  WARNING: Redirect URI ends with slash - this may cause issues")
    print("Google Console URI should match exactly including/excluding trailing slash")

print("✅ SEO OAuth configuration loaded successfully")

# Google OAuth URLs
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GSC_API_BASE = "https://www.googleapis.com/webmasters/v3"

def get_google_auth_url(project_id: int) -> str:
    """Generate Google OAuth URL"""
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": SEO_OAUTH_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid https://www.googleapis.com/auth/webmasters.readonly https://www.googleapis.com/auth/userinfo.email",
        "access_type": "offline",
        "prompt": "consent",
        "state": str(project_id)
    }
    
    auth_url = f"{GOOGLE_AUTH_URL}?{urllib.parse.urlencode(params)}"
    
    # DEBUG: Print authorization URL details
    print("=== AUTH URL DEBUG ===")
    print("CLIENT ID:", GOOGLE_CLIENT_ID)
    print("REDIRECT URI:", SEO_OAUTH_REDIRECT_URI)
    print("AUTH URL:", auth_url)
    print("PROJECT ID:", project_id)
    
    return auth_url

async def get_or_refresh_tokens(connection_id: int, db: Session) -> str:
    """Get valid access token, refresh if needed"""
    token_record = db.query(SEOToken).filter(SEOToken.connection_id == connection_id).first()
    
    if not token_record:
        raise HTTPException(status_code=404, detail="No tokens found")
    
    # Check if token is expired or will expire in next 5 minutes
    if datetime.utcnow() >= token_record.expiry_datetime - timedelta(minutes=5):
        # Refresh the token
        data = {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "refresh_token": token_record.refresh_token,
            "grant_type": "refresh_token"
        }
        
        response = requests.post(GOOGLE_TOKEN_URL, data=data)
        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Failed to refresh token")
        
        token_data = response.json()
        
        # Update token in database
        token_record.access_token = token_data["access_token"]
        token_record.expiry_datetime = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        db.commit()
    
    return token_record.access_token

@router.get("/debug-config")
async def debug_config():
    """Debug endpoint to check OAuth configuration"""
    return {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": "***" if GOOGLE_CLIENT_SECRET else "NOT_SET",
        "redirect_uri": SEO_OAUTH_REDIRECT_URI,
        "token_url": GOOGLE_TOKEN_URL,
        "auth_url": GOOGLE_AUTH_URL,
        "frontend_url": FRONTEND_URL,
        "client_id_set": bool(GOOGLE_CLIENT_ID),
        "client_secret_set": bool(GOOGLE_CLIENT_SECRET),
        "redirect_uri_set": bool(SEO_OAUTH_REDIRECT_URI)
    }

@router.get("/{project_id}/connect-url")
async def get_connect_url(project_id: int, db: Session = Depends(get_db)):
    """Generate Google OAuth connect URL"""
    
    # Verify project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    auth_url = get_google_auth_url(project_id)
    
    return {"auth_url": auth_url}

@router.get("/oauth/callback")
async def oauth_callback(code: str, state: str, db: Session = Depends(get_db)):
    """Handle OAuth callback from Google"""
    
    # DEBUG: Print all configuration values
    print("=== OAUTH CALLBACK DEBUG ===")
    print("CLIENT ID:", GOOGLE_CLIENT_ID)
    print("CLIENT SECRET:", GOOGLE_CLIENT_SECRET)
    print("REDIRECT URI:", SEO_OAUTH_REDIRECT_URI)
    print("TOKEN URL:", GOOGLE_TOKEN_URL)
    print("AUTH CODE:", code[:10] + "..." if len(code) > 10 else code)
    print("STATE:", state)
    
    try:
        project_id = int(state)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid state parameter")
    
    # Exchange code for tokens
    data = {
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": SEO_OAUTH_REDIRECT_URI
    }
    
    print("TOKEN EXCHANGE DATA:", {k: v if k != "client_secret" else "***" for k, v in data.items()})
    
    response = requests.post(GOOGLE_TOKEN_URL, data=data)
    
    print("STATUS:", response.status_code)
    print("RESPONSE:", response.text)
    
    if response.status_code != 200:
        # Return the actual error message instead of generic message
        error_detail = f"Token exchange failed: {response.text}"
        raise HTTPException(status_code=400, detail=error_detail)
    
    token_data = response.json()
    
    # Get user info from Google
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    user_response = requests.get("https://www.googleapis.com/oauth2/v3/userinfo", headers=headers)
    
    if user_response.status_code != 200:
        raise HTTPException(
    status_code=400,
    detail=f"Failed to get user info: {user_response.text}"
)
    
    user_info = user_response.json()
    google_email = user_info["email"]
    
    # Get or create SEO connection
    existing_connection = db.query(SEOConnection).filter(
        SEOConnection.project_id == project_id,
        SEOConnection.google_email == google_email
    ).first()
    
    if existing_connection:
        # Update existing connection
        connection = existing_connection
        connection.is_connected = True
        connection.updated_at = datetime.utcnow()
        
        # Update tokens
        existing_token = db.query(SEOToken).filter(SEOToken.connection_id == connection.id).first()
        if existing_token:
            existing_token.access_token = token_data["access_token"]
            existing_token.refresh_token = token_data.get("refresh_token", existing_token.refresh_token)
            existing_token.expiry_datetime = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            existing_token.updated_at = datetime.utcnow()
        else:
            # Create new token record
            new_token = SEOToken(
                connection_id=connection.id,
                access_token=token_data["access_token"],
                refresh_token=token_data["refresh_token"],
                expiry_datetime=datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            )
            db.add(new_token)
    else:
        # Create new connection
        # Get user_id from project
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        connection = SEOConnection(
            project_id=project_id,
            user_id=project.user_id,
            google_email=google_email,
            is_connected=True
        )
        db.add(connection)
        db.flush()  # Get the ID
        
        # Create token record
        new_token = SEOToken(
            connection_id=connection.id,
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            expiry_datetime=datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
        )
        db.add(new_token)
    
    db.commit()
    
    # Redirect to frontend with success
    redirect_url = f"{FRONTEND_URL}/projects/{project_id}/seo?connected=1"
    return RedirectResponse(url=redirect_url)

@router.get("/{project_id}/sites")
async def get_sites(project_id: int, db: Session = Depends(get_db)):
    """Get list of GSC sites for the connected user"""
    
    # Find SEO connection for this project
    connection = db.query(SEOConnection).filter(
        SEOConnection.project_id == project_id,
        SEOConnection.is_connected == True
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="No SEO connection found for this project")
    
    # Get valid access token
    access_token = await get_or_refresh_tokens(connection.id, db)
    
    # Call GSC API to get sites
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{GSC_API_BASE}/sites", headers=headers)
    
    if response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to fetch sites from Google Search Console")
    
    data = response.json()
    sites = [site["siteUrl"] for site in data.get("siteEntry", [])]
    
    return SiteResponse(sites=sites)

@router.post("/{project_id}/select-site")
async def select_site(project_id: int, request: SelectSiteRequest, db: Session = Depends(get_db)):
    """Select and save the GSC site for this project"""
    
    # Find SEO connection
    connection = db.query(SEOConnection).filter(
        SEOConnection.project_id == project_id,
        SEOConnection.is_connected == True
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="No SEO connection found for this project")
    
    # Update the site URL
    connection.site_url = request.site_url
    connection.updated_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Site selected successfully"}

@router.get("/{project_id}/overview")
async def get_overview(project_id: int, range: str = "7d", db: Session = Depends(get_db)):
    """Get SEO overview data"""
    
    # Find SEO connection
    connection = db.query(SEOConnection).filter(
        SEOConnection.project_id == project_id,
        SEOConnection.is_connected == True,
        SEOConnection.site_url.isnot(None)
    ).first()
    
    if not connection:
        raise HTTPException(status_code=404, detail="No SEO connection or site selected for this project")
    
    # Get valid access token
    access_token = await get_or_refresh_tokens(connection.id, db)
    
    # Calculate date range
    end_date = datetime.utcnow().date()
    if range == "7d":
        start_date = end_date - timedelta(days=6)
    elif range == "30d":
        start_date = end_date - timedelta(days=29)
    elif range == "90d":
        start_date = end_date - timedelta(days=89)
    else:
        start_date = end_date - timedelta(days=6)  # default to 7d
    
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # Make 3 API calls for different dimensions
    line_data = []
    donut_data = []
    table_data = []
    
    try:
        # 1. Line chart data (by date)
        line_request = {
            "startDate": start_date_str,
            "endDate": end_date_str,
            "dimensions": ["date"]
        }
        
        line_response = requests.post(
            f"{GSC_API_BASE}/sites/{urllib.parse.quote_plus(connection.site_url)}/searchAnalytics/query",
            headers=headers,
            json=line_request
        )
        
        if line_response.status_code == 200:
            line_result = line_response.json()
            line_data = [{"date": row["keys"][0], "clicks": row["clicks"]} for row in line_result.get("rows", [])]
        
        # 2. Donut chart data (by country)
        donut_request = {
            "startDate": start_date_str,
            "endDate": end_date_str,
            "dimensions": ["country"]
        }
        
        donut_response = requests.post(
            f"{GSC_API_BASE}/sites/{urllib.parse.quote_plus(connection.site_url)}/searchAnalytics/query",
            headers=headers,
            json=donut_request
        )
        
        if donut_response.status_code == 200:
            donut_result = donut_response.json()
            total_clicks = sum(row["clicks"] for row in donut_result.get("rows", []))
            donut_data = [
                {
                    "name": row["keys"][0],
                    "value": row["clicks"],
                    "percentage": round((row["clicks"] / total_clicks * 100), 2) if total_clicks > 0 else 0
                }
                for row in donut_result.get("rows", [])
            ]
        
        # 3. Table data (by query/keyword)
        table_request = {
            "startDate": start_date_str,
            "endDate": end_date_str,
            "dimensions": ["query"],
            "rowLimit": 100
        }
        
        table_response = requests.post(
            f"{GSC_API_BASE}/sites/{urllib.parse.quote_plus(connection.site_url)}/searchAnalytics/query",
            headers=headers,
            json=table_request
        )
        
        if table_response.status_code == 200:
            table_result = table_response.json()
            table_data = [
                {
                    "keyword": row["keys"][0],
                    "clicks": row["clicks"],
                    "impressions": row["impressions"],
                    "ctr": round(row["ctr"] * 100, 2),
                    "position": round(row["position"], 1)
                }
                for row in table_result.get("rows", [])
            ]
        
        # Calculate overall metrics
        total_clicks = sum(row["clicks"] for row in table_data)
        total_impressions = sum(row["impressions"] for row in table_data)
        avg_ctr = round((total_clicks / total_impressions * 100), 2) if total_impressions > 0 else 0
        avg_position = round(sum(row["position"] * row["clicks"] for row in table_data) / total_clicks, 1) if total_clicks > 0 else 0
        
        metrics = {
            "clicks": total_clicks,
            "impressions": total_impressions,
            "ctr": avg_ctr,
            "position": avg_position
        }
        
        return OverviewResponse(
            line=line_data,
            donut=donut_data,
            metrics=metrics,
            table=table_data[:10]  # Return top 10 keywords
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data from Google Search Console: {str(e)}")
