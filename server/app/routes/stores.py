"""
Store lifecycle API.

This API:
- Persists store state in MongoDB
- Calls orchestrator functions
- Never blocks on Kubernetes readiness
- Requires authentication for all operations
"""
import asyncio
import os
import uuid
from datetime import datetime
from typing import List
import httpx
from fastapi import APIRouter, HTTPException, status, Depends, Request
from pymongo.errors import PyMongoError
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..models import StoreCreate, StoreResponse, StoreStatusUpdate
from ..db import get_stores_collection, db
from ..orchestrator.provisioner import (
    install_store, 
    delete_store as helm_delete_store, 
    generate_values, 
    configure_platform,
    get_store_url_path
)
from ..orchestrator.status import namespace_ready, get_store_password
from ..middleware import get_current_user, require_orchestrator_token


router = APIRouter(prefix="/api/stores", tags=["stores"])
limiter = Limiter(key_func=get_remote_address)
ORCHESTRATOR_URL = os.getenv("ORCHESTRATOR_URL", "").strip()
ORCHESTRATOR_TOKEN = os.getenv("ORCHESTRATOR_TOKEN", "").strip()


async def check_user_quota(user_id: str):
    """Enforce per-user store limits"""
    # Max 5 stores per user (total)
    total_stores = await db.database.stores.count_documents({"creator_id": user_id})
    if total_stores >= 5:
        raise HTTPException(
            status_code=429,
            detail="Store limit reached. Maximum 5 stores per account."
        )


async def trigger_orchestrator(job: dict):
    """Send store job to external orchestrator if configured."""
    if not ORCHESTRATOR_URL:
        return False
    headers = {"Content-Type": "application/json"}
    if ORCHESTRATOR_TOKEN:
        headers["X-Orchestrator-Token"] = ORCHESTRATOR_TOKEN
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(ORCHESTRATOR_URL, json=job, headers=headers)
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Orchestrator trigger failed: {response.text}"
            )
    return True

@router.get("", response_model=List[StoreResponse])
@limiter.limit("100/minute")  # Higher limit for reads
async def list_stores(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all stores for the authenticated user, sorted by creation date (newest first).
    """
    try:
        stores_collection = get_stores_collection()
        # Filter stores by creator_id to only show user's own stores
        cursor = stores_collection.find({"creator_id": current_user["_id"]}).sort("created_at", -1)
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
@limiter.limit("1/minute")  # 1 store per minute per user/IP
async def create_store(
    request: Request,
    store_data: StoreCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new store for the authenticated user.
    Rate limit: 1 store per minute, max 5 stores per account.
    """
    # Check user quota (max 5 stores)
    await check_user_quota(current_user["_id"])
    
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
            "error": None,
            "creator_id": current_user["_id"],
            "creator_name": current_user["name"]
        }
        
        # Insert into MongoDB
        await stores_collection.insert_one(store_doc)
        orchestrator_payload = {
            "store_id": store_id,
            "name": store_data.name,
            "engine": store_data.engine,
            "namespace": namespace,
            "host": host,
            "base_url": base_url,
            "store_url": store_url,
            "creator_id": current_user["_id"],
        }

        if ORCHESTRATOR_URL:
            try:
                await trigger_orchestrator(orchestrator_payload)
            except Exception as e:
                await stores_collection.update_one(
                    {"_id": store_id},
                    {"$set": {"status": "FAILED", "error": str(e)}}
                )
                raise
        else:
            try:
                values_file = generate_values(store_data.name, host, store_data.engine)
                install_store(store_data.name, namespace, values_file)

                for _ in range(30):
                    pods_ready = await asyncio.to_thread(namespace_ready, namespace)

                    if pods_ready:
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
                            await stores_collection.update_one(
                                {"_id": store_id},
                                {"$set": {"status": "FAILED", "error": platform_error}}
                            )
                            raise HTTPException(
                                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f"Provisioning failed: {platform_error}"
                            )

                    await asyncio.sleep(10)
                else:
                    await stores_collection.update_one(
                        {"_id": store_id},
                        {"$set": {"status": "FAILED", "error": "Platform configuration timed out"}}
                    )

            except Exception as e:
                error_message = str(e)
                await stores_collection.update_one(
                    {"_id": store_id},
                    {"$set": {"status": "FAILED", "error": error_message}}
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Provisioning failed: {error_message}"
                )

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


@router.post("/{store_id}/status")
async def update_store_status(
    store_id: str,
    update: StoreStatusUpdate,
    authorized: bool = Depends(require_orchestrator_token)
):
    """Allow orchestrator to push status updates back to the API."""
    try:
        stores_collection = get_stores_collection()
        store = await stores_collection.find_one({"_id": store_id})
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )

        update_fields = {"status": update.status}
        if update.url is not None:
            update_fields["url"] = update.url
        if update.error is not None:
            update_fields["error"] = update.error
        if update.password is not None:
            update_fields["password"] = update.password

        await stores_collection.update_one({"_id": store_id}, {"$set": update_fields})

        store["id"] = store["_id"]
        del store["_id"]
        return {"ok": True, "store_id": store_id, "status": update.status}

    except RuntimeError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service unavailable. Please check your Atlas connection and .env configuration."
        )
    except PyMongoError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")  # Limit delete operations
async def delete_store_api(
    request: Request,
    store_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a store owned by the authenticated user.
    Rate limit: 10 deletes per minute.
    """
    try:
        stores_collection = get_stores_collection()
        
        # Find store and verify ownership
        store = await stores_collection.find_one({"_id": store_id})
        if not store:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Store not found"
            )
        
        # Verify user owns this store
        if store.get("creator_id") != current_user["_id"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this store"
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