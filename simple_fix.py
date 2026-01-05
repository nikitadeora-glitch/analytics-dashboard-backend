from database import engine

conn = engine.connect()
try:
    conn.execute("ALTER TABLE users ADD COLUMN google_id VARCHAR")
    print("google_id added")
except:
    print("google_id already exists")

try:
    conn.execute("ALTER TABLE users ADD COLUMN avatar VARCHAR")
    print("avatar added") 
except:
    print("avatar already exists")

conn.commit()
conn.close()
print("Done!")
