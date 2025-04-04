#!/bin/bash
set -e

echo "Project Size Cleanup Script"
echo "=========================="
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

# Show initial project size
echo "Initial project size:"
du -sh .
echo ""

# 1. Clean up old virtual environments
echo "Checking for backup/old virtual environments..."
find . -maxdepth 2 -type d -name "venv*" | grep -v "^./venv$" | while read dir; do
  du -sh "$dir"
done

if confirm "Remove backup/old virtual environments?"; then
  find . -maxdepth 2 -type d -name "venv*" | grep -v "^./venv$" | xargs rm -rf
  echo "Backup virtual environments removed."
fi

# 2. Clean up Python cache files
echo ""
echo "Checking for Python cache files..."
find . -type d -name "__pycache__" | xargs du -ch 2>/dev/null || echo "No __pycache__ directories found"
find . -name "*.pyc" -o -name "*.pyo" | xargs du -ch 2>/dev/null || echo "No .pyc or .pyo files found"

if confirm "Remove Python cache files?"; then
  find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
  find . -name "*.pyc" -delete 2>/dev/null || true
  find . -name "*.pyo" -delete 2>/dev/null || true
  echo "Python cache files removed."
fi

# 3. Clean up log files
echo ""
echo "Checking for large log files..."
find . -name "*.log" -size +1M | xargs du -sh 2>/dev/null || echo "No large log files found"

if confirm "Rotate large log files (keep only last 1000 lines)?"; then
  find . -name "*.log" -size +1M | while read log_file; do
    echo "Rotating $log_file..."
    tail -n 1000 "$log_file" > "${log_file}.new"
    mv "${log_file}.new" "$log_file"
  done
  echo "Log files rotated."
fi

# 4. Clean up Git repository
if [ -d ".git" ]; then
  echo ""
  echo "Git repository size:"
  du -sh .git
  
  if confirm "Clean up Git repository?"; then
    echo "Running git gc..."
    git gc --aggressive --prune=now
    echo "Git repository cleaned."
    du -sh .git
  fi
fi

# 5. Clean up old backup directories
echo ""
echo "Checking for backup directories..."
find . -maxdepth 1 -type d -name "*_backup*" -o -name "*_old*" | xargs du -sh 2>/dev/null || echo "No backup directories found"

if confirm "Remove backup directories?"; then
  find . -maxdepth 1 -type d -name "*_backup*" -o -name "*_old*" | xargs rm -rf
  echo "Backup directories removed."
fi

# 6. Clean up temporary files
echo ""
echo "Checking for temporary files..."
find . -name "*.tmp" -o -name "*.bak" -o -name "*~" -o -name "*.swp" | xargs du -ch 2>/dev/null || echo "No temporary files found"

if confirm "Remove temporary files?"; then
  find . -name "*.tmp" -o -name "*.bak" -o -name "*~" -o -name "*.swp" -delete
  echo "Temporary files removed."
fi

# Show final project size
echo ""
echo "Final project size:"
du -sh .
echo ""
echo "Project size cleanup complete!"
