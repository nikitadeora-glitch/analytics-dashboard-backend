from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    company_name = Column(String, nullable=True)

    # ✅ Password optional (for Google users)
    hashed_password = Column(String, nullable=True)

    # ✅ Google fields
    google_id = Column(String, nullable=True)
    avatar = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    projects = relationship("Project", back_populates="user")
    password_resets = relationship("PasswordReset", back_populates="user")

class PasswordReset(Base):
    __tablename__ = "password_resets"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    email = Column(String, nullable=False)  # Add email field
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    used_at = Column(DateTime, nullable=True)  # Track when the token was used
    
    user = relationship("User", back_populates="password_resets")

class EmailVerification(Base):
    __tablename__ = "email_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    domain = Column(String, nullable=False)
    tracking_code = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="projects")
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
    
    # UTM tracking fields
    utm_source = Column(String)
    utm_medium = Column(String)
    utm_campaign = Column(String)
    
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

class ExitLinkClick(Base):
    """Track individual exit link clicks"""
    __tablename__ = "exit_link_clicks"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    visitor_id = Column(String, index=True)
    session_id = Column(String, index=True)
    url = Column(String, nullable=False)
    from_page = Column(String)
    clicked_at = Column(DateTime, default=datetime.utcnow, index=True)

class CartAction(Base):
    """Track cart actions (add/remove from cart)"""
    __tablename__ = "cart_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    visit_id = Column(Integer, ForeignKey("visits.id"))
    action = Column(String, nullable=False)  # 'add_to_cart' or 'remove_from_cart'
    product_id = Column(String)
    product_name = Column(String)
    product_url = Column(String)
    page_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    visit = relationship("Visit")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # 'user' or 'ai'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
