import psycopg2
from database import engine

def fix_database():
    try:
        # Connect to database
        conn = engine.connect()
        
        # Add google_id column
        try:
            conn.execute(psycopg2.sql.SQL("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_id VARCHAR"))
            print("✅ google_id column added")
        except Exception as e:
            print(f"google_id column error: {e}")
        
        # Add avatar column
        try:
            conn.execute(psycopg2.sql.SQL("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar VARCHAR"))
            print("✅ avatar column added")
        except Exception as e:
            print(f"avatar column error: {e}")
        
        # Add is_verified column
        try:
            conn.execute(psycopg2.sql.SQL("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE"))
            print("✅ is_verified column added")
        except Exception as e:
            print(f"is_verified column error: {e}")
        
        # Add updated_at column
        try:
            conn.execute(psycopg2.sql.SQL("ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
            print("✅ updated_at column added")
        except Exception as e:
            print(f"updated_at column error: {e}")
        
        conn.commit()
        conn.close()
        print("🎉 Database schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Database update failed: {e}")

if __name__ == "__main__":
    fix_database()
