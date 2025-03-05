"""
Health check endpoints for API status monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging
import os

from app.db.database import get_db, engine
from app.auth.security import JWT_SECRET_KEY

logger = logging.getLogger("job_tracker.api.health")

router = APIRouter()

@router.get("/health")
async def health_check():
    """Simple health check endpoint to verify API is up and running"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "api_version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check that verifies database connection and configuration"""
    health_info = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "api_version": "1.0.0",
        "components": {
            "database": {
                "status": "unknown",
                "connection_string": "****" # Masked for security
            },
            "auth": {
                "status": "configured",
                "jwt_secret": "configured" if JWT_SECRET_KEY != "temporary_secret_key_replace_in_production" else "warning: using default"
            },
            "environment": os.environ.get("ENVIRONMENT", "development")
        }
    }
    
    # Check database connection
    try:
        # Execute a simple query to verify connection
        db.execute("SELECT 1")
        health_info["components"]["database"]["status"] = "connected"
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        health_info["status"] = "warning"
        health_info["components"]["database"]["status"] = "error"
        health_info["components"]["database"]["error"] = str(e)
    
    return health_info
