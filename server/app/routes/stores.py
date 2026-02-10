"""
Store management API routes.
"""
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status
from pymongo.errors import PyMongoError

from ..models import StoreCreate, StoreResponse
from ..db import get_stores_collection


router = APIRouter(prefix="/api/stores", tags=["stores"])


@router.get("", response_model=List[StoreResponse])
async def get_stores():
    """
    Get all stores, sorted by creation date (newest first).
    """
    try:
        stores_collection = get_stores_collection()
        cursor = stores_collection.find().sort("created_at", -1)
        stores = []
        
        async for store in cursor:
            # Convert MongoDB _id to id for response
            store["id"] = str(store["_id"])
            del store["_id"]
            stores.append(StoreResponse(**store))
            
        return stores
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please check your Atlas connection and .env configuration."
        )
    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )


@router.post("", response_model=StoreResponse)
async def create_store(store_data: StoreCreate):
    """
    Create a new store with PROVISIONING status.
    """
    try:
        stores_collection = get_stores_collection()
        
        # Generate UUID for store
        store_id = str(uuid.uuid4())
        
        # Create store document
        store_doc = {
            "_id": store_id,
            "name": store_data.name,
            "engine": store_data.engine,
            "status": "PROVISIONING",
            "url": None,
            "error": None,
            "created_at": datetime.utcnow()
        }
        
        # Insert into MongoDB
        await stores_collection.insert_one(store_doc)
        
        # Convert for response
        store_doc["id"] = store_doc["_id"]
        del store_doc["_id"]
        
        return StoreResponse(**store_doc)
    
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please check your Atlas connection and .env configuration."
        )
    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store(store_id: str):
    """
    Mark store for deletion by setting status to DELETING.
    Does not actually remove the document.
    """
    try:
        stores_collection = get_stores_collection()
        
        # Find and update store
        result = await stores_collection.update_one(
            {"_id": store_id},
            {"$set": {"status": "DELETING"}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )
            
        # Return 204 No Content (no response body)
        return
    
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please check your Atlas connection and .env configuration."
        )
    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )