"""
Script to clear old visit data and start fresh
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'analytics.db')

def clear_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("Clearing Old Data")
        print("=" * 60)
        
        # Count existing data
        cursor.execute("SELECT COUNT(*) FROM visits")
        visit_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM page_views")
        pageview_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM traffic_sources")
        traffic_count = cursor.fetchone()[0]
        
        print(f"\nCurrent data:")
        print(f"  - Visits: {visit_count}")
        print(f"  - Page Views: {pageview_count}")
        print(f"  - Traffic Sources: {traffic_count}")
        
        if visit_count == 0:
            print("\n✅ Database is already empty!")
            return
        
        # Confirm deletion
        print("\n⚠️  This will DELETE ALL visit data!")
        print("Projects will remain intact.")
        
        # Delete data
        print("\nDeleting data...")
        cursor.execute("DELETE FROM page_views")
        print("  ✓ Cleared page_views")
        
        cursor.execute("DELETE FROM visits")
        print("  ✓ Cleared visits")
        
        cursor.execute("DELETE FROM traffic_sources")
        print("  ✓ Cleared traffic_sources")
        
        # Reset auto-increment counters (if table exists)
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='visits'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='page_views'")
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='traffic_sources'")
            print("  ✓ Reset ID counters")
        except:
            print("  ⚠ ID counters not reset (table doesn't exist)")
        
        conn.commit()
        
        print("\n" + "=" * 60)
        print("✅ All old data cleared successfully!")
        print("=" * 60)
        print("\nYou can now generate fresh visits with local time tracking.")
        print("Use: test-new-visit.html or test-live.html")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    clear_data()