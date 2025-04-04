#!/bin/bash
set -e

echo "Cleaning up duplicate processes..."
echo "=================================="

# Function to clean up duplicate processes
cleanup_duplicates() {
  process_name=$1
  process_pattern=$2
  service_name=$3

  # Count processes
  process_count=$(pgrep -f "$process_pattern" | wc -l)
  echo "Found $process_count $process_name processes"

  if [ "$process_count" -gt 1 ]; then
    echo "Terminating duplicate $process_name processes..."

    # If service name is provided, try to restart the service properly
    if [ ! -z "$service_name" ]; then
      echo "Attempting to restart $service_name service..."
      sudo systemctl restart $service_name || true
      sleep 2
    fi

    # If still have duplicates, keep only the newest process
    new_count=$(pgrep -f "$process_pattern" | wc -l)
    if [ "$new_count" -gt 1 ]; then
      newest_pid=$(pgrep -f "$process_pattern" | sort -n | tail -1)
      pgrep -f "$process_pattern" | grep -v $newest_pid | xargs -r kill
      echo "Kept $process_name process with PID $newest_pid"
    fi
  fi
}

# Clean up application processes
cleanup_duplicates "streamlit" "streamlit run dashboard.py" "job-tracker-dashboard"
cleanup_duplicates "uvicorn" "uvicorn main:app" "job-tracker-api"

# Check for multiple PostgreSQL instances
postgres_count=$(pgrep -f "postgres" | wc -l)
echo "Found $postgres_count PostgreSQL processes"

# PostgreSQL typically has multiple processes by design, but we can check for unusual numbers
if [ "$postgres_count" -gt 10 ]; then
  echo "Unusually high number of PostgreSQL processes detected"
  echo "Consider restarting PostgreSQL service if this is unexpected"
  echo "Run: sudo systemctl restart postgresql"
fi

# Check for multiple Nginx instances
nginx_count=$(pgrep -f "nginx" | wc -l)
echo "Found $nginx_count Nginx processes"

# Nginx typically has a master process and worker processes
if [ "$nginx_count" -gt 5 ]; then
  echo "Unusually high number of Nginx processes detected"
  echo "Restarting Nginx service..."
  sudo systemctl restart nginx || true
fi

echo "Process cleanup complete!"
echo ""
echo "Current running processes:"
ps aux | grep -E "streamlit|uvicorn|postgres|nginx" | grep -v grep
