#!/bin/bash
set -e

echo "Running emergency deployment fix..."
echo "=============================="

# 1. Verify Python installation
echo "Step 1: Checking Python installation..."
if ! which python3 &>/dev/null; then
  echo "Python 3 not found. Installing..."
  sudo apt-get update
  sudo apt-get install -y python3 python3-venv
else
  echo "Python 3 is installed: $(python3 --version)"
fi

# 2. Create a fresh virtual environment
echo "Step 2: Creating fresh virtual environment..."
cd ~/job-tracker

# Backup old venv if it exists
if [ -d "venv" ]; then
  echo "Backing up old virtual environment..."
  mv venv venv_old_backup
fi

# Create new venv
echo "Creating new virtual environment with python3..."
python3 -m venv venv
source venv/bin/activate

# Verify Python in venv
echo "Python in venv: $(python --version)"
echo "Pip in venv: $(pip --version || echo 'Pip not working')"

# 3. Fix pip
echo "Step 3: Reinstalling pip..."
curl https://bootstrap.pypa.io/pip/3.8/get-pip.py -o get-pip.py
python get-pip.py --force-reinstall pip==23.3

# Verify pip installation
which pip
pip --version

# 4. Install dependencies
echo "Step 4: Installing dependencies..."
pip install -r requirements.txt

# Verify core dependencies are installed
echo "Verifying uvicorn installation..."
which uvicorn || echo "uvicorn not in PATH"
echo "Verifying streamlit installation..."
which streamlit || echo "streamlit not in PATH"

# 5. Setup Nginx
echo "Step 5: Setting up Nginx..."
sudo apt-get install -y nginx
sudo cp scripts/job-tracker-nginx.conf /etc/nginx/sites-available/job-tracker
sudo ln -sf /etc/nginx/sites-available/job-tracker /etc/nginx/sites-enabled/job-tracker
# Remove default site if it exists
sudo rm -f /etc/nginx/sites-enabled/default
# Test and reload nginx
sudo nginx -t && sudo systemctl restart nginx

# 6. Setup services
echo "Step 6: Setting up systemd services..."
sudo cp scripts/job-tracker-api.service /etc/systemd/system/
sudo cp scripts/job-tracker-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl restart job-tracker-api || echo "Failed to restart API service"
sudo systemctl restart job-tracker-dashboard || echo "Failed to restart Dashboard service"

# 7. Start services manually if systemd fails
echo "Step 7: Starting services manually as fallback..."
cd ~/job-tracker
source venv/bin/activate

# Kill any existing processes
pkill -f "uvicorn main:app" || echo "No API process to kill"
pkill -f "streamlit run dashboard.py" || echo "No dashboard process to kill"

# Start services
nohup venv/bin/uvicorn main:app --host 0.0.0.0 --port 8001 > api.log 2>&1 &
nohup venv/bin/streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &

echo "Services started. Waiting to verify..."
sleep 5

# 8. Verify services
echo "Step 8: Verifying services..."
ps aux | grep uvicorn
ps aux | grep streamlit
curl -s http://localhost:8001/api/docs || echo "API not responding"
curl -s http://localhost:8501 || echo "Dashboard not responding"

echo "Fix completed. The application should now be accessible at:"
echo "Dashboard: http://$(hostname -I | awk '{print $1}')"
echo "API: http://$(hostname -I | awk '{print $1}')/api"
echo ""
echo "If you're still having issues, please check the logs:"
echo "API log: ~/job-tracker/api.log"
echo "Dashboard log: ~/job-tracker/dashboard.log"
echo "Nginx error log: sudo tail -f /var/log/nginx/error.log"
