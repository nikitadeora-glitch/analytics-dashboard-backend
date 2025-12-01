"""
Migrate data from SQLite to PostgreSQL
Run this script AFTER both databases are configured
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Project, Visit, PageView, Page, TrafficSource, Keyword, ExitLink

# SQLite connection
sqlite_engine = create_engine('sqlite:///./analytics.db')
SQLiteSession = sessionmaker(bind=sqlite_engine)

# PostgreSQL connection  
postgres_url = os.getenv("DATABASE_URL", "postgresql://postgres:mypassword@localhost:5432/analytics_db")
postgres_engine = create_engine(postgres_url)
PostgresSession = sessionmaker(bind=postgres_engine)

def migrate_table(model_class, sqlite_session, postgres_session):
    """Migrate a single table from SQLite to PostgreSQL"""
    try:
        # Fetch all records from SQLite
        records = sqlite_session.query(model_class).all()
        
        if not records:
            print(f"✓ No data to migrate for {model_class.__tablename__}")
            return
        
        # Add to PostgreSQL
        for record in records:
            # Create new object without id (let PostgreSQL auto-generate)
            record_dict = {c.name: getattr(record, c.name) 
                          for c in record.__table__.columns 
                          if c.name != 'id'}
            
            new_record = model_class(**record_dict)
            postgres_session.add(new_record)
        
        postgres_session.commit()
        print(f"✓ Migrated {len(records)} records from {model_class.__tablename__}")
        
    except Exception as e:
        print(f"✗ Error migrating {model_class.__tablename__}: {e}")
        postgres_session.rollback()

def main():
    print("Starting migration from SQLite to PostgreSQL...")
    print("-" * 50)
    
    # Create sessions
    sqlite_session = SQLiteSession()
    postgres_session = PostgresSession()
    
    try:
        # Migrate in order (respecting foreign key constraints)
        migrate_table(Project, sqlite_session, postgres_session)
        migrate_table(Visit, sqlite_session, postgres_session)
        migrate_table(Page, sqlite_session, postgres_session)
        migrate_table(PageView, sqlite_session, postgres_session)
        migrate_table(TrafficSource, sqlite_session, postgres_session)
        migrate_table(Keyword, sqlite_session, postgres_session)
        migrate_table(ExitLink, sqlite_session, postgres_session)
        
        print("-" * 50)
        print("✓ Migration completed successfully!")
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
    finally:
        sqlite_session.close()
        postgres_session.close()

if __name__ == "__main__":
    main()
