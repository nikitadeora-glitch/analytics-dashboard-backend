from database import engine, get_db
from models import User
from sqlalchemy.orm import sessionmaker
import bcrypt

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Get test user
user = db.query(User).filter(User.email == 'test@example.com').first()
if user:
    print(f'User found: {user.email} (ID: {user.id})')
    print(f'Password hash: {user.hashed_password[:50]}...')
    
    # Test password verification
    test_passwords = ['Test123!', 'test123', 'Test123', 'test123!']
    for pwd in test_passwords:
        try:
            is_valid = bcrypt.checkpw(pwd.encode('utf-8'), user.hashed_password.encode('utf-8'))
            print(f'Password "{pwd}": {"✅ Valid" if is_valid else "❌ Invalid"}')
        except Exception as e:
            print(f'Password "{pwd}": Error - {e}')
else:
    print('Test user not found')

db.close()
