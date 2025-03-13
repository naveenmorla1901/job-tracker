#!/bin/bash
# Comprehensive script to fix API connection issues

set -e  # Exit on any error

echo "========================================"
echo "Job Tracker API Connection Comprehensive Fix"
echo "========================================"
echo ""

# Stop all services
echo "Stopping all services..."
sudo systemctl stop job-tracker-dashboard.service || echo "Dashboard service not running or not found"
sudo systemctl stop job-tracker-api.service || echo "API service not found"
sudo systemctl daemon-reload

# Check for and kill any lingering processes
echo "Checking for lingering processes..."
pkill -f "uvicorn main:app" || echo "No API process found"
pkill -f "streamlit run dashboard.py" || echo "No dashboard process found"

# Wait for processes to terminate
sleep 2

# Kill anything using our required ports
echo "Ensuring ports are available..."
sudo fuser -k 8001/tcp || echo "Port 8001 already available"
sudo fuser -k 8501/tcp || echo "Port 8501 already available"

# Back up and fix service files
echo "Fixing service configurations..."

# Backup original service files
mkdir -p /tmp/job-tracker-backup
cp /etc/systemd/system/job-tracker-api.service /tmp/job-tracker-backup/ || echo "No existing API service to backup"
cp /etc/systemd/system/job-tracker-dashboard.service /tmp/job-tracker-backup/ || echo "No existing dashboard service to backup"

# Create fresh service files with correct configs
cat > /tmp/job-tracker-api.service << 'EOL'
[Unit]
Description=Job Tracker API
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/job-tracker
Environment="PATH=/home/ubuntu/job-tracker/venv/bin"
Environment="PYTHONPATH=/home/ubuntu/job-tracker"
Environment="PORT=8001"
ExecStart=/home/ubuntu/job-tracker/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=job-tracker-api

[Install]
WantedBy=multi-user.target
EOL

cat > /tmp/job-tracker-dashboard.service << 'EOL'
[Unit]
Description=Job Tracker Dashboard
After=network.target job-tracker-api.service
Wants=job-tracker-api.service

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/job-tracker
Environment="PATH=/home/ubuntu/job-tracker/venv/bin"
Environment="PYTHONPATH=/home/ubuntu/job-tracker"
Environment="JOB_TRACKER_API_URL=http://localhost:8001/api"
ExecStart=/home/ubuntu/job-tracker/venv/bin/streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
SyslogIdentifier=job-tracker-dashboard

[Install]
WantedBy=multi-user.target
EOL

# Install the service files
sudo cp /tmp/job-tracker-api.service /etc/systemd/system/
sudo cp /tmp/job-tracker-dashboard.service /etc/systemd/system/

# Update the service files in the project for future deployments
cp /tmp/job-tracker-api.service ~/job-tracker/scripts/
cp /tmp/job-tracker-dashboard.service ~/job-tracker/scripts/

# Reload systemd configuration
echo "Reloading systemd configuration..."
sudo systemctl daemon-reload

# Enable the services to start at boot
echo "Enabling services to start at boot..."
sudo systemctl enable job-tracker-api.service
sudo systemctl enable job-tracker-dashboard.service

# Start API service first
echo "Starting API service..."
sudo systemctl start job-tracker-api.service

# Wait longer to ensure API is fully started
echo "Waiting 10 seconds for API to fully initialize..."
sleep 10

# Check if API service is running
if systemctl is-active --quiet job-tracker-api.service; then
    echo "✅ API service started successfully"
else
    echo "❌ API service failed to start!"
    echo "Checking logs:"
    sudo journalctl -u job-tracker-api.service -n 40
    echo ""
    echo "API service failed to start. Cannot proceed."
    exit 1
fi

# Test API connection
echo "Testing API connection..."
if curl -s http://localhost:8001/api > /dev/null; then
    echo "✅ API is responding at http://localhost:8001/api"
else
    echo "⚠️ API is not responding at http://localhost:8001/api"
    echo "Checking if API is responding at the root endpoint..."
    
    if curl -s http://localhost:8001/ > /dev/null; then
        echo "✅ API is responding at http://localhost:8001/"
        echo "The API is running but may not have the expected endpoints."
    else
        echo "❌ API is completely unresponsive."
        echo "Checking journalctl logs:"
        sudo journalctl -u job-tracker-api.service -n 40
        echo ""
        echo "Could not establish connection to API. Cannot proceed."
        exit 1
    fi
fi

# Start dashboard service
echo "Starting dashboard service..."
sudo systemctl start job-tracker-dashboard.service
sleep 3

# Check if dashboard service is running
if systemctl is-active --quiet job-tracker-dashboard.service; then
    echo "✅ Dashboard service started successfully"
else
    echo "❌ Dashboard service failed to start!"
    echo "Checking logs:"
    sudo journalctl -u job-tracker-dashboard.service -n 40
    echo ""
    echo "Dashboard service failed to start."
    exit 1
fi

# Update git hooks to ensure they're working correctly
echo "Updating git hook..."
cat > ~/job-tracker/.git/hooks/post-receive << 'EOL'
#!/bin/bash
set -e

# Change to the repository directory
cd /home/ubuntu/job-tracker

# Pull the latest changes
unset GIT_DIR
git pull origin main

# Give system time to complete the update
sleep 2

# Restart the API service first
echo "Restarting job-tracker-api.service..."
sudo systemctl restart job-tracker-api.service

# Wait for API to start before dashboard
echo "Waiting 10 seconds for API to fully initialize..."
sleep 10

# Restart the dashboard service
echo "Restarting job-tracker-dashboard.service..."
sudo systemctl restart job-tracker-dashboard.service

echo "Services restarted successfully!"
echo "API should be available at: http://localhost:8001/api"
echo "Dashboard should be available at: http://localhost:8501"
EOL

chmod +x ~/job-tracker/.git/hooks/post-receive

echo ""
echo "Comprehensive fix completed."
echo ""
echo "To verify the services are working correctly:"
echo "1. Check API status: sudo systemctl status job-tracker-api.service"
echo "2. Check dashboard status: sudo systemctl status job-tracker-dashboard.service"
echo "3. Access the dashboard at: http://YOUR_SERVER_IP:8501"
echo ""
echo "If issues persist, check logs with:"
echo "sudo journalctl -u job-tracker-api.service -n 100"
echo "sudo journalctl -u job-tracker-dashboard.service -n 100"
echo ""
echo "The system is now configured to restart services automatically on git push."
echo "========================================"
