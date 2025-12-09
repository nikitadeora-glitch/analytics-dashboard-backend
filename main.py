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
origins = [
    "https://statecounterrahul.netlify.app",
    "http://statecounterrahul.netlify.app",
    "https://seo.prpwebs.com",
    "http://seo.prpwebs.com",
    "http://localhost:3000"
]
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[*],
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

@app.get("/api/analytics.js")
def serve_analytics_js():
    return FileResponse("analytics.js", media_type="application/javascript")