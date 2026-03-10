#!/usr/bin/env python3
"""
SEO OAuth Flow Test and Configuration Guide
This script helps diagnose OAuth issues and provides the exact configuration needed
"""

import os
import sys
sys.path.append('.')

from routers.seo import (
    GOOGLE_CLIENT_ID, 
    SEO_OAUTH_REDIRECT_URI, 
    GOOGLE_AUTH_URL,
    get_google_auth_url
)

def print_oauth_guide():
    """Print comprehensive OAuth configuration guide"""
    
    print("=" * 80)
    print("🔧 SEO OAUTH CONFIGURATION GUIDE")
    print("=" * 80)
    
    print("\n📋 CURRENT CONFIGURATION:")
    print(f"✅ Client ID: {GOOGLE_CLIENT_ID}")
    print(f"✅ Redirect URI: {SEO_OAUTH_REDIRECT_URI}")
    print(f"✅ Auth URL: {GOOGLE_AUTH_URL}")
    
    print("\n🔴 GOOGLE CONSOLE CONFIGURATION NEEDED:")
    print("Go to: https://console.cloud.google.com/apis/credentials")
    print("\n1. Find your OAuth 2.0 Client ID:")
    print(f"   Client ID: {GOOGLE_CLIENT_ID}")
    
    print("\n2. Click 'EDIT' and ensure these settings:")
    print("   ✅ Application type: Web application")
    print("   ✅ Authorized redirect URIs:")
    print(f"      ➡️  {SEO_OAUTH_REDIRECT_URI}")
    
    print("\n⚠️  COMMON ISSUES TO CHECK:")
    print("   • Redirect URI must match EXACTLY (including http/https and port)")
    print("   • No trailing slash differences")
    print("   • Client ID and Secret must be from the same project")
    
    print("\n🧪 TEST OAUTH FLOW:")
    # Generate test auth URL
    test_project_id = 13
    auth_url = get_google_auth_url(test_project_id)
    print(f"\n1. Visit this URL to test OAuth flow:")
    print(f"   {auth_url}")
    
    print(f"\n2. After Google auth, you'll be redirected to:")
    print(f"   {SEO_OAUTH_REDIRECT_URI}?code=...&state={test_project_id}")
    
    print(f"\n3. The callback will process and redirect to:")
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    print(f"   {frontend_url}/projects/{test_project_id}/seo?connected=1")
    
    print("\n🔍 DEBUGGING ENDPOINTS:")
    print(f"• Config check: http://127.0.0.1:8001/api/seo/debug-config")
    print(f"• Auth URL: http://127.0.0.1:8001/api/seo/13/connect-url")
    
    print("\n📝 ENVIRONMENT VARIABLES NEEDED:")
    print("Add these to your .env file:")
    print(f"GOOGLE_CLIENT_ID={GOOGLE_CLIENT_ID}")
    print("GOOGLE_CLIENT_SECRET=your_actual_client_secret_here")
    print(f"SEO_OAUTH_REDIRECT_URI={SEO_OAUTH_REDIRECT_URI}")
    print("FRONTEND_URL=http://localhost:3000")
    print("ENVIRONMENT=development")
    
    print("\n" + "=" * 80)

def validate_redirect_uri_format():
    """Validate redirect URI format for common issues"""
    
    print("\n🔍 REDIRECT URI VALIDATION:")
    
    issues = []
    
    # Check protocol
    if not SEO_OAUTH_REDIRECT_URI.startswith(("http://", "https://")):
        issues.append("❌ Missing http:// or https:// protocol")
    
    # Check localhost vs actual domain
    if "localhost" in SEO_OAUTH_REDIRECT_URI:
        print("ℹ️  Using localhost - ensure Google Console has localhost URI")
    
    # Check trailing slash
    if SEO_OAUTH_REDIRECT_URI.endswith("/"):
        issues.append("⚠️  Ends with trailing slash - may cause mismatch")
    
    # Check port specificity
    if ":8000" in SEO_OAUTH_REDIRECT_URI:
        print("ℹ️  Using port 8000 - ensure server runs on this port")
    elif ":8001" in SEO_OAUTH_REDIRECT_URI:
        print("ℹ️  Using port 8001 - ensure server runs on this port")
    
    # Check path format
    expected_path = "/api/seo/oauth/callback"
    if expected_path not in SEO_OAUTH_REDIRECT_URI:
        issues.append(f"❌ Expected path '{expected_path}' not found")
    
    if issues:
        print("\n🚨 ISSUES FOUND:")
        for issue in issues:
            print(f"   {issue}")
    else:
        print("✅ Redirect URI format looks correct!")
    
    return len(issues) == 0

if __name__ == "__main__":
    print_oauth_guide()
    validate_redirect_uri_format()
    
    print("\n🎯 NEXT STEPS:")
    print("1. Update Google Console with the correct redirect URI")
    print("2. Restart this server")
    print("3. Test the OAuth flow using the auth URL above")
    print("4. Check server logs for detailed debugging information")
