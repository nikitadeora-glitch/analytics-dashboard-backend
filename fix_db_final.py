from database import engine
from sqlalchemy import text

conn = engine.connect()
try:
    # Add google_id column
    conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR"))
    print("✅ google_id column added successfully")
except Exception as e:
    if "already exists" in str(e):
        print("✅ google_id column already exists")
    else:
        print(f"❌ Error adding google_id: {e}")

try:
    # Add avatar column  
    conn.execute(text("ALTER TABLE users ADD COLUMN avatar VARCHAR"))
    print("✅ avatar column added successfully")
except Exception as e:
    if "already exists" in str(e):
        print("✅ avatar column already exists")
    else:
        print(f"❌ Error adding avatar: {e}")

conn.commit()
conn.close()
print("🎉 Database update completed!")
