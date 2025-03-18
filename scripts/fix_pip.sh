#!/bin/bash
set -e

echo "Fixing pip installation issues..."

# Make sure we're in the right directory
cd ~/job-tracker

# Check if venv exists
if [ ! -d "venv" ]; then
  echo "Creating new virtual environment..."
  python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Try to fix pip by reinstalling it completely
echo "Reinstalling pip..."
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py --force-reinstall pip==23.0.1

# Verify pip is working
echo "Verifying pip installation..."
which pip
pip --version

# Clean pip cache
echo "Cleaning pip cache..."
pip cache purge

# Install dependencies
echo "Installing project dependencies..."
pip install -r requirements.txt

echo "Pip fix completed."
echo "Now you can run the deployment script:"
echo "bash ~/job-tracker/scripts/deploy.sh"
