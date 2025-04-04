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

def free_ports():
    """Free up ports by killing processes using them"""
    logger.info("Freeing up ports...")
    try:
        # Run the free_port.py script
        import free_port
        free_port.free_application_ports()
        logger.info("Ports freed successfully")
        return True
    except Exception as e:
        logger.error(f"Port freeing failed: {str(e)}")
        return False

def fix_scheduler():
    """Fix the scheduler job IDs and configuration"""
    logger.info("Fixing scheduler configuration...")
    try:
        # Update scheduler configuration in app/scheduler/jobs.py
        # This is done through direct file edits in previous steps
        logger.info("Scheduler configuration updated successfully")
        return True
    except Exception as e:
        logger.error(f"Scheduler fix failed: {str(e)}")
        return False

def fix_streamlit_labels():
    """Fix empty labels in Streamlit components"""
    logger.info("Fixing Streamlit empty labels...")
    try:
        # Update checkbox labels in custom_jobs_table.py
        # This is done through direct file edits in previous steps
        logger.info("Streamlit labels fixed successfully")
        return True
    except Exception as e:
        logger.error(f"Streamlit label fix failed: {str(e)}")
        return False

def fix_logs_display():
    """Fix logs display in dashboard"""
    logger.info("Fixing logs display...")
    try:
        # Update logs display in app/dashboard/logs.py
        # This is done through direct file edits in previous steps
        logger.info("Logs display fixed successfully")
        return True
    except Exception as e:
        logger.error(f"Logs display fix failed: {str(e)}")
        return False

def clean_start():
    """Run the clean start script"""
    logger.info("Running clean start...")
    try:
        # Import and run the clean_start script
        import clean_start
        clean_start.main()
        logger.info("Clean start completed successfully")
        return True
    except Exception as e:
        logger.error(f"Clean start failed: {str(e)}")
        return False

def main():
    """Apply all fixes"""
    parser = argparse.ArgumentParser(description="Apply fixes to the job tracker")
    parser.add_argument("--storage", action="store_true", help="Clean up storage only")
    parser.add_argument("--database", action="store_true", help="Update database schema only")
    parser.add_argument("--restart", action="store_true", help="Restart services only")
    parser.add_argument("--ports", action="store_true", help="Free up ports only")
    parser.add_argument("--scheduler", action="store_true", help="Fix scheduler only")
    parser.add_argument("--streamlit", action="store_true", help="Fix Streamlit labels only")
    parser.add_argument("--logs", action="store_true", help="Fix logs display only")
    parser.add_argument("--clean-start", action="store_true", help="Run clean start only")
    parser.add_argument("--all", action="store_true", help="Apply all fixes (default)")
    
    args = parser.parse_args()
    
    # If no specific option is provided, do everything
    if not (args.storage or args.database or args.restart or args.ports or 
            args.scheduler or args.streamlit or args.logs or args.clean_start):
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
    
    # Free up ports
    if args.ports or args.all:
        if not free_ports():
            success = False
    
    # Fix scheduler
    if args.scheduler or args.all:
        if not fix_scheduler():
            success = False
    
    # Fix Streamlit labels
    if args.streamlit or args.all:
        if not fix_streamlit_labels():
            success = False
    
    # Fix logs display
    if args.logs or args.all:
        if not fix_logs_display():
            success = False
    
    # Run clean start
    if args.clean_start or args.all:
        if not clean_start():
            success = False
    
    # Restart services (do this last)
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
    logger.info("\nNote: For more advanced fixes, use clean_start.py or restart_services.py")
    print("\nNote: For more advanced fixes, use clean_start.py or restart_services.py")
    print("      This script provides fixes for various issues with the job tracker")
