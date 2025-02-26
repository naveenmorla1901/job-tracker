#!/bin/bash
set -e

# This script helps set up the Job Tracker on a fresh Oracle Cloud instance

echo "Setting up Job Tracker environment..."

# Update package lists
sudo apt update

# Install required packages
echo "Installing system dependencies..."
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib nginx git

# Configure PostgreSQL
echo "Setting up PostgreSQL..."
sudo -u postgres psql -c "CREATE DATABASE job_tracker;"
sudo -u postgres psql -c "CREATE USER job_tracker WITH PASSWORD 'job_tracker_password';"
sudo -u postgres psql -c "ALTER ROLE job_tracker SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE job_tracker SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE job_tracker SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE job_tracker TO job_tracker;"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
  echo "Creating .env file..."
  cat > .env << EOF
DATABASE_URL=postgresql://job_tracker:job_tracker_password@localhost/job_tracker
ENVIRONMENT=production
EOF
fi

# Set up Python virtual environment
echo "Setting up Python environment..."
if [ ! -d "venv" ]; then
  python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Initialize database
echo "Initializing database..."
python run.py reset_db

# Set up systemd services
echo "Setting up systemd services..."
sudo cp scripts/job-tracker-api.service /etc/systemd/system/
sudo cp scripts/job-tracker-dashboard.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable job-tracker-api
sudo systemctl enable job-tracker-dashboard

# Set up Nginx
echo "Setting up Nginx..."
sudo cp scripts/job-tracker-nginx.conf /etc/nginx/sites-available/job-tracker
sudo ln -sf /etc/nginx/sites-available/job-tracker /etc/nginx/sites-enabled/
sudo systemctl restart nginx

# Start services
echo "Starting services..."
sudo systemctl start job-tracker-api
sudo systemctl start job-tracker-dashboard

echo "Installation complete! Access the dashboard at http://your-server-ip:8501"
