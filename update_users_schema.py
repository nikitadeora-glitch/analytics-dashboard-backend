from sqlalchemy import text
from database import engine

def update_users_table():
    with engine.connect() as conn:
        with conn.begin():
            # Add missing columns to users table (SQLite syntax)
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN company_name VARCHAR"))
            except Exception as e:
                print(f"company_name column might already exist: {e}")
            
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR"))
            except Exception as e:
                print(f"google_id column might already exist: {e}")
            
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN avatar VARCHAR"))
            except Exception as e:
                print(f"avatar column might already exist: {e}")
            
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE"))
            except Exception as e:
                print(f"is_verified column might already exist: {e}")
            
            try:
                conn.execute(text("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"))
            except Exception as e:
                print(f"updated_at column might already exist: {e}")

if __name__ == "__main__":
    print("Updating users table...")
    update_users_table()
    print("Users table schema updated successfully!")
