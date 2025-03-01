"""
Scheduled cleanup for job tracker system
"""
import threading
import time
import logging
import schedule
from datetime import datetime

# Configure logging
logger = logging.getLogger("job_tracker.cleanup")

def cleanup_logs_task():
    """Perform scheduled log cleanup"""
    from log_manager import cleanup_old_logs
    
    logger.info("Running scheduled log cleanup")
    try:
        deleted_count = cleanup_old_logs(days=2)
        logger.info(f"Deleted {deleted_count} old log files")
    except Exception as e:
        logger.error(f"Error during log cleanup: {str(e)}")

def cleanup_database_task():
    """Perform scheduled database cleanup"""
    from purge_old_records import purge_old_records
    
    logger.info("Running scheduled database cleanup")
    try:
        removed_count = purge_old_records(days=7)
        logger.info(f"Removed {removed_count} old database records")
    except Exception as e:
        logger.error(f"Error during database cleanup: {str(e)}")

def run_scheduled_tasks():
    """Run the scheduled tasks"""
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute

def start_scheduled_cleanup_thread():
    """Start the scheduled cleanup in a background thread"""
    # Schedule log cleanup daily at 3 AM
    schedule.every().day.at("03:00").do(cleanup_logs_task)
    
    # Schedule database cleanup daily at 4 AM
    schedule.every().day.at("04:00").do(cleanup_database_task)
    
    # Start the scheduler in a separate thread
    thread = threading.Thread(target=run_scheduled_tasks, daemon=True)
    thread.start()
    logger.info("Scheduled cleanup thread started")
    
    return thread

if __name__ == "__main__":
    # Setup logging when run directly
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("job_tracker.log")
        ]
    )
    
    logger.info("Starting scheduled cleanup service")
    cleanup_thread = start_scheduled_cleanup_thread()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(3600)  # Sleep for 1 hour
    except KeyboardInterrupt:
        logger.info("Scheduled cleanup service stopped")
