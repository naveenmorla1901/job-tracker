#!/bin/bash
# This script tests if the post-receive Git hook is working correctly

echo "Testing post-receive Git hook..."

# Check if the hook exists
if [ ! -f .git/hooks/post-receive ]; then
    echo "ERROR: post-receive hook not found!"
    echo "Creating the hook now..."
    mkdir -p .git/hooks
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
    echo "Hook created successfully."
else
    echo "Hook found. Checking if it's executable..."
    if [ ! -x .git/hooks/post-receive ]; then
        echo "Hook is not executable. Setting executable permission..."
        chmod +x .git/hooks/post-receive
        echo "Permission set."
    else
        echo "Hook is executable."
    fi
fi

# Check if services are installed
echo "Checking systemd services..."
if ! systemctl list-unit-files | grep -q job-tracker-api.service; then
    echo "WARNING: job-tracker-api.service not found in systemd!"
    echo "Install it with: sudo cp scripts/job-tracker-api.service /etc/systemd/system/"
else
    echo "job-tracker-api.service is installed."
fi

if ! systemctl list-unit-files | grep -q job-tracker-dashboard.service; then
    echo "WARNING: job-tracker-dashboard.service not found in systemd!"
    echo "Install it with: sudo cp scripts/job-tracker-dashboard.service /etc/systemd/system/"
else
    echo "job-tracker-dashboard.service is installed."
fi

# Check sudo permissions
echo "Checking sudo permissions..."
if ! sudo -l | grep -q "job-tracker"; then
    echo "WARNING: sudo permissions for restarting services may not be properly configured!"
    echo "Run this to fix it: sudo cp scripts/job-tracker-sudoers /etc/sudoers.d/job-tracker && sudo chmod 0440 /etc/sudoers.d/job-tracker"
else
    echo "Sudo permissions appear to be configured."
fi

# Test run the hook in simulation mode
echo "Running hook in simulation mode (won't actually restart services)..."
echo "This is what would happen when you push changes:"
cat .git/hooks/post-receive | grep -v "systemctl restart" | grep -v "systemctl start"

echo ""
echo "Test completed. If there are any issues, run 'bash scripts/deploy.sh' to fix the setup."
echo "Remember to restart services in production with: sudo systemctl restart job-tracker-api.service && sudo systemctl restart job-tracker-dashboard.service"
