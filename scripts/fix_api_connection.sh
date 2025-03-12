#!/bin/bash
# Script to fix API connection issues

echo "Job Tracker API Connection Fix"
echo "============================="
echo ""

# Stop both services
echo "Stopping services..."
sudo systemctl stop job-tracker-dashboard.service
sudo systemctl stop job-tracker-api.service

# Check if anything is using port 8001
echo "Checking for processes using port 8001..."
if lsof -i :8001 > /dev/null 2>&1; then
    echo "Found process using port 8001. Attempting to kill it..."
    sudo lsof -i :8001 -t | xargs sudo kill -9
    sleep 2
else
    echo "No process found using port 8001."
fi

# Make sure the API service file uses port 8001
echo "Updating API service configuration..."
if ! grep -q "port 8001" /etc/systemd/system/job-tracker-api.service; then
    # If using the run.py version
    if grep -q "run.py api" /etc/systemd/system/job-tracker-api.service; then
        echo "Service uses run.py - this should now correctly use port 8001"
    else
        # If using direct uvicorn command
        sudo sed -i 's/--port [0-9]\+/--port 8001/g' /etc/systemd/system/job-tracker-api.service
        echo "Updated API service port to 8001"
    fi
else
    echo "API service already configured for port 8001"
fi

# Reload systemd to apply changes
echo "Reloading systemd configuration..."
sudo systemctl daemon-reload

# Start services in correct order
echo "Starting API service..."
sudo systemctl start job-tracker-api.service
sleep 3  # Give API time to start before dashboard

echo "Checking API service status..."
if systemctl is-active --quiet job-tracker-api.service; then
    echo "✅ API service started successfully"
else
    echo "❌ API service failed to start!"
    echo "Checking logs:"
    sudo journalctl -u job-tracker-api.service -n 20
    echo ""
    echo "Fix failed. Please check the logs for more information."
    exit 1
fi

# Test API connectivity before starting dashboard
echo "Testing API connectivity..."
if curl -s http://localhost:8001/api/health > /dev/null 2>&1; then
    echo "✅ API is responding correctly"
else
    echo "⚠️ API is not responding at http://localhost:8001/api/health"
    echo "Proceeding anyway, but dashboard might not connect."
fi

echo "Starting dashboard service..."
sudo systemctl start job-tracker-dashboard.service
sleep 2

echo "Checking dashboard service status..."
if systemctl is-active --quiet job-tracker-dashboard.service; then
    echo "✅ Dashboard service started successfully"
else
    echo "❌ Dashboard service failed to start!"
    echo "Checking logs:"
    sudo journalctl -u job-tracker-dashboard.service -n 20
fi

echo ""
echo "Fix completed. Open your dashboard and check if it connects to the API."
echo "If issues persist, run: bash scripts/diagnose_services.sh"
echo ""
