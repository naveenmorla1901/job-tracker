#!/bin/bash
set -e

echo "Fixing 502 Bad Gateway error..."

# 1. Check if Nginx is running
echo "Checking Nginx status..."
sudo systemctl status nginx --no-pager || {
  echo "Nginx is not running. Starting it..."
  sudo systemctl start nginx
}

# 2. Check if services are running
echo "Checking API service status..."
sudo systemctl status job-tracker-api --no-pager || {
  echo "API service is not running. Starting it..."
  sudo systemctl start job-tracker-api
}

echo "Checking Dashboard service status..."
sudo systemctl status job-tracker-dashboard --no-pager || {
  echo "Dashboard service is not running. Starting it..."
  sudo systemctl start job-tracker-dashboard
}

# 3. Check if ports are in use
echo "Checking if ports are in use..."
netstat -tulpn | grep -E '8001|8501' || {
  echo "Services are not listening on expected ports."
  
  # Start services manually if needed
  echo "Starting services manually..."
  cd ~/job-tracker
  source venv/bin/activate
  
  # Kill any existing processes
  pkill -f "uvicorn main:app" || echo "No API process to kill"
  pkill -f "streamlit run dashboard.py" || echo "No dashboard process to kill"
  
  # Start services
  nohup uvicorn main:app --host 0.0.0.0 --port 8001 > api.log 2>&1 &
  nohup streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > dashboard.log 2>&1 &
  
  echo "Services started manually."
}

# 4. Check Nginx configuration
echo "Checking Nginx configuration..."
sudo nginx -t || {
  echo "Nginx configuration is invalid. Fixing it..."
  cat > /tmp/job-tracker-nginx.conf << 'EOL'
server {
    listen 80;
    # Allow access via IP
    server_name _;

    # Dashboard at root
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    location /api {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
EOL
  sudo cp /tmp/job-tracker-nginx.conf /etc/nginx/sites-available/job-tracker
  sudo nginx -t && sudo systemctl restart nginx
}

# 5. Check logs for errors
echo "Checking API logs for errors..."
tail -n 20 ~/job-tracker/api.log || echo "No API log found"

echo "Checking Dashboard logs for errors..."
tail -n 20 ~/job-tracker/dashboard.log || echo "No dashboard log found"

echo "Checking Nginx error logs..."
sudo tail -n 20 /var/log/nginx/error.log || echo "No Nginx error log found"

echo "Fix completed. Check if the application is now accessible at:"
echo "Dashboard: http://$(hostname -I | awk '{print $1}')"
echo "API: http://$(hostname -I | awk '{print $1}')/api"
