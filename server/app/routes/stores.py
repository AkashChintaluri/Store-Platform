"""
Store lifecycle API.

This API:
- Persists store state in MongoDB
- Calls orchestrator functions
- Never blocks on Kubernetes readiness
- Requires authentication for all operations
"""
import uuid
import hashlib
from datetime import datetime
from typing import List
import httpx
from fastapi import APIRouter, HTTPException, status, Depends, Request
from pymongo.errors import PyMongoError
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..models import StoreCreate, StoreResponse, StoreStatusUpdate
from ..db import get_stores_collection, db
from ..middleware import get_current_user, require_orchestrator_token
from ..config import get_settings


router = APIRouter(prefix="/api/stores", tags=["stores"])
limiter = Limiter(key_func=get_remote_address)


def _token_fingerprint(value: str | None) -> str:
    if not value:
        return "empty"
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]


def _url_path_for_engine(engine: str) -> str:
    return "/shop/" if engine == "woocommerce" else "/"


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
    settings = get_settings()
    if not settings.orchestrator_url:
        return False
    if not settings.orchestrator_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ORCHESTRATOR_TOKEN is not configured in backend runtime environment"
        )
    headers = {"Content-Type": "application/json"}
    headers["X-Orchestrator-Token"] = settings.orchestrator_token
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(settings.orchestrator_url, json=job, headers=headers)
        if response.status_code >= 400:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=(
                    "Orchestrator trigger failed: "
                    f"status={response.status_code}, response={response.text}, "
                    f"token_fp={_token_fingerprint(settings.orchestrator_token)}"
                )
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
        settings = get_settings()
        base_domain = settings.store_base_domain
        base_port = settings.store_base_port
        host = f"{store_data.name}.{base_domain}" if base_domain else store_data.name
        base_url = f"http://{host}:{base_port}" if base_port else f"http://{host}"
        url_path = _url_path_for_engine(store_data.engine)
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

        if settings.orchestrator_url:
            try:
                await trigger_orchestrator(orchestrator_payload)
            except Exception as e:
                await stores_collection.update_one(
                    {"_id": store_id},
                    {"$set": {"status": "FAILED", "error": str(e)}}
                )
                raise
        else:
            await stores_collection.update_one(
                {"_id": store_id},
                {"$set": {"status": "FAILED", "error": "ORCHESTRATOR_URL not configured"}}
            )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="ORCHESTRATOR_URL not configured; please run orchestrator service and set environment variable."
            )

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