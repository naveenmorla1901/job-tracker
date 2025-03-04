"""
Main FastAPI application
"""
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import logging
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("job_tracker.log")
    ]
)
logger = logging.getLogger("job_tracker")

from app.db.database import get_db, engine
from app.db.models import Base, Job, Role
from app.api.endpoints.jobs import router as jobs_router
from app.api.endpoints.stats import router as stats_router
from app.api.endpoints.health import router as health_router
from app.api.endpoints.auth.routes import router as auth_router
from app.api.endpoints.user_jobs import router as user_jobs_router
from app.config import ENVIRONMENT

# Get environment for conditional logic
is_test = ENVIRONMENT == "test"

# Create database tables - only if not in test environment
# (tests will create their own tables)
if not is_test:
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Import only if not in test to prevent circular imports
    from app.scheduler.jobs import setup_scheduler
else:
    logger.info("Test environment detected, skipping database initialization")

# Initialize FastAPI app
app = FastAPI(
    title="Job Tracker API",
    description="API for tracking job postings from various companies",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers
app.include_router(jobs_router, prefix="/api/jobs", tags=["jobs"])
app.include_router(stats_router, prefix="/api/stats", tags=["stats"])
app.include_router(health_router, prefix="/api", tags=["health"])
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(user_jobs_router, prefix="/api/user/jobs", tags=["user-jobs"])

@app.on_event("startup")
async def startup_event():
    """Start the scheduler and purge old records when the application starts"""
    # Skip startup tasks in test environment
    if is_test:
        logger.info("Test environment: skipping startup tasks")
        return
        
    logger.info("="*80)
    logger.info("STARTING JOB TRACKER API")
    logger.info("="*80)
    
    # First purge old records
    try:
        from purge_old_records import purge_old_records
        import threading
        
        logger.info("Starting initial database cleanup...")
        
        # Run initial purge in a separate thread
        def purge_thread():
            try:
                removed_count = purge_old_records(days=7)
                logger.info(f"Initial cleanup complete: {removed_count} old records removed")
            except Exception as e:
                logger.error(f"Error during initial cleanup: {str(e)}")
        
        thread = threading.Thread(target=purge_thread)
        thread.daemon = True
        thread.start()
        
        # Start the scheduled cleanup process
        from scheduled_cleanup import start_scheduled_cleanup_thread
        cleanup_thread = start_scheduled_cleanup_thread()
        
        logger.info("Scheduled cleanup service started successfully")
    except Exception as e:
        logger.error(f"Warning: Could not set up scheduled cleanup: {str(e)}")
    
    # Get database statistics
    try:
        db = next(get_db())
        active_jobs = db.query(Job).filter(Job.is_active == True).count()
        total_jobs = db.query(Job).count()
        companies = db.query(Job.company).distinct().count()
        roles = db.query(Role).count()
        
        logger.info("-"*50)
        logger.info("Database Statistics:")
        logger.info(f"Active Jobs: {active_jobs}")
        logger.info(f"Total Jobs: {total_jobs}")
        logger.info(f"Companies: {companies}")
        logger.info(f"Roles: {roles}")
        logger.info("-"*50)
        
        db.close()
    except Exception as e:
        logger.error(f"Error getting database statistics: {str(e)}")
    
    # Then start the scheduler
    logger.info("Initializing job scraper scheduler...")
    from app.scheduler.jobs import setup_scheduler
    setup_scheduler()
    logger.info("Startup complete!")

@app.get("/")
def read_root():
    """Root endpoint for the API"""
    return {
        "message": "Welcome to the Job Tracker API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "status": "ok"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
