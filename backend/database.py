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

        # Increase timeout and add SSL configuration for MongoDB Atlas
        client = AsyncIOMotorClient(
            MONGODB_URL,
            serverSelectionTimeoutMS=30000,  # 30 seconds
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            maxIdleTimeMS=30000,
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True
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