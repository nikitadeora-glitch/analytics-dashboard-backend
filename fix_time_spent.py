"""
Fix time_spent for existing page views by calculating from timestamps
"""
import sqlite3
from datetime import datetime

def fix_time_spent():
    # Connect to SQLite database
    conn = sqlite3.connect('analytics.db')
    cursor = conn.cursor()
    
    try:
        # Get all visits
        cursor.execute("SELECT id, visited_at, session_duration FROM visits")
        visits = cursor.fetchall()
        
        print(f"Processing {len(visits)} visits...")
        
        for visit in visits:
            visit_id, visited_at_str, session_duration = visit
            
            # Get all page views for this visit, ordered by time
            cursor.execute("""
                SELECT id, url, viewed_at, time_spent 
                FROM page_views 
                WHERE visit_id = ? 
                ORDER BY viewed_at
            """, (visit_id,))
            page_views = cursor.fetchall()
            
            if len(page_views) == 0:
                continue
            
            print(f"\nVisit {visit_id}: {len(page_views)} page views")
            
            # Calculate time spent for each page
            for i, pv in enumerate(page_views):
                pv_id, url, viewed_at_str, old_time = pv
                viewed_at = datetime.fromisoformat(viewed_at_str.replace('Z', '+00:00'))
                
                if i < len(page_views) - 1:
                    # Time spent = next page time - current page time
                    next_viewed_at = datetime.fromisoformat(page_views[i + 1][2].replace('Z', '+00:00'))
                    time_diff = (next_viewed_at - viewed_at).total_seconds()
                    
                    # Cap at 30 minutes (1800 seconds) to avoid unrealistic values
                    time_spent = min(int(time_diff), 1800)
                else:
                    # Last page: use session duration or default to 30 seconds
                    if session_duration and session_duration > 0:
                        # Calculate time from last page view to session end
                        visit_start = datetime.fromisoformat(visited_at_str.replace('Z', '+00:00'))
                        session_end = visit_start.timestamp() + session_duration
                        last_page_time = viewed_at.timestamp()
                        time_spent = min(int(session_end - last_page_time), 1800)
                    else:
                        # Default to 30 seconds for last page
                        time_spent = 30
                
                # Update if changed
                if old_time != time_spent:
                    cursor.execute("""
                        UPDATE page_views 
                        SET time_spent = ? 
                        WHERE id = ?
                    """, (time_spent, pv_id))
                    print(f"  Page {i+1}: {url[:50]}... | {old_time}s → {time_spent}s")
            
            conn.commit()
        
        print("\n✅ Done! Time spent values updated.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_time_spent()
