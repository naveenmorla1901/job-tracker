"""
Simplified log management utilities for job tracker

This module provides functions to read, clean, and rotate log files
"""
import os
import logging
from datetime import datetime, timedelta
import glob

# Configure logging
logger = logging.getLogger("job_tracker.log_manager")

def get_log_files(log_dir="logs"):
    """
    Get all log files in the specified directory
    """
    try:
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            logger.info(f"Created logs directory: {log_dir}")

        # Get all log files
        log_files = glob.glob(os.path.join(log_dir, "*.log"))
        
        # Also include specific log files in root directory
        for file in ["job_tracker.log", "dashboard.log", "api.log"]:
            if os.path.exists(file):
                log_files.append(file)
            
        return log_files
    except Exception as e:
        logger.error(f"Error reading log files: {str(e)}")
        return []

def read_log_content(log_file, max_lines=5000):
    """
    Read content from a log file
    """
    try:
        if not os.path.exists(log_file):
            return []

        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            # Read last N lines
            lines = f.readlines()
            if len(lines) > max_lines:
                lines = lines[-max_lines:]
            return lines
    except Exception as e:
        logger.error(f"Error reading log file {log_file}: {str(e)}")
        return []

def cleanup_old_logs(days=2, log_dir="logs"):
    """
    Delete log files older than the specified number of days
    Also rotate main logs if they're too large
    """
    try:
        # Get all log files
        log_files = get_log_files(log_dir)
        
        # Main log files to rotate but not delete
        main_logs = ["job_tracker.log", "dashboard.log", "api.log"]
        archive_logs = []
        
        for main_log in main_logs:
            if main_log in log_files:
                log_files.remove(main_log)
                # Rotate if larger than 5MB
                if os.path.exists(main_log) and os.path.getsize(main_log) > 5 * 1024 * 1024:
                    archive_name = rotate_log(main_log, log_dir)
                    if archive_name:
                        archive_logs.append(archive_name)
            
        # Add archive logs to the list
        log_files.extend(archive_logs)
        
        # Current time for comparison
        now = datetime.now()
        deleted_count = 0
        
        for log_file in log_files:
            try:
                # Skip main logs
                if log_file in main_logs:
                    continue
                    
                # Get file modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                
                # If older than specified days, delete it
                if now - mtime > timedelta(days=days):
                    os.remove(log_file)
                    deleted_count += 1
                    logger.info(f"Deleted old log file: {log_file}")
            except Exception as e:
                logger.error(f"Error processing log file {log_file}: {str(e)}")
                
        return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up old logs: {str(e)}")
        return 0

def rotate_log(log_file, log_dir="logs"):
    """
    Rotate a log file
    Returns the name of the archive file or None if rotation failed
    """
    try:
        if not os.path.exists(log_file):
            return None
            
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Create a timestamped copy
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Get the base name without path
        base_name = os.path.basename(log_file)
        base_name_without_ext = os.path.splitext(base_name)[0]
        archive_name = os.path.join(log_dir, f"{base_name_without_ext}_{timestamp}.log")
        
        # Read the content of the log
        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        # Write to archive
        with open(archive_name, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Clear the log but keep the file
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(f"Log rotated at {datetime.now()} - Previous log saved to {archive_name}\n")
            
        logger.info(f"Rotated log {log_file} to {archive_name}")
        return archive_name
    except Exception as e:
        logger.error(f"Error rotating log {log_file}: {str(e)}")
        return None

if __name__ == "__main__":
    # When run directly, perform log cleanup
    deleted = cleanup_old_logs(days=2)
    print(f"Deleted {deleted} old log files")
