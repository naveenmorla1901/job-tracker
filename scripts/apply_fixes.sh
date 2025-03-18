#!/bin/bash
set -e

echo "Applying fixes for job tracker issues..."
echo "========================================"

# Change to project directory
cd ~/job-tracker

# 1. Fix JWT Secret Key issue
echo "1. Fixing JWT Secret Key issue..."
if ! grep -q "JWT_SECRET_KEY" .env 2>/dev/null; then
  # Generate a secure random key
  JWT_KEY=$(openssl rand -hex 32)
  echo "" >> .env
  echo "# Security (added by fix script)" >> .env
  echo "JWT_SECRET_KEY=$JWT_KEY" >> .env
  echo "JWT_EXPIRY_MINUTES=1440  # 24 hours" >> .env
  echo "  Added JWT_SECRET_KEY to .env file"
else
  echo "  JWT_SECRET_KEY already exists in .env file"
fi

# 2. Analyze disk usage
echo ""
echo "2. Analyzing disk usage..."
bash scripts/analyze_disk_usage.sh

# 3. Offer to clean up disk space
echo ""
echo "3. Disk space cleanup"
read -p "Would you like to run the disk space cleanup script? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  bash scripts/cleanup_disk_space.sh
else
  echo "Skipping disk space cleanup"
fi

# 4. Restart services to apply fixes
echo ""
echo "4. Restarting services to apply fixes..."
sudo systemctl restart job-tracker-api
sudo systemctl restart job-tracker-dashboard
sudo systemctl restart nginx

# Check if services started successfully
echo ""
echo "5. Verifying services..."
if systemctl is-active --quiet job-tracker-api; then
  echo "  API service is running"
else
  echo "  WARNING: API service failed to start. Check logs:"
  echo "  sudo journalctl -u job-tracker-api -n 50"
fi

if systemctl is-active --quiet job-tracker-dashboard; then
  echo "  Dashboard service is running"
else
  echo "  WARNING: Dashboard service failed to start. Check logs:"
  echo "  sudo journalctl -u job-tracker-dashboard -n 50"
fi

if systemctl is-active --quiet nginx; then
  echo "  Nginx service is running"
else
  echo "  WARNING: Nginx service failed to start. Check logs:"
  echo "  sudo journalctl -u nginx -n 50"
fi

echo ""
echo "Fix script completed successfully!"
echo "The application should now be accessible at:"
echo "  Dashboard: http://$(hostname -I | awk '{print $1}')"
echo "  API: http://$(hostname -I | awk '{print $1}')/api"
