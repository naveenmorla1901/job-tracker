#!/bin/bash
# Service Diagnostic Tool for Job Tracker

echo "========================================"
echo "Job Tracker Service Diagnostic Tool"
echo "========================================"
echo ""

# Check if API service is running
echo "Checking API service status..."
if systemctl is-active --quiet job-tracker-api.service; then
    echo "✅ API service is running"
else
    echo "❌ API service is NOT running!"
    echo "   Try starting it with: sudo systemctl start job-tracker-api.service"
    echo "   Check logs with: sudo journalctl -u job-tracker-api.service"
fi

# Check if Dashboard service is running
echo ""
echo "Checking Dashboard service status..."
if systemctl is-active --quiet job-tracker-dashboard.service; then
    echo "✅ Dashboard service is running"
else
    echo "❌ Dashboard service is NOT running!"
    echo "   Try starting it with: sudo systemctl start job-tracker-dashboard.service"
    echo "   Check logs with: sudo journalctl -u job-tracker-dashboard.service"
fi

# Check port 8001 (API)
echo ""
echo "Checking if port 8001 is in use..."
if netstat -tuln | grep -q ":8001 "; then
    echo "✅ Port 8001 is in use (expected for API)"
    echo "   Process using port 8001:"
    netstat -tuln | grep ":8001 "
else
    echo "❌ Port 8001 is NOT in use! API is not running on the expected port."
    echo "   This might be why the dashboard can't connect to the API."
fi

# Check port 8501 (Dashboard)
echo ""
echo "Checking if port 8501 is in use (Dashboard)..."
if netstat -tuln | grep -q ":8501 "; then
    echo "✅ Port 8501 is in use (expected for Dashboard)"
    echo "   Process using port 8501:"
    netstat -tuln | grep ":8501 "
else
    echo "❌ Port 8501 is NOT in use! Dashboard is not running on the expected port."
fi

# Check API connectivity
echo ""
echo "Testing API connectivity..."
if curl -s http://localhost:8001/api/health > /dev/null; then
    echo "✅ API is responding at http://localhost:8001/api/health"
else
    echo "❌ Cannot connect to API at http://localhost:8001/api/health"
    echo "   This might be why the dashboard is showing a connection error."
fi

# Check services configuration
echo ""
echo "Checking service configuration files..."
if grep -q "port 8001" /etc/systemd/system/job-tracker-api.service; then
    echo "✅ API service is configured to use port 8001"
else
    echo "❌ API service might not be configured to use port 8001!"
    echo "   API port in service file:"
    grep -i "port" /etc/systemd/system/job-tracker-api.service || echo "   No port configuration found!"
fi

# Check if dashboard is configured to use the correct API URL
if grep -q "8001/api" /etc/systemd/system/job-tracker-dashboard.service; then
    echo "✅ Dashboard is configured to use API at port 8001"
else
    echo "❌ Dashboard might be using the wrong API port!"
    echo "   API URL in dashboard service file:"
    grep -i "JOB_TRACKER_API_URL" /etc/systemd/system/job-tracker-dashboard.service || echo "   No API URL configuration found!"
fi

echo ""
echo "Diagnostic complete!"
echo ""
echo "If you need to fix the services:"
echo "1. Ensure the API service uses port 8001:"
echo "   sudo systemctl stop job-tracker-api.service"
echo "   sudo systemctl stop job-tracker-dashboard.service"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl start job-tracker-api.service"
echo "   sudo systemctl start job-tracker-dashboard.service"
echo ""
echo "2. Check the logs for errors:"
echo "   sudo journalctl -u job-tracker-api.service -n 50"
echo "   sudo journalctl -u job-tracker-dashboard.service -n 50"
echo ""
echo "3. If services won't start, check for port conflicts:"
echo "   sudo lsof -i :8001"
echo "   sudo lsof -i :8501"
echo ""
echo "4. Kill any conflicting processes:"
echo "   sudo kill <PID>"
echo ""
echo "========================================"
