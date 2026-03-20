# Test directory for analytics dashboard backend

This directory contains pytest test files for the backend API.

## Running Tests

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run all tests
pytest

# Run specific test file
pytest test/test_basic.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=.
```

## Test Structure

- `test_basic.py` - Basic configuration and database connection tests
- Add more test files as needed following the `test_*.py` pattern
