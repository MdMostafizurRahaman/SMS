from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
import os
import ssl
import certifi

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL")
DATABASE_NAME = os.getenv("DATABASE_NAME")

# Global variables
client = None
database = None
users_collection = None

def get_mongodb_url():
    """Ensure MongoDB URL has proper SSL parameters for cloud deployment"""
    # Try different environment variable names that Render might use
    url = (os.getenv("MONGODB_URL") or 
           os.getenv("DATABASE_URL") or 
           os.getenv("MONGO_URL"))
    
    if not url:
        raise ValueError("MONGODB_URL environment variable is not set")
    
    if url and "mongodb+srv://" in url:
        # For SRV connection, ensure we have the right parameters
        if "?" not in url:
            # Add essential SSL parameters for Render deployment
            url += "?ssl=true&retryWrites=true&w=majority&authSource=admin&tlsAllowInvalidCertificates=true&tlsAllowInvalidHostnames=true"
        else:
            # Add missing parameters
            params = []
            if "ssl=true" not in url and "tls=true" not in url:
                params.append("ssl=true")
            if "retryWrites=true" not in url:
                params.append("retryWrites=true")
            if "w=majority" not in url:
                params.append("w=majority")
            if "authSource=" not in url:
                params.append("authSource=admin")
            if params:
                url += "&" + "&".join(params)
    
    return url

async def init_database():
    global client, database, users_collection
    if users_collection is not None:
        return users_collection

    mongodb_url = get_mongodb_url()
    print(f"Connecting to MongoDB: {mongodb_url}")

    try:
        # Use only supported Motor options for SSL/TLS
        client = AsyncIOMotorClient(
            mongodb_url,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            maxIdleTimeMS=60000,
            retryWrites=True,
            w='majority',
            tls=True,
            tlsCAFile=certifi.where(),
            authSource='admin'
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