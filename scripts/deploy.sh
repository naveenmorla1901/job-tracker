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

# Run database migrations if needed (commented out for initial deployment)
# echo "Running database migrations..."
# python run.py update_db

echo "Stopping any existing services..."
# Simple approach for initial deployment - use pkill with a fallback
pkill -f "uvicorn main:app" || echo "No API server running"
pkill -f "streamlit run dashboard.py" || echo "No dashboard running"

echo "Starting services..."
# Start services using nohup for initial deployment
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > api.log 2>&1 &
nohup streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &

echo "Deployment completed successfully!"
echo "API running at: http://$(hostname -I | awk '{print $1}'):8000"
echo "Dashboard running at: http://$(hostname -I | awk '{print $1}'):8501"
