"""
Add new fields to visits table: screen_resolution, language, timezone, isp
Run this script to update the database schema
"""

from sqlalchemy import create_engine, text
from database import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SQL commands to add new columns (SQLite compatible)
sql_commands = [
    "ALTER TABLE visits ADD COLUMN screen_resolution VARCHAR",
    "ALTER TABLE visits ADD COLUMN language VARCHAR",
    "ALTER TABLE visits ADD COLUMN timezone VARCHAR",
    "ALTER TABLE visits ADD COLUMN isp VARCHAR"
]

print("Adding new columns to visits table...")

with engine.connect() as conn:
    for sql in sql_commands:
        try:
            conn.execute(text(sql))
            conn.commit()
            print(f"✓ Executed: {sql}")
        except Exception as e:
            # Column might already exist, that's okay
            if "duplicate column name" in str(e).lower():
                print(f"⚠ Column already exists (skipping): {sql}")
            else:
                print(f"✗ Error: {e}")

print("\n✅ Database migration completed!")
print("New fields added: screen_resolution, language, timezone, isp")
