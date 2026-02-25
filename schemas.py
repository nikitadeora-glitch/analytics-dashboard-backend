from pydantic import BaseModel, EmailStr



from datetime import datetime



from typing import Optional, List







class ProjectCreate(BaseModel):



    name: str



    domain: str







class ProjectResponse(BaseModel):



    id: int



    name: str



    domain: str



    tracking_code: str



    created_at: datetime



    is_active: bool



    



    class Config:



        from_attributes = True







class VisitCreate(BaseModel):



    visitor_id: str



    session_id: Optional[str] = None



    ip_address: Optional[str] = None



    referrer: Optional[str] = None



    entry_page: str



    device: Optional[str] = None



    browser: Optional[str] = None



    os: Optional[str] = None



    screen_resolution: Optional[str] = None



    language: Optional[str] = None



    timezone: Optional[str] = None



    local_time: Optional[str] = None



    local_time_formatted: Optional[str] = None



    timezone_offset: Optional[str] = None



    traffic_source: Optional[str] = None



    traffic_name: Optional[str] = None



    utm_source: Optional[str] = None



    utm_medium: Optional[str] = None



    utm_campaign: Optional[str] = None







class VisitResponse(BaseModel):



    id: int



    visitor_id: str



    country: Optional[str]



    state: Optional[str]



    city: Optional[str]



    device: Optional[str]



    browser: Optional[str]



    referrer: Optional[str]



    visited_at: datetime



    



    class Config:



        from_attributes = True







class PageViewCreate(BaseModel):



    url: str



    title: Optional[str] = None



    time_spent: Optional[int] = 0



    scroll_depth: Optional[float] = 0.0







class SummaryStats(BaseModel):



    total_visits: int



    unique_visitors: int



    live_visitors: int



    top_pages: List[dict]



    top_sources: List[dict]



    device_stats: dict







class PageStats(BaseModel):



    url: str



    title: Optional[str]



    total_views: int



    unique_views: int



    avg_time_spent: float



    bounce_rate: float







class TrafficSourceStats(BaseModel):



    source_type: str



    source_name: str



    visit_count: int



    percentage: float







# Authentication Schemas



class UserCreate(BaseModel):



    full_name: str



    email: EmailStr



    company_name: Optional[str] = None  # Make optional



    password: str



    utm: Optional[dict] = None  # UTM parameters object







class UserLogin(BaseModel):



    email: EmailStr



    password: str



    utm: Optional[dict] = None  # UTM parameters object







class UserResponse(BaseModel):



    id: int



    full_name: str



    email: str



    company_name: str



    is_verified: bool



    created_at: datetime



    



    class Config:



        from_attributes = True







class Token(BaseModel):



    access_token: str



    refresh_token: str



    token_type: str



    user: dict







class PasswordResetRequest(BaseModel):



    email: EmailStr



    utm: Optional[dict] = None  # UTM parameters object







class PasswordResetConfirm(BaseModel):



    token: str



    password: str







class GoogleLoginSchema(BaseModel):



    id_token: str



    utm: Optional[dict] = None  # UTM parameters object







class CartActionCreate(BaseModel):



    action: str  # 'add_to_cart' or 'remove_from_cart'



    product_id: Optional[str] = None



    product_name: Optional[str] = None



    product_url: Optional[str] = None



    page_url: Optional[str] = None











class ChatMessageCreate(BaseModel):



    session_id: str



    role: str  # 'user' or 'ai'



    message: str











class ChatMessageResponse(BaseModel):



    id: int



    session_id: str



    role: str



    message: str



    created_at: datetime







    class Config:



        from_attributes = True











class ChatHistoryResponse(BaseModel):



    session_id: str



    messages: List[ChatMessageResponse]



