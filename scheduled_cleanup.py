"""
Scheduled cleanup process for the Job Tracker application.
This script sets up automatic purging of old job records every morning and evening.
"""
import schedule
import time
import logging
import os
import sys
import threading
from datetime import datetime

# Configure logging
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("cleanup_log.txt"),
            logging.StreamHandler()
        ]
    )

logger = logging.getLogger('job_tracker.cleanup')

def run_purge():
    """Run the purge_old_records function"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Starting scheduled cleanup process at {current_time}")
    
    try:
        # Import the purge function directly to avoid circular imports
        from purge_old_records import purge_old_records
        
        # Run the purge with 7 days as the cutoff
        removed_count = purge_old_records(days=7)
        
        logger.info(f"Scheduled cleanup completed: {removed_count} jobs removed")
        
        # Log current database stats after cleanup
        try:
            from sqlalchemy.orm import Session
            from app.db.database import get_db
            from app.db.models import Job, Role
            
            db = next(get_db())
            active_jobs = db.query(Job).filter(Job.is_active == True).count()
            total_jobs = db.query(Job).count()
            companies = db.query(Job.company).distinct().count()
            roles = db.query(Role).count()
            
            logger.info("-"*50)
            logger.info("Database Statistics After Cleanup:")
            logger.info(f"Active Jobs: {active_jobs}")
            logger.info(f"Total Jobs: {total_jobs}")
            logger.info(f"Companies: {companies}")
            logger.info(f"Roles: {roles}")
            logger.info("-"*50)
            
            db.close()
        except Exception as e:
            logger.error(f"Error getting database statistics: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error during scheduled cleanup: {str(e)}")

def start_scheduled_cleanup():
    """Set up the scheduled cleanup jobs"""
    # Schedule two daily runs
    schedule.every().day.at("06:00").do(run_purge)  # Morning cleanup at 6 AM
    schedule.every().day.at("18:00").do(run_purge)  # Evening cleanup at 6 PM
    
    logger.info("Scheduled cleanup jobs set for 06:00 and 18:00 daily")
    
    # Run immediately on first start
    logger.info("Running initial cleanup...")
    run_purge()
    
    # Keep the scheduler running
    logger.info("Cleanup scheduler now running in background")
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def start_scheduled_cleanup_thread():
    """Start the scheduled cleanup in a background thread"""
    cleanup_thread = threading.Thread(target=start_scheduled_cleanup, daemon=True)
    cleanup_thread.start()
    logger.info("Cleanup thread started successfully")
    return cleanup_thread

if __name__ == "__main__":
    # When run directly, start the scheduler in the foreground
    logger.info("="*50)
    logger.info("STARTING CLEANUP SCHEDULER")
    logger.info("="*50)
    try:
        start_scheduled_cleanup()
    except KeyboardInterrupt:
        logger.info("Cleanup scheduler stopped by user")
        sys.exit(0)
