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
            if "tlsAllowInvalidCertificates=true" not in url:
                params.append("tlsAllowInvalidCertificates=true")
            if "tlsAllowInvalidHostnames=true" not in url:
                params.append("tlsAllowInvalidHostnames=true")
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
        # Create SSL context for MongoDB Atlas connection on Render
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Configuration optimized for cloud deployment platforms like Render
        # SSL settings to resolve TLS handshake issues on Render
        client = AsyncIOMotorClient(
            mongodb_url,
            serverSelectionTimeoutMS=30000,
            connectTimeoutMS=30000,
            socketTimeoutMS=30000,
            maxIdleTimeMS=60000,
            retryWrites=True,
            w='majority',
            # SSL/TLS settings for Render deployment
            tls=True,
            tlsAllowInvalidCertificates=True,
            tlsAllowInvalidHostnames=True,
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
        print(f"Primary MongoDB Atlas connection failed: {e}")
        print("Attempting fallback connection method...")
        
        # Fallback connection with minimal SSL verification
        try:
            fallback_client = AsyncIOMotorClient(
                mongodb_url,
                serverSelectionTimeoutMS=60000,
                connectTimeoutMS=60000,
                socketTimeoutMS=60000,
                ssl=True,
                ssl_cert_reqs=ssl.CERT_NONE,
                ssl_check_hostname=False,
                ssl_ca_certs=None,
                authSource='admin',
                retryWrites=True,
                w='majority'
            )
            
            fallback_database = fallback_client[DATABASE_NAME]
            fallback_users_collection = fallback_database["users"]
            
            # Test fallback connection
            await fallback_client.admin.command('ping')
            print("MongoDB Atlas fallback connection successful")
            
            # Use fallback connection
            client = fallback_client
            database = fallback_database
            users_collection = fallback_users_collection
            
            return users_collection
            
        except Exception as fallback_e:
            print(f"Fallback MongoDB Atlas connection also failed: {fallback_e}")
            print("Please check your MongoDB Atlas cluster is running and accessible")
            raise e

async def get_users_collection():
    return await init_database()