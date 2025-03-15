"""
Simplified log management utilities for job tracker

This module provides functions to read, clean, and rotate log files
"""
import os
import logging
from datetime import datetime, timedelta
import glob
import pytz

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
    Read content from a log file and adjust timezone if needed
    """
    try:
        if not os.path.exists(log_file):
            return []

        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            # Read last N lines
            lines = f.readlines()
            if len(lines) > max_lines:
                lines = lines[-max_lines:]
                
            # Fix timezone issue (convert from UTC to local time)
            corrected_lines = []
            for line in lines:
                try:
                    # Check if this is a log line with a timestamp
                    if len(line) > 19 and line[4] == '-' and line[7] == '-' and line[10] == ' ' and line[13] == ':' and line[16] == ':':
                        # Extract timestamp part (2025-03-02 18:06:04)
                        timestamp_str = line[:19]
                        rest_of_line = line[19:]
                        
                        # Parse the timestamp
                        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        
                        # Assuming the timestamp is in UTC and we want to convert to EST (UTC-5)
                        local_tz = pytz.timezone('America/New_York')  # Adjust to your local timezone
                        utc_dt = pytz.utc.localize(dt)
                        local_dt = utc_dt.astimezone(local_tz)
                        
                        # Create new line with the corrected timestamp
                        corrected_line = local_dt.strftime("%Y-%m-%d %H:%M:%S") + rest_of_line
                        corrected_lines.append(corrected_line)
                    else:
                        # Not a timestamp line, keep as is
                        corrected_lines.append(line)
                except Exception:
                    # If any error in parsing, keep the original line
                    corrected_lines.append(line)
                    
            return corrected_lines
    except Exception as e:
        logger.error(f"Error reading log file {log_file}: {str(e)}")
        return []

def cleanup_old_logs(days=2, log_dir="logs", max_log_size_mb=2):
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
            if os.path.exists(main_log):
                # Always rotate main logs if they exist to keep them small
                if os.path.getsize(main_log) > max_log_size_mb * 1024 * 1024:
                    archive_name = rotate_log(main_log, log_dir)
                    if archive_name:
                        archive_logs.append(archive_name)
                        logger.info(f"Rotated main log {main_log} (exceeded {max_log_size_mb}MB)")
        
        # Make sure we get all log files in the logs directory
        all_log_files = glob.glob(os.path.join(log_dir, "*.log"))
        
        # Add archive logs to the list
        log_files = list(set(log_files + all_log_files + archive_logs))
        
        # Current time for comparison
        now = datetime.now()
        deleted_count = 0
        deleted_size = 0
        
        for log_file in log_files:
            try:
                # Skip main logs in root directory
                if log_file in main_logs:
                    continue
                    
                # Get file modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                
                # If older than specified days, delete it
                if now - mtime > timedelta(days=days):
                    # Get file size before deletion for reporting
                    file_size = os.path.getsize(log_file) if os.path.exists(log_file) else 0
                    
                    # Delete the file
                    os.remove(log_file)
                    deleted_count += 1
                    deleted_size += file_size
                    logger.info(f"Deleted old log file: {log_file} ({file_size / (1024*1024):.2f} MB)")
            except Exception as e:
                logger.error(f"Error processing log file {log_file}: {str(e)}")
        
        # Report total deleted size
        if deleted_count > 0:
            logger.info(f"Total log cleanup: {deleted_count} files, {deleted_size / (1024*1024):.2f} MB")
                
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
