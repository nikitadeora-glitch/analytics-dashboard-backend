import requests
import json

# Test login first
login_data = {
    'email': 'nikita.deora@prpwebs.in',  # Existing user with projects
    'password': 'Test123!'
}

print("=== Testing Login ===")
try:
    response = requests.post(
        'http://localhost:8000/api/auth/login',
        json=login_data,
        headers={'Content-Type': 'application/json'}
    )
    print(f'Login Status: {response.status_code}')
    
    if response.status_code == 200:
        token_data = response.json()
        access_token = token_data.get('access_token')
        print(f'Got token: {access_token[:50]}...')
        
        # Test projects API with token
        print("\n=== Testing Projects API ===")
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        projects_response = requests.get(
            'http://localhost:8000/api/projects/stats/all',
            headers=headers
        )
        print(f'Projects Status: {projects_response.status_code}')
        print(f'Projects Response: {projects_response.text[:200]}...')
        
    else:
        print(f'Login failed: {response.text}')
        
except Exception as e:
    print(f'Exception: {e}')
