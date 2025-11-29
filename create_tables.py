"""
Create all database tables in PostgreSQL
Run this script before migrating data
"""
from database import engine, Base
from models import Project, Visit, PageView, Page, TrafficSource, Keyword, ExitLink

def create_all_tables():
    """Create all tables defined in models.py"""
    try:
        print("Creating tables in PostgreSQL...")
        print("-" * 50)
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✓ Tables created successfully!")
        print("-" * 50)
        print("\nCreated tables:")
        print("  1. projects")
        print("  2. visits")
        print("  3. pages")
        print("  4. page_views")
        print("  5. traffic_sources")
        print("  6. keywords")
        print("  7. exit_links")
        print("\n✅ Ready for data migration!")
        
    except Exception as e:
        print(f"✗ Error creating tables: {e}")

if __name__ == "__main__":
    create_all_tables()
