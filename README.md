# Backend - State Counter Analytics

Python FastAPI backend for analytics platform.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
python -m uvicorn main:app --reload
```

## API Documentation

Visit http://127.0.0.1:8000/docs for interactive API documentation.

## Cart Action Tracking

Track add to cart and remove from cart actions:

### Frontend Usage

```javascript
// Add to cart tracking
Analytics.trackCartAction('add_to_cart', 'product-123', 'Product Name', '/product/123');

// Remove from cart tracking  
Analytics.trackCartAction('remove_from_cart', 'product-123', 'Product Name', '/product/123');
```

### Parameters
- `action`: 'add_to_cart' or 'remove_from_cart'
- `productId`: Unique product identifier (optional)
- `productName`: Product name (optional)
- `productUrl`: Product page URL (optional)

Cart actions will appear as virtual pages in your analytics dashboard with URLs like:
- `/product/123#cart-add_to_cart-product-123`
- `/product/123#cart-remove_from_cart-product-123`

## Database

SQLite by default. To use PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/analytics_db
```

## Structure

- `main.py` - FastAPI application
- `database.py` - Database configuration
- `models.py` - SQLAlchemy models
- `schemas.py` - Pydantic schemas
- `utils.py` - Helper functions
- `routers/` - API endpoints
