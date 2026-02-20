"""
Create sample data for testing
"""
from database import SessionLocal, engine, Base
import models
from datetime import datetime, timedelta
import random

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Create sample project if not exists
project = db.query(models.Project).first()
if not project:
    project = models.Project(
        name="Demo Website",
        domain="demo.example.com",
        tracking_code="demo_tracking_123"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    print(f"✓ Created project: {project.name}")
else:
    print(f"✓ Using existing project: {project.name}")

# Create sample visits
countries = ["United States", "India", "United Kingdom", "Canada", "Germany"]
states = ["California", "Maharashtra", "London", "Ontario", "Bavaria"]
cities = ["San Francisco", "Mumbai", "London", "Toronto", "Munich"]
devices = ["Desktop", "Mobile", "Tablet"]
browsers = ["Chrome", "Firefox", "Safari", "Edge"]
referrers = ["google.com", "facebook.com", "twitter.com", "direct", "instagram.com"]
utm_sources = ["instagram", "facebook", "google", "twitter", None, "email", "referral"]
utm_mediums = ["social", "organic", "cpc", "email", None, "referral"]
utm_campaigns = ["summer_sale", "new_launch", "newsletter", None, "promo_2026"]

print("\nCreating sample visits...")
for i in range(50):
    visit = models.Visit(
        project_id=project.id,
        visitor_id=f"visitor_{i}",
        session_id=f"session_{i}_{random.randint(1000, 9999)}",
        ip_address=f"192.168.1.{i}",
        country=random.choice(countries),
        state=random.choice(states),
        city=random.choice(cities),
        latitude=random.uniform(-90, 90),
        longitude=random.uniform(-180, 180),
        device=random.choice(devices),
        browser=random.choice(browsers),
        os="Windows 10",
        referrer=random.choice(referrers),
        entry_page=f"/page-{random.randint(1, 5)}",
        exit_page=f"/page-{random.randint(1, 5)}",
        session_duration=random.randint(30, 600),
        visited_at=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
        is_unique=random.choice([True, False]),
        # Add UTM fields
        utm_source=random.choice(utm_sources),
        utm_medium=random.choice(utm_mediums),
        utm_campaign=random.choice(utm_campaigns)
    )
    db.add(visit)

db.commit()
print(f"✓ Created 50 sample visits")

# Create sample page views for each visit
print("\nCreating sample page views...")
all_visits = db.query(models.Visit).filter(models.Visit.project_id == project.id).all()
page_urls = ["/", "/about", "/products", "/contact", "/blog", "/pricing", "/features"]
page_titles = ["Home", "About Us", "Products", "Contact", "Blog", "Pricing", "Features"]

pageview_count = 0
for visit in all_visits:
    # Each visit has 2-5 page views
    num_pages = random.randint(2, 5)
    visit_time = visit.visited_at
    
    for i in range(num_pages):
        page_idx = random.randint(0, len(page_urls) - 1)
        time_spent = random.randint(10, 180)  # 10 seconds to 3 minutes
        
        pageview = models.PageView(
            visit_id=visit.id,
            url=page_urls[page_idx],
            title=page_titles[page_idx],
            time_spent=time_spent,
            scroll_depth=random.randint(20, 100),
            viewed_at=visit_time + timedelta(seconds=i * 30)  # Each page 30 seconds apart
        )
        db.add(pageview)
        pageview_count += 1

db.commit()
print(f"✓ Created {pageview_count} sample page views")

# Create sample pages
print("\nCreating sample pages...")
pages_data = [
    ("/", "Home Page"),
    ("/about", "About Us"),
    ("/products", "Products"),
    ("/contact", "Contact"),
    ("/blog", "Blog")
]

for url, title in pages_data:
    page = models.Page(
        project_id=project.id,
        url=url,
        title=title,
        total_views=random.randint(100, 1000),
        unique_views=random.randint(50, 500),
        avg_time_spent=random.uniform(30, 300),
        bounce_rate=random.uniform(20, 80)
    )
    db.add(page)

db.commit()
print(f"✓ Created {len(pages_data)} sample pages")

# Create sample traffic sources
print("\nCreating sample traffic sources...")
sources = [
    ("organic", "Google"),
    ("social", "Facebook"),
    ("social", "Instagram"),
    ("direct", "Direct"),
    ("referral", "example.com")
]

for source_type, source_name in sources:
    traffic = models.TrafficSource(
        project_id=project.id,
        source_type=source_type,
        source_name=source_name,
        visit_count=random.randint(10, 200)
    )
    db.add(traffic)

db.commit()
print(f"✓ Created {len(sources)} traffic sources")

# Create sample keywords
print("\nCreating sample keywords...")
keywords = ["analytics", "tracking", "website stats", "visitor tracking", "real-time analytics"]

for keyword in keywords:
    kw = models.Keyword(
        project_id=project.id,
        keyword=keyword,
        search_engine="Google",
        count=random.randint(5, 50)
    )
    db.add(kw)

db.commit()
print(f"✓ Created {len(keywords)} keywords")

# Store project info before closing session
project_id = project.id
project_name = project.name
tracking_code = project.tracking_code

db.close()

print("\n" + "="*50)
print("✓ Sample data created successfully!")
print("="*50)
print(f"\nProject ID: {project_id}")
print(f"Project Name: {project_name}")
print(f"Tracking Code: {tracking_code}")
print("\nYou can now view the dashboard with sample data!")
