#!/bin/bash
set -e

echo "Deep Cleaning Script"
echo "================="
echo ""

cd ~/job-tracker

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

# Show initial disk usage
echo "Initial project size:"
du -sh .
echo ""

# 1. Git cleanup
if [ -d ".git" ] && confirm "Clean Git repository (this is safe)?"; then
  echo "Cleaning Git repository..."
  git gc --aggressive --prune=now
  
  # Verify size after cleaning
  echo "Git size after cleaning:"
  du -sh .git
fi

# 2. Remove backup virtual environments
echo ""
echo "Backup virtual environments:"
find . -maxdepth 2 -type d -name "venv*" | grep -v "^./venv$" | while read dir; do
  du -sh "$dir"
done

if confirm "Remove backup virtual environments?"; then
  find . -maxdepth 2 -type d -name "venv*" | grep -v "^./venv$" | xargs rm -rf
  echo "Backup virtual environments removed."
fi

# 3. Python cache cleanup
echo ""
if confirm "Clean Python cache files?"; then
  echo "Removing Python cache files..."
  find . -type d -name "__pycache__" -exec rm -rf {} +
  find . -name "*.pyc" -delete
  find . -name "*.pyo" -delete
  echo "Python cache files removed."
fi

# 4. Log rotation
echo ""
echo "Log files:"
find . -type f -name "*.log" | xargs du -sh 2>/dev/null || echo "No log files found"

if confirm "Rotate log files (truncate to last 1000 lines)?"; then
  find . -type f -name "*.log" | while read log_file; do
    if [ -f "$log_file" ]; then
      # Create backup first
      cp "$log_file" "${log_file}.bak"
      # Get the last 1000 lines
      tail -n 1000 "$log_file" > "${log_file}.new"
      # Replace the original
      mv "${log_file}.new" "$log_file"
      echo "Rotated: $log_file"
    fi
  done
  echo "Log files rotated."

  # Ask if user wants to remove backups
  if confirm "Remove log file backups?"; then
    find . -name "*.log.bak" -delete
    echo "Log file backups removed."
  fi
fi

# 5. Old backups & fix directories
echo ""
echo "Old backup directories:"
find . -maxdepth 1 -type d -name "*_old*" -o -name "*_backup*" | while read dir; do
  du -sh "$dir"
done

if confirm "Remove old backup directories?"; then
  find . -maxdepth 1 -type d -name "*_old*" -o -name "*_backup*" | xargs rm -rf
  echo "Old backup directories removed."
fi

# 6. Fix bcrypt issue
echo ""
if confirm "Fix bcrypt compatibility issue?"; then
  source venv/bin/activate
  pip uninstall -y bcrypt passlib
  pip install bcrypt==4.0.1 passlib==1.7.4
  echo "Bcrypt and passlib reinstalled with compatible versions."
fi

# 7. Clean up any stray processes
echo ""
if confirm "Clean up stray processes?"; then
  bash scripts/cleanup_processes.sh
fi

# Final disk usage
echo ""
echo "Final project size:"
du -sh .
echo ""
echo "Disk usage breakdown:"
du -h --max-depth=1 . | sort -hr
echo ""
echo "Deep cleaning completed."
