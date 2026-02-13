"""
FastAPI application setup with MongoDB integration.
"""
import hashlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .db import connect_to_mongo, close_mongo_connection
from .routes.stores import router as stores_router
from .routes.auth import router as auth_router
from .config import get_settings, ConfigError, ENV_PATH


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    try:
        settings = get_settings()
    except ConfigError:
        raise

    allowed_origins = settings.allowed_origins
    # Initialize rate limiter
    limiter = Limiter(key_func=get_remote_address)
    
    app = FastAPI(
        title="Store Platform API",
        description="API for managing store deployments",
        version="1.0.0"
    )
    
    # Add rate limiter to app state
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth_router)
    app.include_router(stores_router)

    # Database lifecycle events
    @app.on_event("startup")
    async def startup_event():
        """Connect to MongoDB on startup"""
        token_fp = hashlib.sha256(settings.orchestrator_token.encode("utf-8")).hexdigest()[:10] if settings.orchestrator_token else "empty"
        print("🚀 Starting Store Platform API...")
        print(f"🧭 Config env file: {ENV_PATH}")
        print(f"🔐 Orchestrator auth token loaded: len={len(settings.orchestrator_token)} fp={token_fp}")
        await connect_to_mongo()
        print("📡 API endpoints available:")
        print("   - GET /api/stores")
        print("   - POST /api/stores") 
        print("   - DELETE /api/stores/{store_id}")
        print("   - GET /docs (API documentation)")
        print()
        print("💡 Setup Instructions:")
        print("   1. Create MongoDB Atlas account: https://cloud.mongodb.com")
        print("   2. Create a cluster and get connection string")
        print("   3. Create .env file with: MONGODB_URI=mongodb+srv://...")
        print("   4. Add your IP to Atlas Network Access")
        print()

    @app.on_event("shutdown")
    async def shutdown_event():
        """Close MongoDB connection on shutdown"""
        await close_mongo_connection()

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        from .db import db
        db_status = "connected" if db.client else "disconnected"
        return {
            "status": "healthy",
            "database": db_status,
            "message": "MongoDB required for full functionality" if db_status == "disconnected" else "All systems operational"
        }

    # Root endpoint
    @app.get("/")
    async def root():
        return {"message": "Store Platform API", "status": "running"}

    return app


# Create app instance
app = create_app()