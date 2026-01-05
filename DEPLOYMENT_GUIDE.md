# 🚀 Production Deployment Guide

## Problem Summary
- **Local**: ✅ Working perfectly (Google login works)
- **Production**: ❌ 404 errors (FastAPI not deployed)

## Root Cause
Production server (`api.seo.prpwebs.com`) only has Nginx running with default page. FastAPI application is not deployed.

## Solution Steps

### 1. Access Production Server
```bash
# SSH into your production server
ssh user@api.seo.prpwebs.com
```

### 2. Deploy Backend Code
```bash
# Navigate to project directory
cd /path/to/analytics-dashboard-backend

# Pull latest code
git pull origin main

# Install dependencies (includes Google OAuth libraries)
pip install -r requirements.txt

# Alternative: Install Google OAuth manually if needed
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

### 3. Set Environment Variables
```bash
# Copy production environment file
cp .env.production .env

# Or set manually:
export GOOGLE_CLIENT_ID="276575813186-e1q7equvp7nq222q5sbal2f7aaensau3.apps.googleusercontent.com"
export JWT_SECRET_KEY="change-this-to-secure-secret-key"
export DATABASE_URL="sqlite:///./analytics.db"
```

### 4. Start FastAPI Server
```bash
# Option 1: Direct start
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Option 2: Use deployment script
./deploy.sh  # Linux/Mac
deploy.bat   # Windows

# Option 3: Start with process manager (recommended)
pm2 start "python -m uvicorn main:app --host 0.0.0.0 --port 8000" --name analytics-api
```

### 5. Configure Nginx Reverse Proxy
Create/edit `/etc/nginx/sites-available/analytics-api`:
```nginx
server {
    listen 80;
    server_name api.seo.prpwebs.com;

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /health {
        proxy_pass http://localhost:8000/health;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/analytics-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Test Deployment
```bash
# Test health endpoint
curl http://api.seo.prpwebs.com/health

# Test Google endpoint
curl -X POST http://api.seo.prpwebs.com/api/google \
  -H "Content-Type: application/json" \
  -d '{"id_token":"test"}'
```

## Expected Results
- Health endpoint: `{"status": "healthy"}`
- Google endpoint: `{"detail": "Invalid Google token"}` (expected for test token)

## Frontend Configuration
Frontend automatically uses production URL when `NODE_ENV=production`:
```javascript
// vite.config.js - Already configured
'import.meta.env.VITE_API_URL': JSON.stringify(process.env.NODE_ENV === 'production' 
  ? 'https://api.seo.prpwebs.com/api' 
  : 'http://127.0.0.1:8000/api')
```

## Troubleshooting

### If 404 still occurs:
1. Check if FastAPI is running: `ps aux | grep uvicorn`
2. Check port 8000: `netstat -tlnp | grep 8000`
3. Check Nginx config: `sudo nginx -t`
4. Check logs: `sudo journalctl -u nginx`

### If Google login fails:
1. Verify GOOGLE_CLIENT_ID environment variable
2. Check Google Cloud Console OAuth settings
3. Ensure domain is added to authorized origins

## Security Notes
- Change JWT_SECRET_KEY to a secure random string
- Use HTTPS in production
- Consider using process manager (pm2, systemd)
- Set up SSL certificate with Let's Encrypt

## Files Created
- `deploy.sh` - Linux/Mac deployment script
- `deploy.bat` - Windows deployment script  
- `.env.production` - Production environment variables
