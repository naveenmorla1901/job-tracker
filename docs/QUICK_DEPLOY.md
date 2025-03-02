# Quick Deployment Guide for Oracle Cloud

This is a simplified guide for getting the Job Tracker up and running on Oracle Cloud quickly.

## 1. Oracle Cloud Setup

1. **Sign up for Oracle Cloud Free Tier**:
   - Go to [https://www.oracle.com/cloud/free/](https://www.oracle.com/cloud/free/)
   - Complete the registration process

2. **Create a Compute Instance**:
   - From the Oracle Cloud dashboard, go to "Compute" → "Instances"
   - Click "Create Instance"
   - Name: `job-tracker`
   - Image: Ubuntu 20.04 or newer
   - Shape: VM.Standard.E2.1.Micro (free tier eligible)
   - Network: Create new VCN and subnet (use the defaults)
   - Add SSH Key: Upload your public key or generate a new one
   - Click "Create"

3. **Configure Security**:
   - After the instance is created, click on its name
   - On the left menu, click "Virtual Cloud Network"
   - Click on your VCN name
   - Click "Security Lists" then the default security list
   - Click "Add Ingress Rules" and add:
     - Port 8000 (API)
     - Port 8501 (Dashboard)
     - Port 22 (SSH - should already be open)

## 2. Deploy the Application

### Manual Deployment

1. **Connect to your instance**:
   ```bash
   ssh ubuntu@<your-instance-ip>
   ```

2. **Install Git and clone the repository**:
   ```bash
   sudo apt update
   sudo apt install -y git
   git clone https://github.com/yourusername/job-tracker.git
   cd job-tracker
   ```

3. **Run the installer script**:
   ```bash
   bash scripts/install.sh
   ```

4. **Create a logs directory**:
   ```bash
   mkdir -p ~/job-tracker/logs
   ```

5. **Initialize the database**:
   ```bash
   source venv/bin/activate
   python run.py reset_db
   ```

6. **Start the application**:
   ```bash
   # Using the runner script
   nohup python run.py api &
   nohup python run.py dashboard &
   
   # Or directly with the underlying commands
   nohup uvicorn main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
   nohup streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > logs/dashboard.log 2>&1 &
   ```

7. **Access your application**:
   - API: `http://<your-instance-ip>:8000`
   - API Docs: `http://<your-instance-ip>:8000/docs`
   - Dashboard: `http://<your-instance-ip>:8501`

### Automated Deployment with GitHub Actions

1. **Generate a deployment SSH key pair**:
   ```bash
   # On your local machine
   ssh-keygen -t ed25519 -f deployment_key -N ""
   ```

2. **Add the public key to your server**:
   ```bash
   # Connect to your server
   ssh ubuntu@<your-instance-ip>
   
   # Add the public key (replace with your actual public key content)
   echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5... deployment_key" >> ~/.ssh/authorized_keys
   ```

3. **Add GitHub Repository Secrets**:
   - Go to your GitHub repository
   - Click "Settings" → "Secrets and variables" → "Actions"
   - Add these secrets:
     - `DEPLOYMENT_PRIVATE_KEY`: Your private SSH key content (from `deployment_key` file)
     - `ORACLE_KNOWN_HOSTS`: Run `ssh-keyscan <your-instance-ip>` locally and paste the output

4. **Ensure your GitHub workflow file is correct**:
   ```yaml
   # .github/workflows/deploy.yml should look like this:
   name: Deploy to Oracle Cloud

   on:
     push:
       branches: [ main ]
     workflow_dispatch:

   jobs:
     deploy:
       runs-on: ubuntu-latest
       
       steps:
       - name: Checkout code
         uses: actions/checkout@v3
       
       - name: Set up Python
         uses: actions/setup-python@v4
         with:
           python-version: '3.10'
           
       - name: Install dependencies
         run: |
           python -m pip install --upgrade pip
           if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
       
       - name: Install SSH key using proper action
         uses: webfactory/ssh-agent@v0.8.0
         with:
           ssh-private-key: ${{ secrets.DEPLOYMENT_PRIVATE_KEY }}
       
       - name: Add host key
         run: |
           mkdir -p ~/.ssh
           ssh-keyscan -t ed25519 <your-instance-ip> >> ~/.ssh/known_hosts
           chmod 644 ~/.ssh/known_hosts
       
       - name: Test SSH connection
         run: |
           ssh -o StrictHostKeyChecking=no ubuntu@<your-instance-ip> "echo SSH connection successful"
         
       - name: Deploy to Oracle Cloud
         if: success()
         run: |
           rsync -avz -e "ssh -o StrictHostKeyChecking=no" --exclude '.git' --exclude 'venv' --exclude '__pycache__' . ubuntu@<your-instance-ip>:~/job-tracker/
           ssh -o StrictHostKeyChecking=no ubuntu@<your-instance-ip> "cd ~/job-tracker && bash scripts/deploy.sh"
   ```
   Be sure to replace `<your-instance-ip>` with your actual instance IP address.

5. **Push to the repository**:
   ```bash
   git add .
   git commit -m "Update deployment workflow"
   git push origin main
   ```

6. **Monitor the deployment**:
   - Go to the "Actions" tab in your GitHub repository
   - Watch the "Deploy to Oracle Cloud" workflow
   - Once complete, access your application at the URLs above

## 3. Setting Up Systemd Services (Optional)

For production deployments, set up systemd services to ensure the application runs automatically after server restarts:

1. **Copy service files**:
   ```bash
   # On your server
   sudo cp ~/job-tracker/scripts/job-tracker-api.service /etc/systemd/system/
   sudo cp ~/job-tracker/scripts/job-tracker-dashboard.service /etc/systemd/system/
   ```

2. **Enable and start services**:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable job-tracker-api
   sudo systemctl enable job-tracker-dashboard
   sudo systemctl start job-tracker-api
   sudo systemctl start job-tracker-dashboard
   ```

3. **Check service status**:
   ```bash
   sudo systemctl status job-tracker-api
   sudo systemctl status job-tracker-dashboard
   ```

## Troubleshooting

If you have issues:

1. **Check application logs**:
   ```bash
   cat ~/job-tracker/logs/api.log
   cat ~/job-tracker/logs/dashboard.log
   ```

2. **Verify services are running**:
   ```bash
   ps aux | grep uvicorn
   ps aux | grep streamlit
   ```

3. **Restart services**:
   ```bash
   # If using systemd:
   sudo systemctl restart job-tracker-api
   sudo systemctl restart job-tracker-dashboard
   
   # If running manually:
   pkill -f "uvicorn main:app"
   pkill -f "streamlit run dashboard.py"
   nohup python run.py api &
   nohup python run.py dashboard &
   ```

4. **Check database connection**:
   ```bash
   source venv/bin/activate
   python -c "from app.db.database import engine; print('Connection successful' if engine.connect() else 'Connection failed')"
   ```

5. **SSH key issues in GitHub Actions**:
   If you see errors related to SSH keys in GitHub Actions, regenerate the deployment key and update the secret:
   ```bash
   # Generate a new key pair
   ssh-keygen -t ed25519 -f new_deploy_key -N ""
   
   # Add to server (after connecting)
   echo "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5... new_deploy_key" >> ~/.ssh/authorized_keys
   
   # Update GitHub secret with the new private key
   ```

6. **Port availability**:
   ```bash
   # Check if ports are in use
   sudo netstat -tulpn | grep -E '8000|8501'
   
   # Kill processes if needed
   sudo kill -9 <process-id>
   ```
