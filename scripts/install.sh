#!/bin/bash
set -e

# Simplified installation script - focus on getting things running first

echo "Setting up Job Tracker environment..."

# Update package lists
sudo apt update

# Install required packages (minimal set)
echo "Installing system dependencies..."
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib

# Configure PostgreSQL (basic setup)
echo "Setting up PostgreSQL..."
if ! sudo -u postgres psql -lqt | cut -d \| -f 1 | grep -qw job_tracker; then
  echo "Creating database..."
  sudo -u postgres psql -c "CREATE DATABASE job_tracker;"
  sudo -u postgres psql -c "CREATE USER job_tracker WITH PASSWORD 'job_tracker_password';"
  sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE job_tracker TO job_tracker;"
else
  echo "Database already exists."
fi

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

# Initialize database (basic initial setup)
echo "Database is ready for initialization. You can now run:"
echo "python run.py reset_db"

echo "Installation complete!"
echo "To start the application:"
echo "1. Initialize the database: python run.py reset_db"
echo "2. Start the API: python run.py api"
echo "3. Start the dashboard: python run.py dashboard"
