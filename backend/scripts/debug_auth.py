import sys
import os
import asyncio

# Ensure backend dir is on sys.path so imports of local modules succeed
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BACKEND_DIR)

from database import get_users_collection
from auth import get_password_hash, authenticate_user


async def main():
    coll = await get_users_collection()
    email = 'debug_auth_test@example.com'
    password = 'DebugAuthPass!'

    # cleanup
    await coll.delete_many({'email': email})

    # insert a new pending user
    await coll.insert_one({
        'email': email,
        'password_hash': get_password_hash(password),
        'full_name': 'Debug Auth',
        'role': 'pending'
    })
    print('Inserted test user')

    # Try correct password
    user = await authenticate_user(email, password)
    print('authenticate_user(correct) ->', bool(user))
    if user:
        print('user.role =', user.role)

    # Try wrong password
    bad = await authenticate_user(email, 'wrongpass')
    print('authenticate_user(wrong) ->', bool(bad))

    # cleanup
    await coll.delete_many({'email': email})
    print('Cleanup done')


if __name__ == '__main__':
    asyncio.run(main())
