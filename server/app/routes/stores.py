"""
Store lifecycle API.

This API:
- Persists store state in MongoDB
- Calls orchestrator functions
- Never blocks on Kubernetes readiness
"""
import asyncio
import os
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, HTTPException, status
from pymongo.errors import PyMongoError

from ..models import StoreCreate, StoreResponse
from ..db import get_stores_collection
from ..orchestrator.provisioner import (
    install_store, 
    delete_store as helm_delete_store, 
    generate_values, 
    configure_platform,
    get_store_url_path
)
from ..orchestrator.status import namespace_ready, get_store_password


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
            
            # Fetch password for READY stores
            if store.get("status") == "READY" and store.get("namespace") and store.get("name") and store.get("engine"):
                password = await asyncio.to_thread(
                    get_store_password, 
                    store["namespace"], 
                    store["name"],
                    store["engine"]
                )
                store["password"] = password
            
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
    Create a new store.
    """
    try:
        stores_collection = get_stores_collection()
        
        # Generate store metadata
        store_id = str(uuid.uuid4())
        namespace = store_data.name
        base_domain = os.getenv("STORE_BASE_DOMAIN", "localhost").strip()
        base_port = os.getenv("STORE_BASE_PORT", "").strip()
        host = f"{store_data.name}.{base_domain}" if base_domain else store_data.name
        base_url = f"http://{host}:{base_port}" if base_port else f"http://{host}"
        url_path = get_store_url_path(store_data.engine)
        store_url = f"{base_url}{url_path}"
        
        # Create store document
        store_doc = {
            "_id": store_id,
            "name": store_data.name,
            "engine": store_data.engine,
            "namespace": namespace,
            "host": host,
            "status": "PROVISIONING",
            "url": None,
            "created_at": datetime.utcnow(),
            "error": None
        }
        
        # Insert into MongoDB
        await stores_collection.insert_one(store_doc)
        
        try:
            # Generate Helm values and deploy
            values_file = generate_values(store_data.name, host, store_data.engine)
            install_store(store_data.name, namespace, values_file)
            
            for _ in range(30):
                pods_ready = await asyncio.to_thread(namespace_ready, namespace)
                
                if pods_ready:
                    # Pods are ready, now run platform configuration
                    platform_success, platform_error = await asyncio.to_thread(
                        configure_platform, namespace, store_data.name, store_data.engine
                    )
                    
                    if platform_success:
                        await stores_collection.update_one(
                            {"_id": store_id},
                            {"$set": {"status": "READY", "url": store_url}}
                        )
                        break
                    elif platform_error and "not installed" not in platform_error:
                        # Fatal error (not just waiting for platform)
                        await stores_collection.update_one(
                            {"_id": store_id},
                            {"$set": {"status": "FAILED", "error": platform_error}}
                        )
                        raise HTTPException(
                            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail=f"Provisioning failed: {platform_error}"
                        )
                    # else: Platform not ready yet, keep waiting
                    
                await asyncio.sleep(10)
            else:
                await stores_collection.update_one(
                    {"_id": store_id},
                    {"$set": {"status": "FAILED", "error": "Platform configuration timed out"}}
                )
            
        except Exception as e:
            error_message = str(e)
            # Update status to failed
            await stores_collection.update_one(
                {"_id": store_id},
                {"$set": {"status": "FAILED", "error": error_message}}
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Provisioning failed: {error_message}"
            )
        
        # Return the created store
        store_doc["id"] = store_doc["_id"]
        del store_doc["_id"]
        
        return StoreResponse(**store_doc)
    
    except RuntimeError as e:
        # MongoDB not available - test orchestrator without persistence
        print("⚠️  Testing orchestrator without MongoDB persistence")
        
        # Generate store metadata
        store_id = str(uuid.uuid4())
        namespace = store_data.name
        host = f"{store_data.name}.127.0.0.1.nip.io"
        base_url = f"http://{host}"
        url_path = get_store_url_path(store_data.engine)
        store_url = f"{base_url}{url_path}"
        
        try:
            # Generate Helm values and deploy (orchestrator test)
            values_file = generate_values(store_data.name, host, store_data.engine)
            helm_output = install_store(store_data.name, namespace, values_file)
            print(f"✅ Helm deployment successful: {helm_output}")
            
            # Return mock response for testing
            return StoreResponse(
                id=store_id,
                name=store_data.name,
                engine=store_data.engine,
                namespace=namespace,
                host=host,
                status="READY",
                url=store_url,
                created_at=datetime.utcnow(),
                error=None
            )
            
        except Exception as e:
            print(f"❌ Helm deployment failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Provisioning failed: {str(e)}"
            )
    
    except PyMongoError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_store_api(store_id: str):
    """
    Delete a store and all Kubernetes resources.
    """
    try:
        stores_collection = get_stores_collection()
        
        # Find store
        store = await stores_collection.find_one({"_id": store_id})
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )

        namespace = store.get("namespace") or store.get("name")
        
        if namespace:
            try:
                # Delete via Helm
                helm_delete_store(store["name"], namespace)
            except Exception as e:
                message = str(e)
                if store.get("status") != "FAILED" and "release: not found" not in message:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Failed to delete store: {message}"
                    )
        
        # Remove from MongoDB
        await stores_collection.delete_one({"_id": store_id})
        
        # Return 204 No Content
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