#!/bin/bash
set -e

echo "Job Tracker Service Monitor"
echo "=========================="
echo ""

# Check service statuses
echo "1. Checking service status:"
echo "--------------------------"
echo "API Service:"
sudo systemctl status job-tracker-api --no-pager || echo "Service not running"
echo ""

echo "Dashboard Service:"
sudo systemctl status job-tracker-dashboard --no-pager || echo "Service not running"
echo ""

echo "Nginx Service:"
sudo systemctl status nginx --no-pager || echo "Service not running"
echo ""

# Check for running processes
echo "2. Running processes:"
echo "--------------------"
echo "Process counts:"
echo "- Uvicorn processes: $(pgrep -f 'uvicorn main:app' | wc -l)"
echo "- Streamlit processes: $(pgrep -f 'streamlit run dashboard.py' | wc -l)"
echo "- Postgres processes: $(pgrep -f 'postgres' | wc -l)"
echo "- Nginx processes: $(pgrep -f 'nginx' | wc -l)"
echo ""

echo "Process details:"
ps -ef | grep -E "uvicorn|streamlit|postgres|nginx" | grep -v grep
echo ""

# Check port usage
echo "3. Port usage:"
echo "-------------"
echo "Port 8001 (API):"
sudo netstat -tulpn | grep 8001 || echo "No process using port 8001"
echo ""

echo "Port 8501 (Dashboard):"
sudo netstat -tulpn | grep 8501 || echo "No process using port 8501"
echo ""

echo "Port 80 (HTTP):"
sudo netstat -tulpn | grep :80 || echo "No process using port 80"
echo ""

# Check recent logs
echo "4. Recent logs:"
echo "--------------"
echo "API logs (last 5 lines):"
tail -n 5 ~/job-tracker/api.log 2>/dev/null || echo "No API log file found"
echo ""

echo "Dashboard logs (last 5 lines):"
tail -n 5 ~/job-tracker/dashboard.log 2>/dev/null || echo "No dashboard log file found"
echo ""

echo "System logs for API service (last 5 lines):"
sudo journalctl -u job-tracker-api -n 5 --no-pager || echo "No API service logs"
echo ""

echo "System logs for Dashboard service (last 5 lines):"
sudo journalctl -u job-tracker-dashboard -n 5 --no-pager || echo "No dashboard service logs"
echo ""

# Check for scheduler issues
echo "5. Scheduler status:"
echo "------------------"
echo "Checking for scheduler processes:"
ps aux | grep -E "apscheduler|scheduler" | grep -v grep || echo "No scheduler processes found"
echo ""

echo "Scheduler logs from API (if available):"
grep -E "scheduler|scraper" ~/job-tracker/job_tracker.log | tail -n 10 || echo "No scheduler logs found"
echo ""

# Provide action options
echo "======================="
echo "RECOMMENDED ACTIONS:"
echo "======================="
echo "1. To restart all services:"
echo "   sudo systemctl restart job-tracker-api job-tracker-dashboard nginx"
echo ""
echo "2. To clear all processes and restart cleanly:"
echo "   bash ~/job-tracker/scripts/cleanup_processes.sh"
echo "   sudo systemctl restart job-tracker-api job-tracker-dashboard"
echo ""
echo "3. To check detailed disk usage:"
echo "   bash ~/job-tracker/scripts/analyze_disk_usage.sh"
echo ""
echo "4. To check detailed logs:"
echo "   tail -f ~/job-tracker/job_tracker.log"
echo "   tail -f ~/job-tracker/dashboard.log"
echo ""
echo "5. To apply all fixes and restart (recommended):"
echo "   bash ~/job-tracker/scripts/apply_fixes.sh"
echo ""
