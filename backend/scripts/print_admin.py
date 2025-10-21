import asyncio
from database import get_users_collection

async def main():
    coll = await get_users_collection()
    admin = await coll.find_one({'email': 'admin@gmail.com'})
    if not admin:
        print('Admin not found')
        return
    # print relevant fields
    print('Admin found:')
    print('email:', admin.get('email'))
    print('full_name:', admin.get('full_name'))
    print('role:', admin.get('role'))
    print('password_hash:', admin.get('password_hash')[:60] if admin.get('password_hash') else None)

asyncio.run(main())
