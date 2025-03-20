#!/usr/bin/env python
# Script to apply all fixes for the job tracker issues
import os
import logging
import argparse
import subprocess
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("fixes.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def run_command(command):
    """Run a command and return its output"""
    try:
        logger.info(f"Running command: {command}")
        result = subprocess.run(command, shell=True, check=True, 
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                               universal_newlines=True)
        logger.info(f"Command completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed with code {e.returncode}")
        logger.error(f"Error output: {e.stderr}")
        return None

def clean_storage():
    """Run the storage cleanup script"""
    logger.info("Cleaning up storage...")
    try:
        # First try to use the bash script if available
        if os.path.exists("scripts/cleanup_disk_space.sh") and os.name != 'nt':
            logger.info("Using existing cleanup_disk_space.sh script")
            result = run_command("bash scripts/cleanup_disk_space.sh")
            if result is not None:
                logger.info("Storage cleanup completed via bash script")
                return True
        
        # Fall back to Python script
        import cleanup_storage
        cleanup_storage.main()
        logger.info("Storage cleanup completed via Python script")
        return True
    except Exception as e:
        logger.error(f"Storage cleanup failed: {str(e)}")
        return False

def update_database():
    """Run the database migration to update the schema"""
    logger.info("Updating database schema...")
    try:
        # First run alembic to generate migration
        run_command("alembic revision --autogenerate -m \"Update datetime columns to use timezone\"")
        
        # Then apply the migration
        result = run_command("alembic upgrade head")
        
        if result:
            logger.info("Database schema updated successfully")
            return True
        else:
            logger.error("Database update may have failed")
            return False
    except Exception as e:
        logger.error(f"Database update failed: {str(e)}")
        return False

def restart_services():
    """Restart the API and dashboard services"""
    logger.info("Restarting services...")
    try:
        # First try to use the maintenance script if available
        if os.path.exists("scripts/maintenance.sh") and os.name != 'nt':
            logger.info("Using existing maintenance.sh script")
            result = run_command("bash scripts/maintenance.sh 2")
            if result is not None:
                logger.info("Services restarted via maintenance script")
                return True
        
        # Fall back to direct systemctl commands
        if os.path.exists("/etc/systemd/system/job-tracker-api.service"):
            # Running on Linux with systemd
            run_command("sudo systemctl restart job-tracker-api.service")
            run_command("sudo systemctl restart job-tracker-dashboard.service")
        else:
            # Running locally or in a different environment
            logger.info("No system services found, assuming local development environment")
            logger.info("Please restart the API and dashboard manually:")
            logger.info("1. Run 'python run.py api' in one terminal")
            logger.info("2. Run 'python run.py dashboard' in another terminal")
        
        return True
    except Exception as e:
        logger.error(f"Service restart failed: {str(e)}")
        return False

def main():
    """Apply all fixes"""
    parser = argparse.ArgumentParser(description="Apply fixes to the job tracker")
    parser.add_argument("--storage", action="store_true", help="Clean up storage only")
    parser.add_argument("--database", action="store_true", help="Update database schema only")
    parser.add_argument("--restart", action="store_true", help="Restart services only")
    parser.add_argument("--all", action="store_true", help="Apply all fixes (default)")
    
    args = parser.parse_args()
    
    # If no specific option is provided, do everything
    if not (args.storage or args.database or args.restart):
        args.all = True
    
    success = True
    
    # Clean up storage
    if args.storage or args.all:
        if not clean_storage():
            success = False
    
    # Update database schema
    if args.database or args.all:
        if not update_database():
            success = False
    
    # Restart services
    if args.restart or args.all:
        if not restart_services():
            success = False
    
    if success:
        logger.info("All fixes applied successfully")
    else:
        logger.error("Some fixes failed, please check the log")
        sys.exit(1)

if __name__ == "__main__":
    main()
    logger.info("\nNote: For full system maintenance, use scripts/maintenance.sh")
    print("\nNote: For full system maintenance, use scripts/maintenance.sh")
    print("      This script provides specific fixes for timestamp, log display, and role issues")
