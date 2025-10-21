import sys, os, asyncio
# Ensure backend package dir is on sys.path regardless of current working directory
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BACKEND_DIR)

from database import get_users_collection
from auth import authenticate_user


async def main():
    coll = await get_users_collection()
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@gmail.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'BigBangAdmin2025!')
    admin = await coll.find_one({'email': admin_email})
    if not admin:
        print('Admin not found in DB')
        return
    print('Admin found, role=', admin.get('role'))

    user = await authenticate_user(admin_email, admin_password)
    print('authenticate_user(admin) returned:', bool(user))

if __name__ == '__main__':
    asyncio.run(main())
