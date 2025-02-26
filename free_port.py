"""
Utility to free port 8000 for the Job Tracker application
"""
from port_utils import ensure_port_is_free

if __name__ == "__main__":
    print("Attempting to free port 8000...")
    
    if ensure_port_is_free(8000):
        print("✅ Success: Port 8000 is now available")
    else:
        print("❌ Error: Could not free port 8000")
        print("Try manually stopping services or restarting your computer")
