"""
Utility to free up ports by killing processes
"""
import os
import psutil
import logging
import socket
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("job_tracker.log")
    ]
)
logger = logging.getLogger("job_tracker.free_port")

def is_port_in_use(port):
    """Check if a port is in use"""
    try:
        # Try to bind to the port
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("0.0.0.0", port))
        s.close()
        return False
    except OSError:
        # If we can't bind, the port is in use
        return True

def find_processes_using_port(port):
    """Find all processes using a specific port"""
    processes = []
    
    try:
        # Loop through all processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                # Get connections for this process
                connections = proc.connections()
                for conn in connections:
                    # Check if this connection uses our port
                    if conn.laddr.port == port:
                        processes.append(proc)
                        break
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                # Skip processes we can't access
                pass
    except Exception as e:
        logger.error(f"Error while searching for processes: {e}")
    
    return processes

def kill_process(process):
    """Kill a process by PID"""
    try:
        process.terminate()
        logger.info(f"Sent termination signal to process {process.pid} ({process.name()})")
        
        # Wait for it to terminate gracefully
        gone, alive = psutil.wait_procs([process], timeout=3)
        
        if process in alive:
            # If it's still alive, force kill
            process.kill()
            logger.info(f"Force killed process {process.pid}")
    except Exception as e:
        logger.error(f"Error killing process {process.pid}: {e}")
        return False
    
    return True

def free_port(port, kill=True):
    """
    Free up a port by killing processes using it
    
    Args:
        port: Port number to free
        kill: Whether to kill processes or just report them
        
    Returns:
        True if port is free after operation, False otherwise
    """
    # Check if the port is in use
    if not is_port_in_use(port):
        logger.info(f"Port {port} is not in use")
        return True
    
    # Find processes using the port
    processes = find_processes_using_port(port)
    
    if not processes:
        logger.info(f"No processes found using port {port}, but port is in use")
        return False
    
    # Log the processes found
    logger.info(f"Found {len(processes)} processes using port {port}:")
    for proc in processes:
        logger.info(f"  PID {proc.pid}: {proc.name()} - {' '.join(proc.cmdline())}")
    
    if not kill:
        # Just report, don't kill
        return False
    
    # Kill each process
    killed_count = 0
    for proc in processes:
        if kill_process(proc):
            killed_count += 1
    
    logger.info(f"Killed {killed_count}/{len(processes)} processes using port {port}")
    
    # Check if the port is now free
    time.sleep(1)  # Give a moment for the OS to release the port
    if is_port_in_use(port):
        logger.error(f"Port {port} is still in use after killing processes")
        return False
    
    logger.info(f"Port {port} is now free")
    return True

def free_application_ports():
    """Free all ports used by the application"""
    ports = [8001, 8501]  # API and Dashboard ports
    
    for port in ports:
        if is_port_in_use(port):
            logger.info(f"Freeing port {port}...")
            free_port(port)
        else:
            logger.info(f"Port {port} is already free")

if __name__ == "__main__":
    # Get port from command line argument or default to 8001
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    free_port(port)
