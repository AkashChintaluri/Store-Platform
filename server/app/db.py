"""
MongoDB database connection and configuration.
"""
import os
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional


class Database:
    client: Optional[AsyncIOMotorClient] = None
    database: Optional[AsyncIOMotorDatabase] = None


db = Database()


async def connect_to_mongo():
    """Create database connection"""
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name = os.getenv("MONGODB_DB", "store_platform")
    
    try:
        # For Atlas, we need longer timeouts
        db.client = AsyncIOMotorClient(
            mongodb_uri, 
            serverSelectionTimeoutMS=10000,  # 10 seconds for Atlas
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        db.database = db.client[database_name]
        
        # Test connection
        await db.client.admin.command('ping')
        print(f"✅ Connected to MongoDB Atlas database: {database_name}")
    except Exception as e:
        print(f"⚠️  MongoDB connection failed: {str(e)}")
        print(f"⚠️  Check your MONGODB_URI in .env file")
        print(f"⚠️  Running without database - API will return errors")
        # Set client to None to indicate no connection
        db.client = None
        db.database = None


async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        print("🔌 Disconnected from MongoDB")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance"""
    if db.database is None:
        raise RuntimeError("MongoDB not connected. Please check your Atlas connection.")
    return db.database


# Collection shortcuts
def get_stores_collection():
    """Get stores collection"""
    if db.database is None:
        raise RuntimeError("MongoDB not connected. Please check your Atlas connection.")
    return db.database.stores


# Future collections (when you add auth)
def get_users_collection():
    """Get users collection"""
    if db.database is None:
        raise RuntimeError("MongoDB not connected. Please check your Atlas connection.")
    return db.database.users


def get_sessions_collection():
    """Get sessions collection"""
    if db.database is None:
        raise RuntimeError("MongoDB not connected. Please check your Atlas connection.")
    return db.database.sessions