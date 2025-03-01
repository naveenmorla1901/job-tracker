"""
Log management utilities for job tracker

This module provides functions to read, clean, and rotate log files
"""
import os
import re
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
        
        # Also include job_tracker.log in root directory
        if os.path.exists("job_tracker.log"):
            log_files.append("job_tracker.log")
            
        return log_files
    except Exception as e:
        logger.error(f"Error reading log files: {str(e)}")
        return []

def read_log_content(log_file, max_lines=1000):
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

def extract_scraper_runs(log_content):
    """
    Extract scraper run information from log content
    """
    scraper_runs = []
    current_run = {"start_time": None, "scrapers": [], "summary": None}
    in_run = False
    
    for line in log_content:
        # Match run start
        if "RUNNING ALL SCRAPERS NOW" in line.upper():
            # If we were already in a run, save the previous one
            if in_run and current_run["scrapers"]:
                scraper_runs.append(current_run)
                
            # Start a new run
            timestamp = line.split(" - ", 1)[0]
            current_run = {
                "start_time": timestamp,
                "scrapers": [],
                "summary": None
            }
            in_run = True
            
        # Match individual scraper
        elif in_run and "SCRAPER" in line and "COMPLETED" in line.upper():
            scraper_info = re.search(r"Scraper (\w+) completed: (\d+) added, (\d+) updated, (\d+) expired", line)
            if scraper_info:
                scraper_name, added, updated, expired = scraper_info.groups()
                timestamp = line.split(" - ", 1)[0]
                current_run["scrapers"].append({
                    "time": timestamp,
                    "name": scraper_name,
                    "added": int(added),
                    "updated": int(updated),
                    "expired": int(expired)
                })
                
        # Match run summary
        elif in_run and "SCRAPER RUN SUMMARY" in line.upper():
            timestamp = line.split(" - ", 1)[0]
            summary_lines = []
            current_run["summary_time"] = timestamp
            
            # Get next few lines for summary
            i = log_content.index(line)
            for j in range(i, min(i+10, len(log_content))):
                if "===" in log_content[j]:
                    continue
                if "INFO" in log_content[j] and any(x in log_content[j] for x in ["Scrapers run", "Successful", "Failed", "Total jobs"]):
                    summary_part = log_content[j].split("INFO - ", 1)[1].strip() if "INFO - " in log_content[j] else log_content[j].strip()
                    summary_lines.append(summary_part)
            
            current_run["summary"] = summary_lines
            
            # End the run
            scraper_runs.append(current_run)
            current_run = {"start_time": None, "scrapers": [], "summary": None}
            in_run = False
    
    # Add the last run if it's still open
    if in_run and current_run["scrapers"]:
        scraper_runs.append(current_run)
        
    return scraper_runs

def cleanup_old_logs(days=2, log_dir="logs"):
    """
    Delete log files older than the specified number of days
    """
    try:
        # Get all log files
        log_files = get_log_files(log_dir)
        
        # Keep job_tracker.log (main log file)
        if "job_tracker.log" in log_files:
            log_files.remove("job_tracker.log")
            
        # Current time for comparison
        now = datetime.now()
        deleted_count = 0
        
        for log_file in log_files:
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(log_file))
                
                # If older than specified days, delete it
                if now - mtime > timedelta(days=days):
                    os.remove(log_file)
                    deleted_count += 1
                    logger.info(f"Deleted old log file: {log_file}")
            except Exception as e:
                logger.error(f"Error processing log file {log_file}: {str(e)}")
                
        # Handle job_tracker.log differently - rotate it if it's too large
        main_log = "job_tracker.log"
        if os.path.exists(main_log) and os.path.getsize(main_log) > 5 * 1024 * 1024:  # 5 MB
            rotate_main_log(main_log, log_dir)
            
        return deleted_count
    except Exception as e:
        logger.error(f"Error cleaning up old logs: {str(e)}")
        return 0

def rotate_main_log(main_log, log_dir="logs"):
    """
    Rotate the main log file
    """
    try:
        if not os.path.exists(main_log):
            return
            
        # Create logs directory if it doesn't exist
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
            
        # Create a timestamped copy
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = os.path.join(log_dir, f"job_tracker_{timestamp}.log")
        
        # Read the content of the main log
        with open(main_log, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
            
        # Write to archive
        with open(archive_name, 'w', encoding='utf-8') as f:
            f.write(content)
            
        # Clear the main log but keep the file
        with open(main_log, 'w', encoding='utf-8') as f:
            f.write(f"Log rotated at {datetime.now()} - Previous log saved to {archive_name}\n")
            
        logger.info(f"Rotated main log to {archive_name}")
    except Exception as e:
        logger.error(f"Error rotating main log: {str(e)}")

if __name__ == "__main__":
    # When run directly, perform log cleanup
    deleted = cleanup_old_logs(days=2)
    print(f"Deleted {deleted} old log files")
