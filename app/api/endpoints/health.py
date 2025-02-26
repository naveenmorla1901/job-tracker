"""
Health check endpoint for API status monitoring
"""
from fastapi import APIRouter
from datetime import datetime
import logging

logger = logging.getLogger("job_tracker.api.health")

router = APIRouter()

@router.get("/")
def health_check():
    """Simple health check endpoint to verify API is up and running"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "api_version": "1.0.0"
    }
