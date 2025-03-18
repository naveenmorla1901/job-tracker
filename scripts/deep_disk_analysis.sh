#!/bin/bash
set -e

echo "Deep Disk Analysis"
echo "================="
echo ""

cd ~/job-tracker

# Overall project size
echo "Total project size:"
du -sh .

echo ""
echo "Analyzing Git repository:"
if [ -d ".git" ]; then
  echo "Git directory size:"
  du -sh .git
  
  echo ""
  echo "Git database size:"
  du -sh .git/objects
  
  echo ""
  echo "Git packfiles:"
  find .git/objects/pack -type f -name "*.pack" -exec du -sh {} \;
  
  echo ""
  echo "Git commit count:"
  git rev-list --count --all
fi

echo ""
echo "Looking for backup venv directories:"
find . -maxdepth 2 -type d -name "venv*" | while read dir; do
  du -sh "$dir"
done

echo ""
echo "Python cache directories:"
find . -type d -name "__pycache__" | while read dir; do
  du -sh "$dir"
done

echo ""
echo "Log file sizes:"
find . -type f -name "*.log" | xargs du -sh 2>/dev/null | sort -hr || echo "No log files found"

echo ""
echo "Old directories from fixes:"
find . -maxdepth 1 -type d -name "*_old*" -o -name "*_backup*" | while read dir; do
  du -sh "$dir"
done

echo ""
echo "Database size:"
sudo -u postgres psql -c "SELECT pg_size_pretty(pg_database_size('job_tracker')) AS job_tracker_size;"

echo ""
echo "Top 20 largest files/directories:"
find . -type f -o -type d | sort -k2 | xargs du -sh 2>/dev/null | sort -hr | head -20

echo ""
echo "Disk usage breakdown (top level):"
du -h --max-depth=1 . | sort -hr
