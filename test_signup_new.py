import requests

# Test with different email
test_data = {
    'full_name': 'New Test User',
    'email': 'newuser@example.com', 
    'company_name': None,
    'password': 'Test123!'
}

try:
    response = requests.post(
        'http://localhost:8000/api/auth/signup',
        json=test_data,
        headers={'Content-Type': 'application/json'}
    )
    print(f'Status: {response.status_code}')
    print(f'Response: {response.text}')
    
    if response.status_code == 400:
        print("❌ 400 Error - Check email or password")
    elif response.status_code == 200:
        print("✅ Success - Account created")
        
except Exception as e:
    print(f'❌ Exception: {e}')
