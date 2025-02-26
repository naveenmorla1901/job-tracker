"""
Startup script for the Job Tracker application
"""
import os
import sys
import subprocess
import time
from port_utils import ensure_port_is_free, find_free_port

def start_api_server(port=8000):
    """Start the FastAPI server with the specified port"""
    print(f"\nStarting API server on port {port}...\n")
    
    # Use a different port if 8000 is not available
    if not ensure_port_is_free(port):
        new_port = find_free_port(8001)
        print(f"Port {port} is not available. Using port {new_port} instead.")
        port = new_port
        
    # Start the server
    server_process = subprocess.Popen(
        ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(port), "--reload"],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print(f"\nAPI server started on port {port}.")
    print(f"API documentation available at: http://localhost:{port}/docs")
    print(f"API endpoints available at: http://localhost:{port}/api/...")
    
    return server_process

def start_dashboard(port=8501):
    """Start the Streamlit dashboard with the specified port"""
    print(f"\nStarting dashboard on port {port}...\n")
    
    # Start the dashboard
    dashboard_process = subprocess.Popen(
        ["streamlit", "run", "dashboard.py", "--server.port", str(port)],
        cwd=os.path.dirname(os.path.abspath(__file__))
    )
    
    print(f"\nDashboard started on port {port}.")
    print(f"Dashboard available at: http://localhost:{port}")
    
    return dashboard_process

def main():
    """Main entry point for starting the application"""
    print("=" * 50)
    print("Job Tracker Application Starter")
    print("=" * 50)
    
    start_option = input("""
Choose what to start:
1. API server only
2. Dashboard only
3. Both API server and dashboard
4. Free port 8000 (if occupied)
Selection (1-4): """).strip()
    
    try:
        if start_option == "1":
            # Start API server only
            server_process = start_api_server()
            print("\nPress Ctrl+C to stop the server...")
            server_process.wait()
            
        elif start_option == "2":
            # Start dashboard only
            dashboard_process = start_dashboard()
            print("\nPress Ctrl+C to stop the dashboard...")
            dashboard_process.wait()
            
        elif start_option == "3":
            # Start both
            server_process = start_api_server()
            time.sleep(2)  # Wait for server to start
            dashboard_process = start_dashboard()
            
            print("\nBoth services are now running.")
            print("Press Ctrl+C to stop all services...")
            try:
                server_process.wait()
            except KeyboardInterrupt:
                print("\nStopping services...")
                server_process.terminate()
                dashboard_process.terminate()
                
        elif start_option == "4":
            # Free port 8000
            if ensure_port_is_free(8000):
                print("\nPort 8000 is now available.")
            else:
                print("\nFailed to free port 8000.")
                
        else:
            print("\nInvalid selection. Please enter 1, 2, 3, or 4.")
            
    except KeyboardInterrupt:
        print("\nOperation canceled by user.")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    main()
