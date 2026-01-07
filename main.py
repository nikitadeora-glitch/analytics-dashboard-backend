from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from sqlalchemy.orm import Session

from database import engine, get_db, Base
from routers import projects, analytics, visitors, pages, traffic_sources, reports, auth
import models
import os

# ---------------------------------------------------
# Create DB tables
# ---------------------------------------------------
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------
# Custom CORS Middleware (Allow All Origins with Credentials)
# ---------------------------------------------------
class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        response = await call_next(request)
        
        # Add CORS headers for all origins
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            
        return response

# ---------------------------------------------------
# FastAPI App
# ---------------------------------------------------
app = FastAPI(title="State Counter Analytics API")

# Add custom CORS middleware
app.add_middleware(CustomCORSMiddleware)

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

# ---------------------------------------------------
# Root Routes
# ---------------------------------------------------
@app.get("/")
def root():
    return {"message": "State Counter Analytics API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

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
