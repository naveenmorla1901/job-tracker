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

4. **Initialize the database**:
   ```bash
   source venv/bin/activate
   python run.py reset_db
   ```

5. **Start the application**:
   ```bash
   nohup python run.py api &
   nohup python run.py dashboard &
   ```

6. **Access your application**:
   - API: `http://<your-instance-ip>:8000`
   - Dashboard: `http://<your-instance-ip>:8501`

### Automated Deployment with GitHub Actions

1. **Add GitHub Repository Secrets**:
   - Go to your GitHub repository
   - Click "Settings" → "Secrets and variables" → "Actions"
   - Add these secrets:
     - `ORACLE_SSH_KEY`: Your private SSH key content
     - `ORACLE_HOST`: Your instance's IP address
     - `ORACLE_USER`: `ubuntu`
     - `ORACLE_KNOWN_HOSTS`: Run `ssh-keyscan <your-instance-ip>` locally and paste the output

2. **Push to the repository**:
   ```bash
   git push origin main
   ```

3. **Monitor the deployment**:
   - Go to the "Actions" tab in your GitHub repository
   - Watch the "Deploy to Oracle Cloud" workflow
   - Once complete, access your application at the URLs above

## Troubleshooting

If you have issues:

1. **Check application logs**:
   ```bash
   cat api.log
   cat dashboard.log
   ```

2. **Verify services are running**:
   ```bash
   ps aux | grep python
   ```

3. **Restart services**:
   ```bash
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
