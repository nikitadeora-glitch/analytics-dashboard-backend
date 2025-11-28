from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    domain = Column(String, unique=True, nullable=False)
    tracking_code = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    visits = relationship("Visit", back_populates="project")
    pages = relationship("Page", back_populates="project")

class Visit(Base):
    __tablename__ = "visits"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    visitor_id = Column(String, index=True)
    session_id = Column(String, index=True)
    ip_address = Column(String)
    country = Column(String)
    state = Column(String)
    city = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    isp = Column(String)
    device = Column(String)
    browser = Column(String)
    os = Column(String)
    screen_resolution = Column(String)
    language = Column(String)
    timezone = Column(String)
    local_time = Column(String)
    local_time_formatted = Column(String)
    timezone_offset = Column(String)
    referrer = Column(String)
    entry_page = Column(String)
    exit_page = Column(String)
    session_duration = Column(Integer)
    visited_at = Column(DateTime, default=datetime.utcnow, index=True)
    is_unique = Column(Boolean, default=True)
    is_new_session = Column(Boolean, default=True)
    
    project = relationship("Project", back_populates="visits")
    page_views = relationship("PageView", back_populates="visit")

class PageView(Base):
    __tablename__ = "page_views"
    
    id = Column(Integer, primary_key=True, index=True)
    visit_id = Column(Integer, ForeignKey("visits.id"))
    page_id = Column(Integer, ForeignKey("pages.id"))
    url = Column(String, nullable=False)
    title = Column(String)
    time_spent = Column(Integer)
    scroll_depth = Column(Float)
    viewed_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    visit = relationship("Visit", back_populates="page_views")
    page = relationship("Page", back_populates="page_views")

class Page(Base):
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    url = Column(String, nullable=False)
    title = Column(String)
    total_views = Column(Integer, default=0)
    unique_views = Column(Integer, default=0)
    avg_time_spent = Column(Float, default=0.0)
    bounce_rate = Column(Float, default=0.0)
    
    project = relationship("Project", back_populates="pages")
    page_views = relationship("PageView", back_populates="page")

class TrafficSource(Base):
    __tablename__ = "traffic_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    source_type = Column(String)  # organic, direct, social, referral, ads
    source_name = Column(String)  # google, facebook, instagram, etc.
    referrer_url = Column(String)
    utm_source = Column(String)
    utm_medium = Column(String)
    utm_campaign = Column(String)
    visit_count = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Keyword(Base):
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    keyword = Column(String, nullable=False)
    search_engine = Column(String)
    count = Column(Integer, default=1)
    last_seen = Column(DateTime, default=datetime.utcnow)

class ExitLink(Base):
    __tablename__ = "exit_links"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    url = Column(String, nullable=False)
    from_page = Column(String)
    click_count = Column(Integer, default=1)
    last_clicked = Column(DateTime, default=datetime.utcnow)
