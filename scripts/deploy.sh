#!/bin/bash
set -e

echo "Starting deployment process..."

# Run the comprehensive project size cleanup script
echo "Running project size cleanup..."
if [ -f "scripts/cleanup_project_size.sh" ]; then
  # Run in non-interactive mode for automated deployments
  bash scripts/cleanup_project_size.sh <<< "y\ny\ny\ny\ny\ny"
else
  # Fallback to basic cleanup if the script doesn't exist
  echo "Cleanup script not found, using basic cleanup..."
  find . -maxdepth 1 -type d -name "venv_old*" -o -name "venv_backup*" -o -name "*_backup" | xargs rm -rf 2>/dev/null || true
  find . -name "*.pyc" -o -name "*.pyo" -o -name "__pycache__" | xargs rm -rf 2>/dev/null || true
  find . -name "*.log.old" -o -name "*.log.bak" | xargs rm -f 2>/dev/null || true

  # Truncate large log files
  for log_file in *.log; do
    if [ -f "$log_file" ] && [ $(du -b "$log_file" | cut -f1) -gt 5000000 ]; then
      echo "Truncating large log file: $log_file"
      tail -n 1000 "$log_file" > "${log_file}.new"
      mv "${log_file}.new" "$log_file"
    fi
  done
fi

# Clean up any running processes before deployment
echo "Cleaning up processes before deployment..."
if [ -f "scripts/cleanup_processes.sh" ]; then
  bash scripts/cleanup_processes.sh
fi

# Check Python availability
if ! command -v python3 &> /dev/null; then
  echo "Python 3 not found! Installing..."
  sudo apt-get update
  sudo apt-get install -y python3 python3-venv
fi

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

# Verify Python and pip are working
echo "Python version: $(python --version)"
echo "Pip version: $(pip --version || echo 'Pip not working properly')"

# Check if pip is broken and fix if needed
if ! pip --version &> /dev/null; then
  echo "Pip appears to be broken. Reinstalling..."
  curl -sS https://bootstrap.pypa.io/pip/3.8/get-pip.py -o get-pip.py
  python get-pip.py --force-reinstall pip==23.3
fi

# Install dependencies 1
echo "Installing dependencies..."

# Try pip upgrade with retry
for i in {1..3}; do
  python -m pip install --upgrade pip==23.3 && break || echo "Attempt $i failed. Retrying..."
  sleep 2
done

# Try requirements installation with retry
for i in {1..3}; do
  python -m pip install -r requirements.txt && break || echo "Attempt $i failed. Retrying..."
  sleep 2
done

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
# Better approach for stopping services - use both systemctl and direct process killing
# Try stopping via systemctl first
sudo systemctl stop job-tracker-api || echo "No API service to stop"
sudo systemctl stop job-tracker-dashboard || echo "No dashboard service to stop"

# Also kill any stray processes
pkill -f "uvicorn main:app" || echo "No API process running"
pkill -f "streamlit run dashboard.py" || echo "No dashboard running"

# Wait for processes to completely terminate
sleep 3

echo "Starting services..."
# Start services using nohup for initial deployment
nohup uvicorn main:app --host 0.0.0.0 --port 8001 > api.log 2>&1 &
nohup streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &

# Sleep to ensure services are up before continuing
sleep 5

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

# Stop the API and dashboard services first
if systemctl is-active --quiet job-tracker-api.service; then
    echo "Stopping job-tracker-api.service..."
    sudo systemctl stop job-tracker-api.service
fi

if systemctl is-active --quiet job-tracker-dashboard.service; then
    echo "Stopping job-tracker-dashboard.service..."
    sudo systemctl stop job-tracker-dashboard.service
fi

# Kill any remaining processes
pkill -f "uvicorn main:app" || echo "No API process running"
pkill -f "streamlit run dashboard.py" || echo "No dashboard running"

# Wait for processes to terminate
sleep 2

# Start the services
echo "Starting job-tracker-api.service..."
sudo systemctl start job-tracker-api.service

echo "Starting job-tracker-dashboard.service..."
sudo systemctl start job-tracker-dashboard.service

# Run the process cleanup script to ensure no duplicate processes
bash scripts/cleanup_processes.sh

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

# Final cleanup to ensure no duplicate processes and minimal disk usage
echo "Running final cleanup..."
bash scripts/cleanup_processes.sh

# Check project size after deployment
echo "Final project size:"
du -sh .

echo "Deployment completed successfully!"
echo "API running at: http://$(hostname -I | awk '{print $1}'):8001"
echo "Dashboard running at: http://$(hostname -I | awk '{print $1}'):8501"

echo "Note: If you experience issues with duplicate processes or increasing project size,"
echo "run 'bash scripts/maintenance.sh' to perform comprehensive maintenance."
