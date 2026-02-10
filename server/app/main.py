"""
FastAPI application setup with MongoDB integration.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import connect_to_mongo, close_mongo_connection
from .routes.stores import router as stores_router


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    app = FastAPI(
        title="Store Platform API",
        description="API for managing store deployments",
        version="1.0.0"
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(stores_router)

    # Database lifecycle events
    @app.on_event("startup")
    async def startup_event():
        """Connect to MongoDB on startup"""
        print("🚀 Starting Store Platform API...")
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