"""
Simplified log management utilities for job tracker

This module provides functions to read, clean, and rotate log files
"""
import os
import re
import logging
from collections import deque
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

def default_api_log_paths():
    """Paths checked for API / scheduler scraper output (same order as dashboard API tab)."""
    return [
        "job_tracker.log",
        "/var/log/job-tracker/api.log",
        "/home/ubuntu/job-tracker/job_tracker.log",
    ]


def _read_log_tail_raw_lines(log_file, max_lines):
    """Return up to the last max_lines from a log file (no timezone rewriting)."""
    if not os.path.exists(log_file):
        return []
    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
        if len(all_lines) <= max_lines:
            return all_lines
        return all_lines[-max_lines:]
    except Exception as e:
        logger.error(f"Error tailing log file {log_file}: {str(e)}")
        return []


def _merged_tail_lines_from_paths(log_paths, max_lines_per_file):
    """Read tails from each path, merge and sort by leading timestamp."""
    collected = []
    for path in log_paths:
        collected.extend(_read_log_tail_raw_lines(path, max_lines_per_file))

    def sort_key(line):
        try:
            if len(line) > 19 and line[4] == "-" and line[7] == "-" and line[10] == " ":
                return datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
        return datetime.min

    collected.sort(key=sort_key)
    return collected


def _scraper_line_matcher(scraper_name):
    """Match lines emitted by app.scheduler.jobs run_scraper for this module name."""
    e = re.escape(scraper_name)
    return re.compile(
        rf"(?:Running scraper \d+/\d+: {e}\b|"
        rf"Scraper {e} |"
        rf"SCRAPER FAILURE: {e} \|"
        rf"Using custom roles for {e}:|"
        rf"Full traceback for {e}:)"
    )


def get_scraper_log_snippets(
    scraper_names,
    log_paths=None,
    lines_per_scraper=12,
    max_tail_lines_per_file=80_000,
):
    """
    For each scraper module name, return the last ``lines_per_scraper`` log lines
    that refer to that scraper's scheduler run (from merged API log tails).
    """
    if log_paths is None:
        log_paths = default_api_log_paths()

    existing = [p for p in log_paths if os.path.exists(p)]
    if not existing:
        return {}

    merged = _merged_tail_lines_from_paths(existing, max_tail_lines_per_file)
    if not merged:
        return {name: [] for name in scraper_names}

    matchers = {name: _scraper_line_matcher(name) for name in scraper_names}
    buffers = {name: deque(maxlen=lines_per_scraper) for name in scraper_names}
    for line in merged:
        low = line.lower()
        if "scraper" not in low and "custom roles" not in low:
            continue
        for name, rx in matchers.items():
            if rx.search(line):
                buffers[name].append(line)

    return {name: list(buf) for name, buf in buffers.items()}


def read_log_content(log_file, max_lines=5000):
    """
    Read content from a log file and adjust timezone if needed
    """
    try:
        if not os.path.exists(log_file):
            return []

        with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
            # Read all lines from the file
            all_lines = f.readlines()
            
            # Check for scraper run summaries to highlight in logs
            scraper_summary_lines = []
            for i, line in enumerate(all_lines):
                if "SCRAPER RUN SUMMARY" in line:
                    # Collect this line and the next 7 lines which typically contain the summary
                    summary_block = all_lines[i:i+8]
                    scraper_summary_lines.extend(summary_block)
            
            # Limit lines for display
            if len(all_lines) > max_lines:
                # First include important scraper summary logs
                selected_lines = scraper_summary_lines
                
                # Then add the most recent logs up to max_lines
                remaining_lines = max_lines - len(selected_lines)
                if remaining_lines > 0:
                    selected_lines.extend(all_lines[-remaining_lines:])
                
                # Sort lines to maintain chronological order
                # Try to parse timestamps and sort
                def get_timestamp(line):
                    try:
                        if len(line) > 19 and line[4] == '-' and line[7] == '-' and line[10] == ' ':
                            return datetime.strptime(line[:19], "%Y-%m-%d %H:%M:%S")
                    except:
                        pass
                    return datetime.min
                
                sorted_lines = sorted(selected_lines, key=get_timestamp)
            else:
                sorted_lines = all_lines
                
            # Fix timezone issue (convert from UTC to local time)
            corrected_lines = []
            for line in sorted_lines:
                try:
                    # Check if this is a log line with a timestamp
                    if len(line) > 19 and line[4] == '-' and line[7] == '-' and line[10] == ' ' and line[13] == ':' and line[16] == ':':
                        # Extract timestamp part (2025-03-02 18:06:04)
                        timestamp_str = line[:19]
                        rest_of_line = line[19:]
                        
                        # Parse the timestamp
                        dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        
                        # Assuming the timestamp is in UTC and we want to convert to local timezone
                        try:
                            local_tz = pytz.timezone('America/New_York')  # Adjust to your local timezone
                            utc_dt = pytz.utc.localize(dt)
                            local_dt = utc_dt.astimezone(local_tz)
                            
                            # Create new line with the corrected timestamp
                            corrected_line = local_dt.strftime("%Y-%m-%d %H:%M:%S") + rest_of_line
                        except:
                            # If timezone conversion fails, use the original timestamp
                            corrected_line = line
                        
                        # Highlight important scraper summary lines
                        if "SCRAPER RUN SUMMARY" in corrected_line:
                            corrected_line = "\n" + "=" * 50 + "\n" + corrected_line
                        elif "Total jobs added:" in corrected_line or "Total jobs updated:" in corrected_line:
                            corrected_line = ">>> " + corrected_line
                            
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
