#!/usr/bin/env python3
"""
Production Deployment Check Script
Run this to verify if the backend is properly configured for production
"""

import os
import sys
import requests
from dotenv import load_dotenv

def check_backend_health():
    """Check if backend API is accessible"""
    print("🔍 Checking Backend API Health...")
    print("=" * 50)
    
    # Load environment
    load_dotenv('.env.production')
    
    # Get API URL
    api_url = os.getenv('VITE_API_URL', 'https://api.seo.prpwebs.com/api')
    health_url = api_url.replace('/api', '') + '/health'
    
    print(f"📡 Checking: {health_url}")
    
    try:
        response = requests.get(health_url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Backend is running!")
            print(f"📊 Status: {data.get('status')}")
            print(f"⏰ Timestamp: {data.get('timestamp')}")
            
            if 'email_config' in data:
                email_config = data['email_config']
                print(f"\n📧 Email Configuration:")
                print(f"  Configured: {email_config.get('configured')}")
                print(f"  Server: {email_config.get('server')}")
                print(f"  Port: {email_config.get('port')}")
                print(f"  Frontend URL: {email_config.get('frontend_url')}")
                
                if not email_config.get('configured'):
                    print("❌ Email configuration is incomplete!")
                    print("   Check MAIL_USERNAME and MAIL_PASSWORD in production environment")
            
            return True
        else:
            print(f"❌ Backend returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out - Backend may be down or slow")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend - Server may be down")
        print("   Check if the backend is deployed and running")
        return False
    except Exception as e:
        print(f"❌ Error checking backend: {str(e)}")
        return False

def check_cors():
    """Check CORS configuration"""
    print("\n🌐 Checking CORS Configuration...")
    print("=" * 50)
    
    api_url = os.getenv('VITE_API_URL', 'https://api.seo.prpwebs.com/api')
    
    try:
        # Send OPTIONS request to check CORS
        response = requests.options(f"{api_url}/forgot-password", timeout=10, headers={
            'Origin': 'https://seo.prpwebs.com',
            'Access-Control-Request-Method': 'POST',
            'Access-Control-Request-Headers': 'Content-Type'
        })
        
        print(f"📡 OPTIONS Request Status: {response.status_code}")
        
        cors_headers = {
            'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
            'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
        }
        
        print("\n📋 CORS Headers:")
        for header, value in cors_headers.items():
            if value:
                print(f"  {header}: {value}")
            else:
                print(f"  {header}: ❌ Missing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking CORS: {str(e)}")
        return False

def main():
    """Main check function"""
    print("🚀 Production Deployment Check")
    print("=" * 50)
    
    # Check backend health
    backend_ok = check_backend_health()
    
    # Check CORS
    cors_ok = check_cors()
    
    print("\n" + "=" * 50)
    print("📋 Summary:")
    print(f"  Backend Health: {'✅ OK' if backend_ok else '❌ FAILED'}")
    print(f"  CORS Config: {'✅ OK' if cors_ok else '❌ FAILED'}")
    
    if not backend_ok:
        print("\n🔧 Backend Issues:")
        print("  1. Check if backend is deployed and running")
        print("  2. Verify domain DNS configuration")
        print("  3. Check server logs for errors")
        print("  4. Ensure environment variables are set correctly")
    
    if not cors_ok:
        print("\n🔧 CORS Issues:")
        print("  1. Check CORS middleware configuration")
        print("  2. Verify allowed origins list")
        print("  3. Check if frontend domain is whitelisted")

if __name__ == "__main__":
    main()
