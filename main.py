from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from database import engine, get_db, Base
from routers import projects, analytics, visitors, pages, traffic_sources, reports
import models
import os

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="State Counter Analytics API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api/projects", tags=["Projects"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(visitors.router, prefix="/api/visitors", tags=["Visitors"])
app.include_router(pages.router, prefix="/api/pages", tags=["Pages"])
app.include_router(traffic_sources.router, prefix="/api/traffic", tags=["Traffic Sources"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])

@app.get("/")
def root():
    return {"message": "State Counter Analytics API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/analytics.js")
def serve_analytics_script():
    """Serve the analytics.js tracking script"""
    # Get the path to analytics.js (one level up from backend folder)
    script_path = os.path.join(os.path.dirname(__file__), "..", "analytics.js")
    
    if not os.path.exists(script_path):
        raise HTTPException(status_code=404, detail="Analytics script not found")
    
    return FileResponse(
        script_path,
        media_type="application/javascript",
        headers={
            "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
            "Access-Control-Allow-Origin": "*"
        }
    )
