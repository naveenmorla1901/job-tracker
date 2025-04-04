"""
Utility script to safely restart job tracker services.
This script:
1. Kills existing processes
2. Restarts the services
"""
import os
import sys
import subprocess
import time
import logging
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("restart.log")
    ]
)
logger = logging.getLogger("job_tracker.restart")

def is_running_on_server():
    """Check if we're running on a Linux server"""
    return platform.system() == "Linux"

def restart_service(service_name):
    """Restart a systemd service"""
    if not is_running_on_server():
        logger.warning(f"Not running on Linux server, can't restart {service_name}")
        return False
    
    try:
        # Check if the service exists
        check_cmd = ["systemctl", "list-unit-files", service_name]
        result = subprocess.run(check_cmd, capture_output=True, text=True)
        
        if service_name not in result.stdout:
            logger.error(f"Service {service_name} not found")
            return False
        
        # Restart the service
        logger.info(f"Restarting {service_name}...")
        restart_cmd = ["sudo", "systemctl", "restart", service_name]
        result = subprocess.run(restart_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error(f"Failed to restart {service_name}: {result.stderr}")
            return False
        
        # Check service status
        status_cmd = ["systemctl", "is-active", service_name]
        result = subprocess.run(status_cmd, capture_output=True, text=True)
        
        if result.stdout.strip() == "active":
            logger.info(f"{service_name} restarted successfully")
            return True
        else:
            logger.error(f"{service_name} failed to start: {result.stdout.strip()}")
            return False
    
    except Exception as e:
        logger.error(f"Error restarting {service_name}: {str(e)}")
        return False

def kill_process_by_port(port):
    """Kill processes using a specific port"""
    try:
        # Import free_port module for port management
        from free_port import free_port
        
        # Free the port by killing any processes using it
        if free_port(port):
            logger.info(f"Successfully freed port {port}")
            return True
        else:
            logger.error(f"Failed to free port {port}")
            return False
    
    except Exception as e:
        logger.error(f"Error killing process on port {port}: {str(e)}")
        return False

def restart_job_tracker():
    """Restart all job tracker services"""
    logger.info("=" * 80)
    logger.info("Starting job tracker service restart")
    logger.info("=" * 80)
    
    success = True
    
    if is_running_on_server():
        # We're on Linux, use systemd services
        services = ["job-tracker-api.service", "job-tracker-dashboard.service"]
        
        for service in services:
            if not restart_service(service):
                success = False
    else:
        # We're on Windows or macOS, use direct process management
        logger.info("Not running on Linux server, using direct process management")
        
        # First, kill processes on the ports we need
        kill_process_by_port(8001)  # API port
        kill_process_by_port(8501)  # Dashboard port
        
        # Then start the processes using run.py
        
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Get the Python executable from the virtual environment
        if platform.system() == "Windows":
            python_exe = os.path.join(current_dir, "venv", "Scripts", "python.exe")
        else:
            python_exe = os.path.join(current_dir, "venv", "bin", "python")
        
        # Start the API
        try:
            logger.info("Starting API...")
            subprocess.Popen([python_exe, "run.py", "api"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE,
                           cwd=current_dir)
            logger.info("API started")
        except Exception as e:
            logger.error(f"Error starting API: {str(e)}")
            success = False
        
        # Wait for API to initialize
        time.sleep(5)
        
        # Start the dashboard
        try:
            logger.info("Starting dashboard...")
            subprocess.Popen([python_exe, "run.py", "dashboard"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE,
                           cwd=current_dir)
            logger.info("Dashboard started")
        except Exception as e:
            logger.error(f"Error starting dashboard: {str(e)}")
            success = False
    
    if success:
        logger.info("All services restarted successfully")
    else:
        logger.warning("Some services failed to restart")
    
    return success

if __name__ == "__main__":
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Restart job tracker services")
    parser.add_argument("--service", choices=["api", "dashboard", "all"], default="all",
                        help="Which service to restart (default: all)")
    args = parser.parse_args()
    
    if args.service == "api":
        if is_running_on_server():
            restart_service("job-tracker-api.service")
        else:
            kill_process_by_port(8001)
            # Start API using run.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if platform.system() == "Windows":
                python_exe = os.path.join(current_dir, "venv", "Scripts", "python.exe")
            else:
                python_exe = os.path.join(current_dir, "venv", "bin", "python")
            subprocess.Popen([python_exe, "run.py", "api"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE,
                           cwd=current_dir)
    elif args.service == "dashboard":
        if is_running_on_server():
            restart_service("job-tracker-dashboard.service")
        else:
            kill_process_by_port(8501)
            # Start dashboard using run.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if platform.system() == "Windows":
                python_exe = os.path.join(current_dir, "venv", "Scripts", "python.exe")
            else:
                python_exe = os.path.join(current_dir, "venv", "bin", "python")
            subprocess.Popen([python_exe, "run.py", "dashboard"], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.PIPE,
                           cwd=current_dir)
    else:
        restart_job_tracker()
