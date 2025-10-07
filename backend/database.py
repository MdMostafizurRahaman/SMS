from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# Global variables
client = None
database = None
users_collection = None

async def init_database():
    global client, database, users_collection
    if users_collection is not None:
        return users_collection
    try:
        print(f"Connecting to MongoDB: {MONGODB_URL}")

        # Configuration optimized for cloud deployment platforms like Render
        client = AsyncIOMotorClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=5000,  # Reduced timeout
            connectTimeoutMS=10000,
            socketTimeoutMS=20000,
            maxIdleTimeMS=45000,
            retryWrites=True,
            w='majority'
        )
        database = client[DATABASE_NAME]
        users_collection = database["users"]
        # Test the connection
        await client.admin.command('ping')
        print("MongoDB Atlas connection successful")
        return users_collection
    except Exception as e:
        print(f"MongoDB Atlas connection failed: {e}")
        print("Please check your MongoDB Atlas cluster is running and accessible")
        raise e

async def get_users_collection():
    return await init_database()