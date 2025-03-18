#!/bin/bash
set -e

echo "Job Tracker Maintenance Script"
echo "============================="
echo ""

# Function to ask for confirmation
confirm() {
  read -p "$1 (y/n): " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    return 0  # success
  else
    return 1  # failure
  fi
}

# Present menu of options
echo "Choose a maintenance action:"
echo "1. Process cleanup (remove duplicate processes)"
echo "2. Service restart (restart all services properly)"
echo "3. Disk cleanup (clean up unnecessary files)"
echo "4. System monitoring (check all services and logs)"
echo "5. Fix scheduler (fix any scheduling issues)"
echo "6. Run all fixes (comprehensive maintenance)"
echo "7. Exit"
echo ""

read -p "Enter your choice (1-7): " choice
echo ""

case $choice in
  1)
    # Process cleanup
    echo "Running process cleanup..."
    bash ~/job-tracker/scripts/cleanup_processes.sh
    ;;
    
  2)
    # Service restart
    echo "Restarting all services..."
    sudo systemctl stop job-tracker-api job-tracker-dashboard
    sleep 2
    pkill -f "uvicorn main:app" || echo "No API processes to kill"
    pkill -f "streamlit run dashboard.py" || echo "No dashboard processes to kill"
    sleep 2
    sudo systemctl start job-tracker-api
    sudo systemctl start job-tracker-dashboard
    sleep 2
    echo "Services restarted."
    ;;
    
  3)
    # Disk cleanup
    echo "Running disk cleanup..."
    bash ~/job-tracker/scripts/cleanup_disk_space.sh
    ;;
    
  4)
    # System monitoring
    echo "Running system monitoring..."
    bash ~/job-tracker/scripts/service_monitor.sh
    ;;
    
  5)
    # Fix scheduler
    echo "Fixing scheduler issues..."
    sudo systemctl restart job-tracker-api
    echo "API service restarted to reset scheduler."
    # Wait a moment and check if scheduler is running
    sleep 5
    ps aux | grep -E "apscheduler|scheduler" | grep -v grep || echo "No scheduler processes found"
    ;;
    
  6)
    # Run all fixes
    echo "Running all maintenance tasks..."
    
    echo "Step 1: Stopping all services..."
    sudo systemctl stop job-tracker-api job-tracker-dashboard || true
    sleep 2
    
    echo "Step 2: Cleaning up processes..."
    pkill -f "uvicorn main:app" || echo "No API processes to kill"
    pkill -f "streamlit run dashboard.py" || echo "No dashboard processes to kill"
    sleep 2
    
    echo "Step 3: Running disk cleanup..."
    if confirm "Run disk cleanup?"; then
      bash ~/job-tracker/scripts/cleanup_disk_space.sh
    else
      echo "Skipping disk cleanup"
    fi
    
    echo "Step 4: Updating service files..."
    # Copy updated service files
    sudo cp ~/job-tracker/job-tracker-api.service /etc/systemd/system/
    sudo cp ~/job-tracker/job-tracker-dashboard.service /etc/systemd/system/
    sudo systemctl daemon-reload
    
    echo "Step 5: Starting services..."
    sudo systemctl start job-tracker-api
    sleep 2
    sudo systemctl start job-tracker-dashboard
    sleep 2
    
    echo "Step 6: Verifying services..."
    sudo systemctl status job-tracker-api --no-pager || echo "API service failed to start"
    sudo systemctl status job-tracker-dashboard --no-pager || echo "Dashboard service failed to start"
    
    echo "Step 7: Checking processes..."
    ps aux | grep -E "uvicorn|streamlit" | grep -v grep
    
    echo "Maintenance completed!"
    ;;
    
  7)
    # Exit
    echo "Exiting maintenance script."
    exit 0
    ;;
    
  *)
    echo "Invalid choice. Please run again and select a valid option (1-7)."
    ;;
esac

echo ""
echo "Maintenance task completed."
echo "Check service status with: sudo systemctl status job-tracker-api job-tracker-dashboard"
