from database import SessionLocal
from models import Visit, PageView

db = SessionLocal()

# Check total counts
total_visits = db.query(Visit).count()
total_page_views = db.query(PageView).count()

print(f'Total visits: {total_visits}')
print(f'Total page views: {total_page_views}')

# Check some sample visits
visits = db.query(Visit).limit(5).all()
for v in visits:
    page_count = len(v.page_views)
    print(f'Visit {v.id}: Visitor {v.visitor_id}, Session {v.session_id}, Pages: {page_count}')
    if page_count > 0:
        for pv in v.page_views:
            print(f'  - {pv.url} (time: {pv.time_spent}s)')

db.close()