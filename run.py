"""
Simple runner script for the Job Tracker
"""
import os
import sys
import subprocess
from port_utils import ensure_port_is_free, find_free_port

def main():
    """Main function to handle command line arguments"""
    # Configure usage message
    usage = """
Job Tracker Runner
-----------------
Usage: python run.py [command]

Commands:
  api          Start the API server
  dashboard    Start the dashboard
  purge        Delete job records older than 7 days
  cleanup      Clean up the database (remove duplicates, fix issues)
  reset_db     RESET DATABASE - Delete ALL data and start fresh
  quick_clean  Quickly remove test files without confirmation
  free         Free port 8000 if it's in use
  update_db    Update the database schema
  help         Show this help message
"""

    # Get command line arguments
    if len(sys.argv) < 2:
        print(usage)
        return

    command = sys.argv[1].lower()

    # Execute the appropriate command
    if command == "api":
        # Free port 8000 or find an alternative
        port = 8000
        if not ensure_port_is_free(port):
            port = find_free_port(8001)
            print(f"Port 8000 is not available. Using port {port} instead.")
        
        # Start the API server
        subprocess.run(["uvicorn", "main:app", "--reload", "--port", str(port)])
        
    elif command == "dashboard":
        # Start the dashboard
        subprocess.run(["streamlit", "run", "dashboard.py"])
        
    elif command == "purge":
        # Purge old records
        from purge_old_records import purge_old_records
        purge_old_records(days=7)
        
    elif command == "cleanup":
        # Clean up the database
        from cleanup import cleanup_database
        cleanup_database()
    
    elif command == "reset_db":
        # Reset database completely
        from reset_database import reset_database, validate_database_structure
        print("\nWARNING: This will delete ALL existing data in the job tracker database!")
        proceed = input("Are you sure you want to proceed? (yes/no): ")
        
        if proceed.lower() == "yes":
            reset_database()
            validate_database_structure()
            print("\nDatabase reset complete. You can now start the API server.")
        else:
            print("Operation canceled.")
        
    elif command == "quick_clean":
        # Quick cleanup of test files
        from quick_cleanup import quick_cleanup
        quick_cleanup()
        
    elif command == "free":
        # Free port 8000
        if ensure_port_is_free(8000):
            print("Port 8000 is now available.")
        else:
            print("Failed to free port 8000.")
            
    elif command == "update_db":
        # Update the database schema
        from update_db import run_migration_update
        run_migration_update()
        
    elif command == "help":
        print(usage)
        
    else:
        print(f"Unknown command: {command}")
        print(usage)

if __name__ == "__main__":
    main()
