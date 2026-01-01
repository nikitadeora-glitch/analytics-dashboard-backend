from database import SessionLocal
from models import Visit, PageView, User, Project

db = SessionLocal()

# Check users
print("=== USERS ===")
users = db.query(User).all()
print(f"Total users: {len(users)}")
for user in users:
    print(f"User {user.id}: {user.email} - {user.full_name}")

print("\n=== PROJECTS ===")
projects = db.query(Project).all()
print(f"Total projects: {len(projects)}")
for project in projects:
    print(f"Project {project.id}: {project.name} (User: {project.user_id})")

print("\n=== VISITS ===")
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