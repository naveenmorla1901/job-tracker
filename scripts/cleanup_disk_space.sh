#!/bin/bash
set -e

echo "Cleaning up disk space in job-tracker directory..."
echo "================================================="

# Change to project directory
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

echo "Current project size:"
du -sh .

# 1. Clean up old virtual environments (backup the current one first)
if confirm "Clean up old virtual environments?"; then
  echo "Current venv directory:"
  du -sh venv

  echo "Looking for other venv directories..."
  find . -maxdepth 1 -name "venv*" -type d | grep -v "^./venv$" || echo "No other venv directories found"

  if confirm "Remove old venv directories?"; then
    find . -maxdepth 1 -name "venv*" -type d | grep -v "^./venv$" | xargs rm -rf
    echo "Old venv directories removed"
  fi
fi

# 2. Clean up log files
if confirm "Clean up old log files?"; then
  echo "Log files:"
  find . -name "*.log" -type f -exec du -sh {} \; | sort -hr

  if confirm "Remove log files larger than 10MB?"; then
    find . -name "*.log" -type f -size +10M -exec rm {} \;
    echo "Large log files removed"
  fi
fi

# 3. Clean up Python cache files
if confirm "Clean up Python cache files?"; then
  echo "Python cache files:"
  find . -type d -name "__pycache__" -o -name "*.pyc" -o -name "*.pyo" | xargs du -ch

  if confirm "Remove Python cache files?"; then
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -name "*.pyc" -o -name "*.pyo" -exec rm -f {} +
    echo "Python cache files removed"
  fi
fi

# 4. Clean up temporary files
if confirm "Clean up temporary files?"; then
  echo "Temporary files:"
  find . -name "*.tmp" -o -name "*.bak" -o -name "*.swp" -o -name "*~" | xargs du -ch

  if confirm "Remove temporary files?"; then
    find . -name "*.tmp" -o -name "*.bak" -o -name "*.swp" -o -name "*~" -exec rm {} \;
    echo "Temporary files removed"
  fi
fi

# 5. Clean up Git repository
if [ -d ".git" ] && confirm "Clean up Git repository?"; then
  echo "Git directory size before cleanup:"
  du -sh .git

  echo "Running git gc..."
  git gc --aggressive --prune=now
  
  echo "Git directory size after cleanup:"
  du -sh .git
fi

# Show results
echo ""
echo "Cleanup complete!"
echo "New project size:"
du -sh .

echo ""
echo "If you still have disk space issues, run scripts/analyze_disk_usage.sh"
echo "to identify other large files or directories that could be removed."
