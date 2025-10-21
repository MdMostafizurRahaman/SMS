import os
import random
import string
from fastapi.testclient import TestClient

import sys
sys.path.insert(0, os.path.abspath('..'))

from main import app
from database import get_users_collection


def random_email():
    s = ''.join(random.choice(string.ascii_lowercase) for _ in range(6))
    return f'test_{s}@example.com'


def run_tests():
    client = TestClient(app)

    print('GET /healthz')
    r = client.get('/healthz')
    print(r.status_code, r.json())

    admin_user = os.getenv('ADMIN_EMAIL', 'admin@gmail.com')
    admin_pass = os.getenv('ADMIN_PASSWORD', 'admin123')

    print('\nPOST /token (admin)')
    r = client.post('/token', data={'username': admin_user, 'password': admin_pass})
    print(r.status_code)
    try:
        print(r.json())
    except Exception:
        print('No JSON')

    token = None
    if r.status_code == 200:
        token = r.json().get('access_token')

    # Register a test user
    email = random_email()
    password = 'Password123!'
    print(f'\nPOST /register -> {email}')
    r = client.post('/register', json={'email': email, 'password': password, 'full_name': 'Test User'})
    print(r.status_code)
    try:
        print(r.json())
    except Exception:
        print('No JSON')

    print('\nPOST /token for new user (should be 401 or pending)')
    r2 = client.post('/token', data={'username': email, 'password': password})
    print(r2.status_code)
    try:
        print(r2.json())
    except Exception:
        print('No JSON')

    if token:
        print('\nGET /users/me with admin token')
        r3 = client.get('/users/me', headers={'Authorization': f'Bearer {token}'})
        print(r3.status_code)
        try:
            print(r3.json())
        except Exception:
            print('No JSON')

    # Cleanup: remove test user from DB if created
    try:
        import asyncio
        async def cleanup():
            coll = await get_users_collection()
            await coll.delete_many({'email': {'$regex': '^test_'}})
        asyncio.run(cleanup())
        print('\nCleanup done (deleted test users)')
    except Exception as e:
        print('\nCleanup failed:', e)


if __name__ == '__main__':
    run_tests()
