import sys
sys.path.append('.')
from routers.auth import signup
from schemas import UserCreate
from models import User

print('✅ All imports successful')

# Test schema validation
test_data = UserCreate(
    full_name='Test User',
    email='test@example.com',
    company_name=None,
    password='Test123!'
)
print('✅ Schema validation successful')
print(f'✅ Test data: {test_data}')
