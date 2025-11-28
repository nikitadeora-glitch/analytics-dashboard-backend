import sqlite3

conn = sqlite3.connect('analytics.db')
cursor = conn.cursor()

print("=" * 60)
print("Traffic Sources in Database:")
print("=" * 60)

cursor.execute('SELECT source_type, source_name, visit_count FROM traffic_sources ORDER BY visit_count DESC')
rows = cursor.fetchall()

if rows:
    for row in rows:
        print(f"  {row[0]:10} | {row[1]:20} | {row[2]} visits")
    print(f"\nTotal: {len(rows)} traffic sources")
else:
    print("  No traffic sources found!")

conn.close()
