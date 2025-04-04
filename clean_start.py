"""
Utility script to clean up and start the job tracker application properly.
This script:
1. Checks for and kills any existing application processes
2. Frees up the required ports (8001 for API, 8501 for dashboard)
3. Starts the application components
"""

import os
import sys
import time
import subprocess
import logging
import psutil
import platform

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("startup.log")
    ]
)
logger = logging.getLogger("job_tracker.clean_start")

# Import utility functions
from free_port import free_port, is_port_in_use
from port_utils import get_next_available_port

def check_postgres_connections():
    """Check active PostgreSQL connections"""
    try:
        # Get the current directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Build the path to the .env file
        env_file = os.path.join(current_dir, ".env")
        
        # Read DATABASE_URL from .env
        import re
        database_url = None
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith("DATABASE_URL="):
                        database_url = line.strip().split("=")[1].strip()
                        break
        
        if not database_url:
            logger.warning("Could not find DATABASE_URL in .env file")
            return
        
        # Extract database connection info
        match = re.match(r"postgresql://([^:]+):([^@]+)@([^:/]+)(?::(\d+))?/(.+)", database_url)
        if not match:
            logger.warning(f"Invalid DATABASE_URL format: {database_url}")
            return
        
        user, password, host, port, dbname = match.groups()
        port = port or "5432"  # Default PostgreSQL port
        
        # Build the SQL query to list active connections
        sql = "SELECT pid, datname, usename, application_name, client_addr, state, query_start, wait_event_type FROM pg_stat_activity WHERE datname = %s;"
        
        # Create a temporary file with the query
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sql') as f:
            f.write(sql)
            sql_file = f.name
        
        try:
            # Run the query using PSQL
            cmd = ["psql", "-h", host, "-p", port, "-U", user, "-d", dbname, "-f", sql_file]
            
            # Set the PGPASSWORD environment variable for authentication
            env = os.environ.copy()
            env["PGPASSWORD"] = password
            
            # Execute the command
            result = subprocess.run(cmd, capture_output=True, text=True, env=env)
            
            if result.returncode == 0:
                logger.info("Active PostgreSQL connections:")
                logger.info(result.stdout)
            else:
                logger.warning(f"Error checking PostgreSQL connections: {result.stderr}")
        finally:
            # Remove the temporary SQL file
            try:
                os.unlink(sql_file)
            except:
                pass
    except Exception as e:
        logger.error(f"Error checking PostgreSQL connections: {str(e)}")

def kill_process_by_name(name):
    """Kill all processes matching the given name"""
    killed = 0
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Check if this process matches the name we're looking for
                if (proc.info['name'] and name.lower() in proc.info['name'].lower()) or \
                   (proc.info['cmdline'] and any(name.lower() in cmd.lower() for cmd in proc.info['cmdline'] if cmd)):
                    logger.info(f"Killing process: {proc.info['pid']} {proc.info['name']} {' '.join(proc.info['cmdline'])}")
                    proc.terminate()
                    killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
    except Exception as e:
        logger.error(f"Error killing processes by name {name}: {str(e)}")
    
    logger.info(f"Killed {killed} processes matching {name}")
    return killed

def clean_stale_processes():
    """Kill any stale application processes"""
    logger.info("Cleaning up stale processes...")
    
    # List of process names to kill
    process_names = ["uvicorn", "streamlit", "job-tracker"]
    
    total_killed = 0
    for name in process_names:
        killed = kill_process_by_name(name)
        total_killed += killed
    
    logger.info(f"Cleaned up {total_killed} stale processes")
    return total_killed

def free_application_ports():
    """Ensure application ports are free"""
    logger.info("Ensuring application ports are free...")
    
    ports = [8001, 8501]  # API and Dashboard ports
    freed_count = 0
    
    for port in ports:
        if is_port_in_use(port):
            logger.info(f"Port {port} is in use, attempting to free...")
            if free_port(port):
                logger.info(f"Successfully freed port {port}")
                freed_count += 1
            else:
                logger.warning(f"Could not free port {port}")
        else:
            logger.info(f"Port {port} is already free")
    
    return freed_count

def check_postgres_processes():
    """Check for multiple PostgreSQL processes and clean up if needed"""
    logger.info("Checking PostgreSQL processes...")
    
    try:
        # Get all postgres processes
        postgres_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if 'postgres' in proc.name().lower() or any('postgres' in str(cmd).lower() for cmd in proc.cmdline() if cmd):
                    postgres_processes.append(proc)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Log the number of postgres processes found
        logger.info(f"Found {len(postgres_processes)} PostgreSQL processes")
        
        # If there are more than 8 postgres processes, this might be abnormal
        # Log details for all processes for analysis
        for proc in postgres_processes:
            try:
                logger.info(f"PostgreSQL process: PID={proc.pid}, Name={proc.name()}, Cmdline={proc.cmdline()}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # PostgreSQL typically has multiple processes for handling different tasks
        # but too many might indicate a problem
        if len(postgres_processes) > 10:
            logger.warning("Unusually high number of PostgreSQL processes detected")
            
            # Check connections to see what might be causing the issue
            check_postgres_connections()
            
        return len(postgres_processes)
    
    except Exception as e:
        logger.error(f"Error checking PostgreSQL processes: {str(e)}")
        return 0

def start_api_server():
    """Start the API server"""
    logger.info("Starting API server...")
    
    try:
        # Get the Python executable from the virtual environment
        if platform.system() == "Windows":
            python_exe = os.path.join("venv", "Scripts", "python.exe")
        else:
            python_exe = os.path.join("venv", "bin", "python")
        
        # Make sure the Python executable exists
        if not os.path.exists(python_exe):
            logger.error(f"Python executable not found at {python_exe}")
            return False
        
        # Start the API server
        cmd = [python_exe, "run.py", "api"]
        
        # Start the process in the background
        if platform.system() == "Windows":
            from subprocess import DEVNULL
            process = subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        
        logger.info(f"API server started with PID {process.pid}")
        
        # Wait a moment for the server to start
        time.sleep(5)
        
        # Check if the API is running by checking if the port is in use
        if is_port_in_use(8001):
            logger.info("API server is running")
            return True
        else:
            logger.error("API server failed to start")
            return False
        
    except Exception as e:
        logger.error(f"Error starting API server: {str(e)}")
        return False

def start_dashboard():
    """Start the dashboard"""
    logger.info("Starting dashboard...")
    
    try:
        # Get the Python executable from the virtual environment
        if platform.system() == "Windows":
            python_exe = os.path.join("venv", "Scripts", "python.exe")
        else:
            python_exe = os.path.join("venv", "bin", "python")
        
        # Make sure the Python executable exists
        if not os.path.exists(python_exe):
            logger.error(f"Python executable not found at {python_exe}")
            return False
        
        # Start the dashboard
        cmd = [python_exe, "run.py", "dashboard"]
        
        # Start the process in the background
        if platform.system() == "Windows":
            from subprocess import DEVNULL
            process = subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True)
        
        logger.info(f"Dashboard started with PID {process.pid}")
        
        # Wait a moment for the dashboard to start
        time.sleep(5)
        
        # Check if the dashboard is running by checking if the port is in use
        if is_port_in_use(8501):
            logger.info("Dashboard is running")
            return True
        else:
            logger.error("Dashboard failed to start")
            return False
        
    except Exception as e:
        logger.error(f"Error starting dashboard: {str(e)}")
        return False

def main():
    """Main entry point"""
    logger.info("=" * 80)
    logger.info("Starting clean start script...")
    logger.info("=" * 80)
    
    # Step 1: Check and clean up stale processes
    clean_stale_processes()
    
    # Step 2: Free up application ports
    free_application_ports()
    
    # Step 3: Check PostgreSQL processes
    check_postgres_processes()
    
    # Step 4: Start the API server
    api_success = start_api_server()
    
    # Wait a moment for the API to fully initialize
    time.sleep(10)
    
    # Step 5: Start the dashboard (only if API started successfully)
    dashboard_success = False
    if api_success:
        dashboard_success = start_dashboard()
    
    # Report results
    if api_success and dashboard_success:
        logger.info("Clean start completed successfully!")
        return 0
    else:
        logger.error("Clean start completed with errors:")
        logger.error(f"  API server: {'Success' if api_success else 'Failed'}")
        logger.error(f"  Dashboard: {'Success' if dashboard_success else 'Failed'}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
