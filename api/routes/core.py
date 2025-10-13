import os
from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter()


@router.get("/")
async def root():
    """Serve React app or API information."""
    if os.path.exists("frontend/build/index.html"):
        return FileResponse("frontend/build/index.html")
    return {
        "message": "Multi-hop Research Agent API",
        "version": "1.0.0",
        "status": "running",
    }


@router.get("/health")
async def health_check():
    """Minimal health check endpoint."""
    return {"status": "healthy"}



