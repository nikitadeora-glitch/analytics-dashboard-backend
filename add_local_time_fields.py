"""
Migration script to add local time tracking fields to visits table
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
        
        # Add local_time column if it doesn't exist
        if 'local_time' not in columns:
            print("Adding local_time column...")
            cursor.execute("ALTER TABLE visits ADD COLUMN local_time TEXT")
            print("✓ Added local_time column")
        else:
            print("✓ local_time column already exists")
        
        # Add local_time_formatted column if it doesn't exist
        if 'local_time_formatted' not in columns:
            print("Adding local_time_formatted column...")
            cursor.execute("ALTER TABLE visits ADD COLUMN local_time_formatted TEXT")
            print("✓ Added local_time_formatted column")
        else:
            print("✓ local_time_formatted column already exists")
        
        # Add timezone_offset column if it doesn't exist
        if 'timezone_offset' not in columns:
            print("Adding timezone_offset column...")
            cursor.execute("ALTER TABLE visits ADD COLUMN timezone_offset TEXT")
            print("✓ Added timezone_offset column")
        else:
            print("✓ timezone_offset column already exists")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nNew fields added:")
        print("  - local_time: ISO format timestamp")
        print("  - local_time_formatted: Human-readable format")
        print("  - timezone_offset: UTC offset (e.g., +05:30)")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Local Time Tracking Migration")
    print("=" * 60)
    migrate()
