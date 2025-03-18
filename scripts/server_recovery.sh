#!/bin/bash
# This script is designed to run directly on the server to fix deployment issues
# Run it as: bash server_recovery.sh

set -e
echo "Server Recovery Script"
echo "======================"

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip nginx curl

# Change to job-tracker directory
cd ~/job-tracker

# Create completely fresh virtual environment
echo "Creating fresh virtual environment..."
rm -rf venv_new 2>/dev/null || true
python3 -m venv venv_new
source venv_new/bin/activate

# Verify Python
echo "Python version: $(python --version)"

# Install pip separately first
echo "Installing pip..."
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py --force-reinstall

# Verify pip
echo "Pip version: $(pip --version)"

# Install requirements
echo "Installing requirements..."
pip install wheel
pip install -r requirements.txt

# Verify critical packages
echo "Verifying uvicorn..."
which uvicorn
echo "Verifying streamlit..."
which streamlit

# Replace the broken venv with the new one
echo "Replacing virtual environment..."
mv venv venv_old 2>/dev/null || true
mv venv_new venv

# Configure Nginx
echo "Configuring Nginx..."
sudo cp scripts/job-tracker-nginx.conf /etc/nginx/sites-available/job-tracker
sudo ln -sf /etc/nginx/sites-available/job-tracker /etc/nginx/sites-enabled/job-tracker
sudo rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
sudo nginx -t && sudo systemctl restart nginx

# Start services manually (most reliable method)
echo "Starting services manually..."
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "streamlit run dashboard.py" 2>/dev/null || true

echo "Starting API..."
nohup ~/job-tracker/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001 > ~/job-tracker/api.log 2>&1 &

echo "Starting Dashboard..."
nohup ~/job-tracker/venv/bin/streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > ~/job-tracker/dashboard.log 2>&1 &

# Wait for services to start
echo "Waiting for services to start..."
sleep 10

# Verify services are running
echo "Checking API service..."
curl -s http://localhost:8001 || echo "API not responding"
echo "Checking Dashboard service..."
curl -s http://localhost:8501 || echo "Dashboard not responding"

echo "Recovery complete. Services should now be accessible at:"
echo "- Dashboard: http://$(hostname -I | awk '{print $1}'):8501"
echo "- API: http://$(hostname -I | awk '{print $1}'):8001"
echo "- Via Nginx: http://$(hostname -I | awk '{print $1}')"

echo "If you're still having issues, check the logs:"
echo "- API log: tail -f ~/job-tracker/api.log"
echo "- Dashboard log: tail -f ~/job-tracker/dashboard.log"
echo "- Nginx error log: sudo tail -f /var/log/nginx/error.log"
