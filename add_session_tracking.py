"""
Migration script to add session tracking fields to visits table
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'analytics.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(visits)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Add session_id column if it doesn't exist
        if 'session_id' not in columns:
            print("Adding session_id column...")
            cursor.execute("ALTER TABLE visits ADD COLUMN session_id TEXT")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_visits_session_id ON visits(session_id)")
            print("✓ Added session_id column")
        else:
            print("✓ session_id column already exists")
        
        # Add is_new_session column if it doesn't exist
        if 'is_new_session' not in columns:
            print("Adding is_new_session column...")
            cursor.execute("ALTER TABLE visits ADD COLUMN is_new_session BOOLEAN DEFAULT 1")
            print("✓ Added is_new_session column")
        else:
            print("✓ is_new_session column already exists")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 50)
    print("Session Tracking Migration")
    print("=" * 50)
    migrate()
