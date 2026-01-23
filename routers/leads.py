from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

router = APIRouter()

class LeadCreate(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    message: Optional[str] = None
    utm: Optional[dict] = None  # UTM parameters object

class LeadResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

@router.post("/submit", response_model=dict)
async def submit_lead(lead_data: LeadCreate):
    """Submit a lead with UTM tracking"""
    # Log UTM data if present
    if lead_data.utm:
        print(f"🎯 UTM Data during lead submission: {lead_data.utm}")
    
    # Here you would normally save to database
    # For now, just return success with UTM info
    return {
        "message": "Lead submitted successfully",
        "lead": {
            "email": lead_data.email,
            "name": lead_data.name,
            "company": lead_data.company
        },
        "utm_captured": bool(lead_data.utm),
        "utm_data": lead_data.utm
    }
