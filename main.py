from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.orm import Session

from database import engine, get_db, Base
from routers import projects, analytics, visitors, pages, traffic_sources, reports, auth, leads, chathistory
import models
import os
from logging_config import *
logger = logging.getLogger("app")
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------
# Custom CORS Middleware (Allow Specific Origins with Credentials)
# ---------------------------------------------------
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Get frontend URL from environment, fallback to default
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        # List of allowed origins (both local and production)
        allowed_origins = [
            # Local development
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",  # Vite dev server alternate port
            "http://127.0.0.1:3001",  # Vite dev server alternate port
            "http://localhost:5173",  # Vite dev server
            "http://127.0.0.1:5173",  # Vite dev server
            # Production domains
            "https://seo.prpwebs.com",
            "https://www.seo.prpwebs.com",
            "https://api.seo.prpwebs.com",
            # Environment-specific frontend URL
            frontend_url,
            # Add your React frontend domain here
            "https://api.seo.prpwebs.com",
        ]
        
        # Remove duplicates and None values
        allowed_origins = list(set(filter(None, allowed_origins)))
        
        # Handle preflight requests first
        if request.method == "OPTIONS":
            response = Response()
            # Only allow specific origins when credentials are involved
            if origin and origin in allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
            elif origin:
                # For unknown origins, don't allow credentials
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "false"
            else:
                # No origin header, fallback to first allowed origin
                response.headers["Access-Control-Allow-Origin"] = allowed_origins[0]
                response.headers["Access-Control-Allow-Credentials"] = "false"
                
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
            response.headers["Access-Control-Max-Age"] = "86400"
            return response
        
        response = await call_next(request)
        
        # Add CORS headers for all responses
        if origin and origin in allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        elif origin:
            # For unknown origins, don't allow credentials
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "false"
        else:
            # No origin header, fallback to first allowed origin
            response.headers["Access-Control-Allow-Origin"] = allowed_origins[0]
            response.headers["Access-Control-Allow-Credentials"] = "false"
            
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        
        return response

# ---------------------------------------------------
# Request Logging Middleware
# ---------------------------------------------------
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        import time
        
        # Start time
        start_time = time.time()
        
        # Log incoming request
        logger.info(f"📥 {request.method} {request.url.path}")
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate response time
            process_time = time.time() - start_time
            
            # Log response
            status_emoji = "✅" if response.status_code < 400 else "❌"
            logger.info(
                f"{status_emoji} {request.method} {request.url.path} "
                f"→ {response.status_code} ({process_time:.3f}s)"
            )
            
            # Add response time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Calculate response time
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"❌ {request.method} {request.url.path} "
                f"→ ERROR ({process_time:.3f}s): {str(e)}",
                exc_info=True
            )
            raise

# ---------------------------------------------------
# FastAPI App
# ---------------------------------------------------
app = FastAPI(title="State Counter Analytics API")

# Add custom CORS middleware
app.add_middleware(CustomCORSMiddleware)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# ---------------------------------------------------
# Routers
# ---------------------------------------------------
app.include_router(auth.router, prefix="/api", tags=["Authentication"])
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(visitors.router, prefix="/api/visitors", tags=["Visitors"])
app.include_router(pages.router, prefix="/api/pages", tags=["Pages"])
app.include_router(traffic_sources.router, prefix="/api/traffic", tags=["Traffic Sources"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(leads.router, prefix="/api/lead", tags=["Leads"])
app.include_router(chathistory.router, prefix="/api/chathistory", tags=["Chat History"])

# ---------------------------------------------------
# Root Routes
# ---------------------------------------------------
@app.get("/")
def root():
    return {
        "message": "State Counter Analytics API", 
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "debug_email": "/debug/email"
        }
    }

@app.get("/health")
def health_check():
    """Enhanced health check that includes email configuration status"""
    import os
    from datetime import datetime
    import time

    # Check email configuration
    email_config = {
        "mail_username": bool(os.getenv("MAIL_USERNAME")),
        "mail_password": bool(os.getenv("MAIL_PASSWORD")),
        "mail_server": os.getenv("MAIL_SERVER", "smtp.gmail.com"),
        "mail_port": os.getenv("MAIL_PORT", "587"),
        "frontend_url": os.getenv("FRONTEND_URL", "http://localhost:3000")
    }
    
    email_configured = all([
        email_config["mail_username"],
        email_config["mail_password"]
    ])
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "email_config": {
            "configured": email_configured,
            "server": email_config["mail_server"],
            "port": email_config["mail_port"],
            "frontend_url": email_config["frontend_url"]
        }
    }

@app.get("/debug/email")
def debug_email_config():
    """Debug endpoint to check email configuration (remove in production)"""
    import os
    
    return {
        "environment": os.getenv("ENV", "development"),
        "mail_username": os.getenv("MAIL_USERNAME"),
        "mail_password_set": bool(os.getenv("MAIL_PASSWORD")),
        "mail_server": os.getenv("MAIL_SERVER"),
        "mail_port": os.getenv("MAIL_PORT"),
        "frontend_url": os.getenv("FRONTEND_URL"),
        "all_mail_env_vars": {k: v for k, v in os.environ.items() if 'MAIL' in k.upper()}
    }

# ---------------------------------------------------
# Analytics Script Serve
# ---------------------------------------------------
@app.get("/api/analytics.js")
def serve_analytics_js():
    return FileResponse(
        "analytics.js",
        media_type="application/javascript",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )

# ---------------------------------------------------
# Local Run
# ---------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
