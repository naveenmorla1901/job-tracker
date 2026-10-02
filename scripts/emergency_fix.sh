#!/bin/bash
# Fallback run by the deploy workflow when scripts/deploy.sh fails.
# Repairs dependencies in place and restarts the systemd units. It never starts
# its own nohup copies: those held ports 8001/8501 while the units (Restart=always)
# retried every 5s, filling dashboard.log with "Port 8501 is already in use".
set -e

echo "Running emergency deployment fix..."
echo "=============================="
cd ~/job-tracker

echo "Step 1: Installing system dependencies..."
sudo apt-get update || echo "apt-get update failed; continuing with cached package lists"
sudo apt-get install -y python3 python3-venv libxml2-dev libxslt1-dev zlib1g-dev nginx

echo "Step 2: Checking the virtual environment..."
# Rebuild only when the existing venv is actually broken
if [ ! -x venv/bin/python ] || ! venv/bin/python -m pip --version &>/dev/null; then
  echo "venv is missing or broken; recreating it..."
  rm -rf venv_old_backup
  [ -d venv ] && mv venv venv_old_backup
  python3 -m venv venv
  curl -sS https://bootstrap.pypa.io/pip/3.8/get-pip.py -o get-pip.py
  venv/bin/python get-pip.py --force-reinstall pip==23.3
  rm -f get-pip.py
fi
source venv/bin/activate
echo "Python in venv: $(python --version)"

echo "Step 3: Installing Python dependencies..."
python -m pip install -r requirements.txt

echo "Step 4: Setting up Nginx..."
bash scripts/setup_nginx.sh

echo "Step 5: Restarting services under systemd..."
sudo cp scripts/job-tracker-api.service /etc/systemd/system/
sudo cp scripts/job-tracker-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable job-tracker-api job-tracker-dashboard
sudo systemctl stop job-tracker-api job-tracker-dashboard || true
# Kill strays left by older deploys that started nohup copies
pkill -f "uvicorn main:app --host 0.0.0.0 --port 8001" || true
pkill -f "streamlit run dashboard.py" || true
sleep 3
sudo systemctl start job-tracker-api job-tracker-dashboard

echo "Step 6: Verifying services..."
sleep 5
systemctl --no-pager --lines=5 status job-tracker-api job-tracker-dashboard || true
curl -sf -o /dev/null http://localhost:8001/api/health && echo "API responding" || echo "API not responding"
curl -sf -o /dev/null http://localhost:8501 && echo "Dashboard responding" || echo "Dashboard not responding"

echo "Fix completed. Logs: ~/job-tracker/api.log, ~/job-tracker/dashboard.log"
