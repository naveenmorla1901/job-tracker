"""
Utility functions for managing port conflicts
"""
import socket
import subprocess
import time
import sys
import os

def is_port_in_use(port):
    """Check if a port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_free_port(start_port=8000, max_port=9000):
    """Find a free port starting from start_port"""
    port = start_port
    while port < max_port:
        if not is_port_in_use(port):
            return port
        port += 1
    raise RuntimeError(f"No free ports found between {start_port} and {max_port}")

def free_port_windows(port):
    """Free a port on Windows by killing the process using it"""
    try:
        # Find the process using the port
        result = subprocess.run(
            f'netstat -ano | findstr :{port}',
            shell=True, 
            capture_output=True, 
            text=True
        )
        
        if not result.stdout.strip():
            print(f"No process found using port {port}")
            return True
            
        # Extract the PID
        lines = result.stdout.strip().split('\n')
        for line in lines:
            if f":{port}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                print(f"Process with PID {pid} is using port {port}")
                
                # Kill the process
                kill_result = subprocess.run(
                    f'taskkill /F /PID {pid}',
                    shell=True, 
                    capture_output=True, 
                    text=True
                )
                
                if kill_result.returncode == 0:
                    print(f"Successfully terminated process {pid}")
                    return True
                else:
                    print(f"Failed to terminate process: {kill_result.stderr}")
                    return False
        
        print(f"Could not find a listening process on port {port}")
        return False
        
    except Exception as e:
        print(f"Error freeing port {port}: {str(e)}")
        return False

def ensure_port_is_free(port):
    """Ensure a port is free, attempting to kill processes if needed"""
    if not is_port_in_use(port):
        print(f"Port {port} is already free")
        return True
        
    print(f"Port {port} is in use. Attempting to free it...")
    if free_port_windows(port):
        # Wait a moment for the port to be released
        time.sleep(1)
        if not is_port_in_use(port):
            print(f"Successfully freed port {port}")
            return True
        else:
            print(f"Port {port} is still in use after attempting to free it")
            return False
    
    return False

if __name__ == "__main__":
    # When run directly, try to free port 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8000
        
    if ensure_port_is_free(port):
        print(f"✓ Port {port} is now available")
    else:
        print(f"✗ Could not free port {port}")
