#!/bin/bash
set -e

echo "Setting up Nginx for Job Tracker..."

# Check if Nginx is installed
if ! command -v nginx &> /dev/null; then
    echo "Installing Nginx..."
    sudo apt update
    sudo apt install -y nginx
fi

# Create Nginx configuration
CONFIG_PATH="/etc/nginx/sites-available/job-tracker"
echo "Creating Nginx configuration at $CONFIG_PATH..."

# Copy the configuration from project
sudo cp "$(dirname "$0")/job-tracker-nginx.conf" "$CONFIG_PATH"

# Enable the site
if [ ! -L "/etc/nginx/sites-enabled/job-tracker" ]; then
    echo "Enabling site configuration..."
    sudo ln -sf "$CONFIG_PATH" "/etc/nginx/sites-enabled/job-tracker"
fi

# Optionally remove default site
if [ -L "/etc/nginx/sites-enabled/default" ]; then
    echo "Disabling default site..."
    sudo rm -f "/etc/nginx/sites-enabled/default"
fi

# Test Nginx configuration
echo "Testing Nginx configuration..."
sudo nginx -t

# Restart Nginx
echo "Restarting Nginx..."
sudo systemctl restart nginx

echo "Nginx setup complete!"
echo "Job Tracker should now be accessible at:"
echo "  - Dashboard: http://$(hostname -I | awk '{print $1}')"
echo "  - API: http://$(hostname -I | awk '{print $1}')/api"
