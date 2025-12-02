"""
Migration script to add exit_link_clicks table for individual click tracking
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./analytics.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
Base = declarative_base()

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

def migrate():
    print("Creating exit_link_clicks table...")
    try:
        Base.metadata.create_all(bind=engine, tables=[ExitLinkClick.__table__])
        print("✅ Table created successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    migrate()
