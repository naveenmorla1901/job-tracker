#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
  export $(cat .env | grep -v '^#' | xargs)
fi

echo "Starting deployment process..."

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

# Run database migrations if needed
echo "Running database migrations..."
python run.py update_db

# Restart services
echo "Restarting services..."

# Stop any existing API services
if pgrep -f "uvicorn main:app" > /dev/null; then
  echo "Stopping API server..."
  pkill -f "uvicorn main:app"
fi

# Stop any existing dashboard services
if pgrep -f "streamlit run dashboard.py" > /dev/null; then
  echo "Stopping dashboard..."
  pkill -f "streamlit run dashboard.py"
fi

# Start services using systemd if available, otherwise use nohup
if [ -f /etc/systemd/system/job-tracker-api.service ]; then
  echo "Restarting service via systemd..."
  sudo systemctl restart job-tracker-api
  sudo systemctl restart job-tracker-dashboard
else
  echo "Starting services via nohup..."
  nohup uvicorn main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
  nohup streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &
fi

echo "Deployment completed successfully!"
