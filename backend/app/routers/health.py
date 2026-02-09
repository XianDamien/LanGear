"""Health check router."""

from datetime import datetime

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    """Health check endpoint.

    Returns:
        Service status and timestamp
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
