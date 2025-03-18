#!/bin/bash
set -e

echo "Running comprehensive fix for all issues..."
echo "========================================"

cd ~/job-tracker

# 1. Analyze current disk usage first
echo "Step 1: Analyzing disk usage..."
bash scripts/deep_disk_analysis.sh

# 2. Fix bcrypt issue
echo ""
echo "Step 2: Fixing bcrypt issue..."
source venv/bin/activate
pip install bcrypt==4.0.1 passlib==1.7.4
deactivate

# 3. Run deep clean
echo ""
echo "Step 3: Running deep clean..."
bash scripts/deep_clean.sh

# 4. Restart services properly
echo ""
echo "Step 4: Restarting services correctly..."
sudo systemctl stop job-tracker-api job-tracker-dashboard
sleep 2
sudo pkill -f "uvicorn main:app" || echo "No API processes to kill"
sudo pkill -f "streamlit run dashboard.py" || echo "No dashboard processes to kill"
sleep 2

echo "Starting services..."
sudo systemctl start job-tracker-api
sleep 2
sudo systemctl start job-tracker-dashboard
sleep 2

# 5. Run process cleanup to ensure everything is running properly
echo ""
echo "Step 5: Verifying processes..."
bash scripts/cleanup_processes.sh

# 6. Final status check
echo ""
echo "Step 6: Checking service status..."
sudo systemctl status job-tracker-api --no-pager
echo ""
sudo systemctl status job-tracker-dashboard --no-pager

echo ""
echo "All fixes applied!"
echo "Final disk usage:"
du -sh ~/job-tracker
echo ""
echo "Check the services are running properly at:"
echo "Dashboard: http://$(hostname -I | awk '{print $1}')"
echo "API: http://$(hostname -I | awk '{print $1}')/api"
