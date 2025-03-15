"""
Script to optimize storage and processes in the job_tracker project
"""
import os
import sys
import shutil
import glob
import psutil
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('job_tracker.optimize')

def clean_pycache():
    """Clean up __pycache__ directories"""
    project_dir = os.path.abspath(os.path.dirname(__file__))
    pycache_dirs = []
    
    # Find all __pycache__ directories
    for dirpath, dirnames, filenames in os.walk(project_dir):
        for dirname in dirnames:
            if dirname == "__pycache__":
                pycache_dirs.append(os.path.join(dirpath, dirname))
    
    # Delete each __pycache__ directory
    total_size = 0
    count = 0
    for cache_dir in pycache_dirs:
        try:
            # Calculate size before deletion
            dir_size = 0
            for dirpath, dirnames, filenames in os.walk(cache_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.exists(fp):
                        dir_size += os.path.getsize(fp)
            
            # Delete the directory
            shutil.rmtree(cache_dir)
            total_size += dir_size
            count += 1
            logger.info(f"Removed: {cache_dir} ({dir_size / (1024*1024):.2f} MB)")
        except Exception as e:
            logger.error(f"Error removing {cache_dir}: {str(e)}")
    
    logger.info(f"Cleaned {count} __pycache__ directories, freed {total_size / (1024*1024):.2f} MB")
    return count, total_size

def clean_temp_files():
    """Clean up temporary files"""
    project_dir = os.path.abspath(os.path.dirname(__file__))
    temp_exts = [".tmp", ".bak", ".pyc"]
    found_files = []
    
    # Find all temporary files
    for ext in temp_exts:
        for dirpath, dirnames, filenames in os.walk(project_dir):
            for f in filenames:
                if f.endswith(ext):
                    found_files.append(os.path.join(dirpath, f))
    
    # Delete each temporary file
    total_size = 0
    count = 0
    for filepath in found_files:
        try:
            # Calculate size before deletion
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                os.remove(filepath)
                total_size += file_size
                count += 1
                logger.info(f"Removed: {filepath} ({file_size / (1024*1024):.2f} MB)")
        except Exception as e:
            logger.error(f"Error removing {filepath}: {str(e)}")
    
    logger.info(f"Cleaned {count} temporary files, freed {total_size / (1024*1024):.2f} MB")
    return count, total_size

def aggressive_log_cleanup(days=1):
    """Perform aggressive log cleanup"""
    from log_manager import cleanup_old_logs, rotate_log
    
    # First rotate main logs to keep them small
    project_dir = os.path.abspath(os.path.dirname(__file__))
    log_dir = os.path.join(project_dir, "logs")
    
    # Ensure logs directory exists
    os.makedirs(log_dir, exist_ok=True)
    
    # Rotate main log files
    main_logs = ["job_tracker.log", "dashboard.log", "api.log"]
    for log_file in main_logs:
        log_path = os.path.join(project_dir, log_file)
        if os.path.exists(log_path) and os.path.getsize(log_path) > 1 * 1024 * 1024:  # 1MB
            logger.info(f"Rotating log file: {log_file}")
            rotate_log(log_file, log_dir)
    
    # Run standard log cleanup
    deleted_count = cleanup_old_logs(days=days, max_log_size_mb=1)
    
    return deleted_count

def clean_old_backups(days=14):
    """Clean up old backup files"""
    project_dir = os.path.abspath(os.path.dirname(__file__))
    backup_dir = os.path.join(project_dir, "backups")
    
    if not os.path.exists(backup_dir):
        logger.info("No backups directory found")
        return 0, 0
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=days)
    
    # Find files older than cutoff date
    old_files = []
    total_size = 0
    count = 0
    
    for filepath in glob.glob(os.path.join(backup_dir, "*")):
        if os.path.isfile(filepath):
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if mtime < cutoff_date:
                file_size = os.path.getsize(filepath)
                old_files.append((filepath, file_size))
    
    # Delete old files
    for filepath, file_size in old_files:
        try:
            os.remove(filepath)
            total_size += file_size
            count += 1
            logger.info(f"Removed old backup: {os.path.basename(filepath)} ({file_size / (1024*1024):.2f} MB)")
        except Exception as e:
            logger.error(f"Error removing {filepath}: {str(e)}")
    
    logger.info(f"Cleaned {count} old backup files, freed {total_size / (1024*1024):.2f} MB")
    return count, total_size

def clean_zombie_processes():
    """Find and clean up zombie or hung processes related to the project"""
    killed_count = 0
    
    try:
        # Look for Python processes that might be related to our app
        python_procs = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'create_time']):
            try:
                if "python" in proc.name().lower():
                    # Check if process is related to our app
                    cmdline = " ".join(proc.cmdline())
                    if any(keyword in cmdline for keyword in ["job_tracker", "uvicorn main", "streamlit run dashboard"]):
                        age_minutes = (datetime.now() - datetime.fromtimestamp(proc.create_time())).total_seconds() / 60
                        
                        # Check if process is using high CPU or memory, or has been running for too long
                        if proc.cpu_percent() > 90 or (proc.memory_info().rss / (1024*1024)) > 500 or age_minutes > 720:  # 12 hours
                            python_procs.append((proc, age_minutes))
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        
        # Sort by age, oldest first
        python_procs.sort(key=lambda x: x[1], reverse=True)
        
        # Kill problematic processes
        for proc, age_minutes in python_procs:
            try:
                logger.info(f"Terminating process {proc.pid} (running for {age_minutes:.1f} minutes): {' '.join(proc.cmdline())}")
                proc.terminate()
                killed_count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                logger.error(f"Failed to terminate process {proc.pid}")
        
        logger.info(f"Terminated {killed_count} problematic processes")
    except Exception as e:
        logger.error(f"Error cleaning zombie processes: {str(e)}")
    
    return killed_count

def optimize_storage():
    """Run all optimization tasks"""
    logger.info("Starting storage and process optimization")
    
    # Track total space freed and files cleaned
    total_space_freed = 0
    total_files_cleaned = 0
    
    # Clean __pycache__ directories
    count, size = clean_pycache()
    total_files_cleaned += count
    total_space_freed += size
    
    # Clean temporary files
    count, size = clean_temp_files()
    total_files_cleaned += count
    total_space_freed += size
    
    # Aggressive log cleanup
    deleted_count = aggressive_log_cleanup(days=1)
    total_files_cleaned += deleted_count
    
    # Clean old backups
    count, size = clean_old_backups()
    total_files_cleaned += count
    total_space_freed += size
    
    # Clean zombie processes
    killed_count = clean_zombie_processes()
    
    # Report results
    logger.info(f"Optimization completed:")
    logger.info(f"  - Total files cleaned: {total_files_cleaned}")
    logger.info(f"  - Total space freed: {total_space_freed / (1024*1024):.2f} MB")
    logger.info(f"  - Problematic processes terminated: {killed_count}")
    
    return {
        "files_cleaned": total_files_cleaned,
        "space_freed_mb": total_space_freed / (1024*1024),
        "processes_terminated": killed_count
    }

if __name__ == "__main__":
    # When run directly, perform optimization
    optimize_storage()
