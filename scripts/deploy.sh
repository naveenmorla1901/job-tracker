#!/bin/bash
set -e

echo "Starting deployment process..."

# Load environment variables
if [ -f .env ]; then
  export $(cat .env | grep -v '^#' | xargs)
fi

# Activate virtual environment or create if it doesn't exist
if [ ! -d "venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv venv
fi

source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install psutil for system monitoring
pip install psutil

# Run database migrations if needed
echo "Running database migrations..."
python run.py update_db

# Create logs directory if it doesn't exist
if [ ! -d "logs" ]; then
  echo "Creating logs directory..."
  mkdir -p logs
fi

echo "Setting up scheduled cleanup..."
python scheduled_cleanup.py > /dev/null 2>&1 &

echo "Setting up Nginx as reverse proxy..."
bash scripts/setup_nginx.sh

echo "Stopping any existing services..."
# Simple approach for initial deployment - use pkill with a fallback
pkill -f "uvicorn main:app" || echo "No API server running"
pkill -f "streamlit run dashboard.py" || echo "No dashboard running"

echo "Starting services..."
# Start services using nohup for initial deployment
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
nohup streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &

echo "Cleaning up old logs..."
python -c "from log_manager import cleanup_old_logs; cleanup_old_logs(days=2)"

# Set up git hooks
echo "Setting up git hooks..."
mkdir -p .git/hooks
cp -f .git/hooks/post-receive .git/hooks/post-receive.backup 2>/dev/null || true
cat > .git/hooks/post-receive << 'EOL'
#!/bin/bash
set -e

# Change to the repository directory
cd /home/ubuntu/job-tracker

# Pull the latest changes (this is needed since the hook fires before the actual update)
unset GIT_DIR
git pull origin main

# Restart the API and dashboard services
if systemctl is-active --quiet job-tracker-api.service; then
    echo "Restarting job-tracker-api.service..."
    sudo systemctl restart job-tracker-api.service
else
    echo "Starting job-tracker-api.service..."
    sudo systemctl start job-tracker-api.service
fi

if systemctl is-active --quiet job-tracker-dashboard.service; then
    echo "Restarting job-tracker-dashboard.service..."
    sudo systemctl restart job-tracker-dashboard.service
else
    echo "Starting job-tracker-dashboard.service..."
    sudo systemctl start job-tracker-dashboard.service
fi

echo "Services restarted successfully!"
EOL
chmod +x .git/hooks/post-receive

# Ensure we have the systemd service files installed and enabled
echo "Setting up systemd services..."
sudo cp scripts/job-tracker-api.service /etc/systemd/system/
sudo cp scripts/job-tracker-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable job-tracker-api.service
sudo systemctl enable job-tracker-dashboard.service

# Set up sudo permissions for the ubuntu user
echo "Setting up sudo permissions..."
sudo cp scripts/job-tracker-sudoers /etc/sudoers.d/job-tracker
sudo chmod 0440 /etc/sudoers.d/job-tracker

echo "Deployment completed successfully!"
echo "API running at: http://$(hostname -I | awk '{print $1}'):8000"
echo "Dashboard running at: http://$(hostname -I | awk '{print $1}'):8501"
