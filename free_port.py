"""
Utility to free up ports by killing processes
"""
import psutil
import logging
import socket
import sys
import time
import subprocess

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
                connections = proc.net_connections()
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
        _, alive = psutil.wait_procs([process], timeout=3)

        if process in alive:
            # If it's still alive, force kill
            process.kill()
            logger.info(f"Force killed process {process.pid}")
    except Exception as e:
        logger.error(f"Error killing process {process.pid}: {e}")
        return False

    return True

def free_port(port, kill=True, force=False):
    """
    Free up a port by killing processes using it

    Args:
        port: Port number to free
        kill: Whether to kill processes or just report them
        force: Whether to use force kill immediately

    Returns:
        True if port is free after operation, False otherwise
    """
    # Check if the port is in use
    if not is_port_in_use(port):
        logger.info(f"Port {port} is not in use")
        return True

    # Find processes using the port
    processes = find_processes_using_port(port)

    # If no processes found through psutil, try using netstat as a fallback
    if not processes:
        logger.info(f"No processes found using port {port} with psutil, trying netstat...")
        try:
            import subprocess
            # Run netstat to find processes using the port
            cmd = f"netstat -ano | findstr :{port}"
            output = subprocess.check_output(cmd, shell=True).decode('utf-8')

            # Parse the output to get PIDs
            pids = set()
            for line in output.splitlines():
                parts = line.strip().split()
                if len(parts) >= 5:
                    try:
                        pid = int(parts[-1])
                        pids.add(pid)
                    except ValueError:
                        pass

            # Get process objects for the PIDs
            for pid in pids:
                try:
                    proc = psutil.Process(pid)
                    processes.append(proc)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        except Exception as e:
            logger.error(f"Error using netstat fallback: {e}")

    if not processes:
        logger.info(f"No processes found using port {port}, but port is in use")
        # Try to kill any process that might be using the port with a more aggressive approach
        if force:
            logger.info("Using force approach to free the port...")
            try:
                # On Windows, use the restkill utility if available
                import subprocess
                subprocess.run(f"powershell -Command \"Stop-Process -Id (Get-NetTCPConnection -LocalPort {port}).OwningProcess -Force\"")
                time.sleep(2)
                if not is_port_in_use(port):
                    logger.info(f"Port {port} freed with PowerShell command")
                    return True
            except Exception as e:
                logger.error(f"Error using PowerShell to free port: {e}")
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
        if force:
            # Skip terminate and go straight to kill
            try:
                proc.kill()
                logger.info(f"Force killed process {proc.pid}")
                killed_count += 1
            except Exception as e:
                logger.error(f"Error force killing process {proc.pid}: {e}")
        else:
            if kill_process(proc):
                killed_count += 1

    logger.info(f"Killed {killed_count}/{len(processes)} processes using port {port}")

    # Check if the port is now free
    time.sleep(2)  # Give more time for the OS to release the port
    if is_port_in_use(port):
        if not force:
            # Try again with force
            logger.warning(f"Port {port} still in use, trying with force=True")
            return free_port(port, kill=True, force=True)
        else:
            logger.error(f"Port {port} is still in use after killing processes with force")
            return False

    logger.info(f"Port {port} is now free")
    return True

def free_application_ports(force=False):
    """Free all ports used by the application

    Args:
        force: Whether to use force kill immediately

    Returns:
        True if all ports are free, False otherwise
    """
    ports = [8001, 8501]  # API and Dashboard ports
    all_free = True

    for port in ports:
        if is_port_in_use(port):
            logger.info(f"Freeing port {port}...")
            if not free_port(port, force=force):
                all_free = False
        else:
            logger.info(f"Port {port} is already free")

    return all_free

if __name__ == "__main__":
    # Get port from command line argument or default to 8001
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001

    # Check if force flag is provided
    force = False
    if len(sys.argv) > 2 and sys.argv[2].lower() in ["force", "true", "1"]:
        force = True
        logger.info("Using force mode to free port")

    # Try to free the port
    if free_port(port, force=force):
        logger.info(f"Successfully freed port {port}")
        sys.exit(0)
    else:
        logger.error(f"Failed to free port {port}")
        sys.exit(1)
