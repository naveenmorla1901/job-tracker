#!/bin/bash
set -e

echo "Analyzing disk usage in job-tracker directory..."
echo "================================================"

# Change to project directory
cd ~/job-tracker

# Overall project size
echo "Total project size:"
du -sh .

echo ""
echo "Top-level directory sizes:"
du -sh --max-depth=1 . | sort -hr

echo ""
echo "Large hidden directories:"
du -sh .[^.]* 2>/dev/null | grep -E "M|G" | sort -hr || echo "No large hidden directories found"

echo ""
echo "Checking for multiple virtual environments:"
find . -name "venv*" -type d | while read -r dir; do
  size=$(du -sh "$dir" | cut -f1)
  echo "$size - $dir"
done

echo ""
echo "Checking for large log files:"
find . -name "*.log" -type f -exec du -sh {} \; | sort -hr | head -10

echo ""
echo "Checking database size:"
if command -v psql &> /dev/null; then
  # Get database size if PostgreSQL is installed
  echo "PostgreSQL database sizes:"
  sudo -u postgres psql -c "SELECT pg_database.datname, pg_size_pretty(pg_database_size(pg_database.datname)) AS size FROM pg_database ORDER BY pg_database_size(pg_database.datname) DESC;"
else
  echo "PostgreSQL client not installed, can't check database size"
fi

echo ""
echo "Checking for unusually large files (>10MB):"
find . -type f -size +10M -exec du -sh {} \; | sort -hr

echo ""
echo "Checking Git repository size:"
if [ -d ".git" ]; then
  echo "Git directory size:"
  du -sh .git
  
  echo "Largest Git objects:"
  git verify-pack -v .git/objects/pack/*.idx | sort -k 3 -n | tail -10 | cat
fi

echo ""
echo "Analysis complete!"
echo "If you find unnecessary large files or old virtual environments,"
echo "you can remove them to free up space."
