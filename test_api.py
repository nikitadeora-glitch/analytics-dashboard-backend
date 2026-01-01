import requests
import json

try:
    response = requests.post(
        'http://localhost:8000/api/auth/signup',
        json={
            'full_name': 'Test User',
            'email': 'test@example.com', 
            'company_name': None,
            'password': 'Test123!'
        },
        headers={'Content-Type': 'application/json'}
    )
    print(f'Status Code: {response.status_code}')
    print(f'Response: {response.text}')
    
    if response.status_code == 200:
        data = response.json()
        print(f'✅ Success! Tokens: {data.get("access_token", "NOT_FOUND")}')
    else:
        print(f'❌ Error: {response.status_code}')
        
except Exception as e:
    print(f'❌ Exception: {e}')
