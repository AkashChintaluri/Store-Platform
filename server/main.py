"""
Entry point for running the FastAPI application.
Use: uvicorn main:app --reload
"""
# Import app from the app package
from app.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0", 
        port=8000, 
        reload=True
    )