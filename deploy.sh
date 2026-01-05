#!/bin/bash

# Production Deployment Script for Analytics Dashboard Backend
# Usage: ./deploy.sh

echo "🚀 Starting Production Deployment..."

# 1. Update code from git
echo "📥 Pulling latest code..."
git pull origin main

# 2. Install dependencies including Google OAuth
echo "📦 Installing dependencies..."
pip install -r requirements.txt
pip install google-auth google-auth-oauthlib google-auth-httplib2

# 3. Set environment variables
echo "⚙️ Setting environment variables..."
export GOOGLE_CLIENT_ID="276575813186-e1q7equvp7nq222q5sbal2f7aaensau3.apps.googleusercontent.com"
export JWT_SECRET_KEY="your-production-jwt-secret-key-change-this"
export DATABASE_URL="sqlite:///./analytics.db"

# 4. Create database tables
echo "🗄️ Creating database tables..."
python -c "from database import engine, Base; Base.metadata.create_all(bind=engine)"

# 5. Start the server
echo "🌐 Starting FastAPI server..."
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

echo "✅ Deployment complete!"
echo "📍 Server running on: http://0.0.0.0:8000"
echo "🔗 API endpoints available at: http://your-domain.com/api"
