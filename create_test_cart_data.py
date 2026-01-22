#!/usr/bin/env python3
"""
Create test cart action data for testing the frontend display
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine
import models
from datetime import datetime, timedelta
import random

def create_test_data():
    db = SessionLocal()
    
    try:
        # Check if project exists (assuming project_id = 1)
        project_id = 1
        project = db.query(models.Project).filter(models.Project.id == project_id).first()
        
        if not project:
            print(f"❌ Project with ID {project_id} not found!")
            print("Please create a project first or update the project_id in this script")
            return
        
        print(f"✅ Found project: {project.name}")
        
        # Create test visit
        test_visit = models.Visit(
            project_id=project_id,
            visitor_id="test_visitor_cart_001",
            session_id="test_session_cart_001",
            ip_address="127.0.0.1",
            device="Desktop",
            browser="Chrome",
            os="Windows",
            referrer="direct",
            entry_page="/products",
            visited_at=datetime.utcnow() - timedelta(minutes=30)
        )
        db.add(test_visit)
        db.flush()
        
        print(f"✅ Created test visit with ID: {test_visit.id}")
        
        # Test products
        test_products = [
            {"id": "laptop-001", "name": "Gaming Laptop", "url": "/products/laptop-001"},
            {"id": "mouse-002", "name": "Wireless Mouse", "url": "/products/mouse-002"},
            {"id": "keyboard-003", "name": "Mechanical Keyboard", "url": "/products/keyboard-003"}
        ]
        
        cart_actions_created = 0
        
        for product in test_products:
            # Create add to cart action
            add_action = models.CartAction(
                project_id=project_id,
                visit_id=test_visit.id,
                action="add_to_cart",
                product_id=product["id"],
                product_name=product["name"],
                product_url=product["url"],
                page_url=product["url"],
                created_at=datetime.utcnow() - timedelta(minutes=random.randint(5, 25))
            )
            db.add(add_action)
            
            # Create virtual page for add to cart
            virtual_add_url = f"{product['url']}#cart-add_to_cart-{product['id']}"
            add_page = models.Page(
                project_id=project_id,
                url=virtual_add_url,
                title=f"Cart Action: add_to_cart - {product['name']}",
                total_views=1,
                unique_views=1
            )
            db.add(add_page)
            db.flush()
            
            # Create page view for add to cart
            add_pageview = models.PageView(
                visit_id=test_visit.id,
                page_id=add_page.id,
                url=virtual_add_url,
                title=add_page.title,
                time_spent=0,
                viewed_at=datetime.utcnow() - timedelta(minutes=random.randint(5, 25))
            )
            db.add(add_pageview)
            cart_actions_created += 1
            
            # For some products, also create remove from cart
            if random.choice([True, False]):
                remove_action = models.CartAction(
                    project_id=project_id,
                    visit_id=test_visit.id,
                    action="remove_from_cart",
                    product_id=product["id"],
                    product_name=product["name"],
                    product_url=product["url"],
                    page_url=product["url"],
                    created_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 10))
                )
                db.add(remove_action)
                
                # Create virtual page for remove from cart
                virtual_remove_url = f"{product['url']}#cart-remove_from_cart-{product['id']}"
                remove_page = models.Page(
                    project_id=project_id,
                    url=virtual_remove_url,
                    title=f"Cart Action: remove_from_cart - {product['name']}",
                    total_views=1,
                    unique_views=1
                )
                db.add(remove_page)
                db.flush()
                
                # Create page view for remove from cart
                remove_pageview = models.PageView(
                    visit_id=test_visit.id,
                    page_id=remove_page.id,
                    url=virtual_remove_url,
                    title=remove_page.title,
                    time_spent=0,
                    viewed_at=datetime.utcnow() - timedelta(minutes=random.randint(1, 10))
                )
                db.add(remove_pageview)
                cart_actions_created += 1
        
        db.commit()
        print(f"✅ Created {cart_actions_created} cart actions with corresponding pages and page views")
        print(f"🎉 Test data creation completed!")
        print(f"📊 You should now see cart actions in your Pages dashboard")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Creating test cart action data...")
    create_test_data()