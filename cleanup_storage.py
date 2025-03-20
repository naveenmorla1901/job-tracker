#!/usr/bin/env python
# Script to clean up redundant backup files and optimize storage
import os
import shutil
import logging
import time
from datetime import datetime, timedelta

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("cleanup.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def get_file_size(file_path):
    """Get file size in MB"""
    return os.path.getsize(file_path) / (1024 * 1024)

def cleanup_backups(backups_dir="backups", max_age_days=7):
    """Clean up backup files older than specified days"""
    if not os.path.exists(backups_dir):
        logger.warning(f"Backup directory {backups_dir} not found.")
        return

    logger.info(f"Cleaning up backup files in {backups_dir}...")
    backup_count = 0
    backup_size = 0
    
    # Calculate cutoff date
    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    
    for filename in os.listdir(backups_dir):
        file_path = os.path.join(backups_dir, filename)
        
        # Skip directories
        if os.path.isdir(file_path):
            continue
            
        # Check file age
        file_modified = datetime.fromtimestamp(os.path.getmtime(file_path))
        
        if file_modified < cutoff_date:
            file_size = get_file_size(file_path)
            logger.info(f"Removing old backup: {filename} ({file_size:.2f} MB)")
            
            try:
                os.remove(file_path)
                backup_count += 1
                backup_size += file_size
            except Exception as e:
                logger.error(f"Error removing {filename}: {str(e)}")
    
    logger.info(f"Removed {backup_count} old backup files, freeing {backup_size:.2f} MB")

def cleanup_git():
    """Run git garbage collection to optimize storage"""
    try:
        logger.info("Running Git garbage collection...")
        start_time = time.time()
        
        # Run git gc
        os.system("git gc --aggressive --prune=now")
        
        # Get .git directory size before and after
        git_dir_size_after = get_directory_size(".git")
        
        logger.info(f"Git optimization completed in {time.time() - start_time:.2f} seconds")
        logger.info(f"Git directory size after optimization: {git_dir_size_after:.2f} MB")
    except Exception as e:
        logger.error(f"Error during Git optimization: {str(e)}")

def get_directory_size(directory):
    """Get directory size in MB"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(directory):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            total_size += os.path.getsize(file_path)
    
    return total_size / (1024 * 1024)  # Convert to MB

def cleanup_pycache():
    """Clean up __pycache__ directories"""
    pycache_dirs = []
    pycache_size = 0
    
    logger.info("Finding __pycache__ directories...")
    
    # Find all __pycache__ directories
    for root, dirs, files in os.walk("."):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            pycache_dirs.append(pycache_path)
            pycache_size += get_directory_size(pycache_path)
    
    logger.info(f"Found {len(pycache_dirs)} __pycache__ directories, total size: {pycache_size:.2f} MB")
    
    # Remove them
    for pycache_dir in pycache_dirs:
        logger.info(f"Removing {pycache_dir}")
        try:
            shutil.rmtree(pycache_dir)
        except Exception as e:
            logger.error(f"Error removing {pycache_dir}: {str(e)}")
    
    logger.info(f"Removed {len(pycache_dirs)} __pycache__ directories, freeing {pycache_size:.2f} MB")

def cleanup_logs(log_dir=".", max_size_mb=10):
    """Clean up log files larger than max_size_mb"""
    log_extensions = [".log"]
    large_logs = []
    
    logger.info(f"Checking for large log files (>{max_size_mb} MB)...")
    
    for root, dirs, files in os.walk(log_dir):
        for filename in files:
            if any(filename.endswith(ext) for ext in log_extensions):
                file_path = os.path.join(root, filename)
                file_size = get_file_size(file_path)
                
                if file_size > max_size_mb:
                    large_logs.append((file_path, file_size))
    
    logger.info(f"Found {len(large_logs)} large log files")
    
    for file_path, file_size in large_logs:
        logger.info(f"Truncating large log: {file_path} ({file_size:.2f} MB)")
        
        try:
            # Instead of deleting, we'll truncate
            with open(file_path, 'r+') as f:
                f.seek(0)
                f.truncate()
                f.write(f"Log truncated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by emergency cleanup\n")
        except Exception as e:
            logger.error(f"Error truncating {file_path}: {str(e)}")

def main():
    """Main function to clean up storage
    
    Note: This script can be run directly or called from apply_fixes.py
    For more comprehensive maintenance, use scripts/maintenance.sh
    """
    logger.info("Starting storage cleanup...")
    
    # Get initial storage info
    total_size_before = get_directory_size(".")
    logger.info(f"Total project size before cleanup: {total_size_before:.2f} MB")
    
    # Perform cleanup operations
    cleanup_backups()
    cleanup_git()
    cleanup_pycache()
    cleanup_logs()
    
    # Get final storage info
    total_size_after = get_directory_size(".")
    saved = total_size_before - total_size_after
    logger.info(f"Total project size after cleanup: {total_size_after:.2f} MB")
    logger.info(f"Storage saved: {saved:.2f} MB ({saved/total_size_before*100:.1f}%)")

if __name__ == "__main__":
    main()
    print("\nNote: For full system maintenance, use scripts/maintenance.sh")
    print("      or scripts/cleanup_disk_space.sh for interactive cleanup")
