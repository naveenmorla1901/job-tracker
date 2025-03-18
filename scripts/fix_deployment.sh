#!/bin/bash
set -e

echo "Running automated deployment fix..."

# Change to the job-tracker directory
cd ~/job-tracker || { echo "Error: job-tracker directory not found"; exit 1; }

# 1. Fix pip installation
echo "Step 1: Fixing pip installation..."
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python -m venv venv_new
source venv_new/bin/activate
python get-pip.py --force-reinstall pip==23.0.1
pip install -r requirements.txt
pip install psutil
deactivate

# 2. Fix venv
echo "Step 2: Replacing broken venv with new venv..."
rm -rf venv.broken 2>/dev/null || true
mv venv venv.broken 2>/dev/null || true
mv venv_new venv

# 3. Check Nginx configuration
echo "Step 3: Verifying Nginx configuration..."
sudo cp scripts/job-tracker-nginx.conf /etc/nginx/sites-available/job-tracker
sudo ln -sf /etc/nginx/sites-available/job-tracker /etc/nginx/sites-enabled/job-tracker || true
sudo nginx -t && sudo systemctl restart nginx

# 4. Update service files
echo "Step 4: Updating service files..."
sudo cp scripts/job-tracker-api.service /etc/systemd/system/
sudo cp scripts/job-tracker-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload

# 5. Restart services
echo "Step 5: Restarting services..."
sudo systemctl restart job-tracker-api
sudo systemctl restart job-tracker-dashboard

# 6. Verify services are running
echo "Step 6: Verifying services..."
echo "API service status:"
sudo systemctl status job-tracker-api --no-pager || true
echo "Dashboard service status:"
sudo systemctl status job-tracker-dashboard --no-pager || true

echo "Fix completed. Check if the application is now accessible at:"
echo "Dashboard: http://$(hostname -I | awk '{print $1}')"
echo "API: http://$(hostname -I | awk '{print $1}')/api"
