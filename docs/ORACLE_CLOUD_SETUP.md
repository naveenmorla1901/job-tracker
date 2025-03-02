# Oracle Cloud Deployment Guide

This guide provides step-by-step instructions for deploying the Job Tracker application to Oracle Cloud Infrastructure (OCI) Free Tier.

## Prerequisites

- Oracle Cloud account (sign up at [https://www.oracle.com/cloud/free/](https://www.oracle.com/cloud/free/))
- GitHub account
- SSH key pair for secure access

## Step 1: Create your Oracle Cloud account

1. Go to [https://www.oracle.com/cloud/free/](https://www.oracle.com/cloud/free/)
2. Click "Start for free"
3. Fill in the registration form 
4. Complete the verification process
5. Set up your Oracle Cloud account

## Step 2: Generate SSH Keys

You'll need an SSH key pair to securely access your cloud instance.

### On Windows:

1. Open PowerShell
2. Run this command to generate an SSH key:
   ```powershell
   ssh-keygen -t ed25519 -f "$HOME\.ssh\deployment_key"
   ```
3. Press Enter when asked for a passphrase (or enter a passphrase for additional security)
4. Find your keys at:
   - Private key: `C:\Users\YourUsername\.ssh\deployment_key`
   - Public key: `C:\Users\YourUsername\.ssh\deployment_key.pub`

### On macOS/Linux:

1. Open Terminal
2. Run this command:
   ```bash
   ssh-keygen -t ed25519 -f ~/.ssh/deployment_key
   ```
3. Press Enter when asked for a passphrase (or enter a passphrase for additional security)
4. Find your keys at:
   - Private key: `~/.ssh/deployment_key`
   - Public key: `~/.ssh/deployment_key.pub`

## Step 3: Set up Oracle Cloud Infrastructure (OCI)

### Create a Virtual Cloud Network (VCN)

1. Sign in to the Oracle Cloud Console
2. Open the navigation menu (☰) and select "Networking" > "Virtual Cloud Networks"
3. Choose your compartment (usually it's the root compartment)
4. Click "Start VCN Wizard"
5. Select "VCN with Internet Connectivity" and click "Start VCN Wizard"
6. Enter the following information:
   - VCN Name: `job-tracker-vcn`
   - Compartment: Leave as default
   - VCN CIDR Block: `10.0.0.0/16`
   - Public Subnet CIDR Block: `10.0.0.0/24`
   - Private Subnet CIDR Block: `10.0.1.0/24`
7. Click "Next" and then "Create"

### Create an Instance

1. Open the navigation menu (☰) and select "Compute" > "Instances"
2. Click "Create Instance"
3. Enter a name: `job-tracker-instance`
4. Choose an availability domain (leave the default)
5. Select "Change Image" and pick "Canonical Ubuntu" (20.04 or newer)
6. For the shape, select "VM.Standard.E2.1.Micro" (this is included in the Free Tier)
7. In the networking section:
   - Select the VCN you created earlier (`job-tracker-vcn`)
   - Select the public subnet
   - Assign a public IP address: Yes
8. Add your SSH key:
   - Select "Paste public key"
   - Paste the contents of your public key file (e.g., `~/.ssh/deployment_key.pub`)
9. Click "Create"

### Configure Security Rules

1. After your instance is created, click on its name to view details
2. In the "Primary VNIC" section, click on the subnet link
3. Click on the "Default Security List" link
4. Click "Add Ingress Rules"
5. Add rules for the following:
   - For API access:
     - Source CIDR: `0.0.0.0/0`
     - IP Protocol: TCP
     - Destination Port Range: 8000
   - For Dashboard access:
     - Source CIDR: `0.0.0.0/0`
     - IP Protocol: TCP
     - Destination Port Range: 8501
   - For HTTP access:
     - Source CIDR: `0.0.0.0/0`
     - IP Protocol: TCP
     - Destination Port Range: 80
   - For HTTPS access:
     - Source CIDR: `0.0.0.0/0`
     - IP Protocol: TCP
     - Destination Port Range: 443
6. Click "Add Ingress Rules"

## Step 4: Connect to Your Instance

1. Get the public IP address from the instance details page
2. Connect via SSH:

   **Windows (PowerShell):**
   ```powershell
   ssh -i "$HOME\.ssh\deployment_key" ubuntu@170.9.227.112
   ```

   **macOS/Linux:**
   ```bash
   ssh -i ~/.ssh/deployment_key ubuntu@170.9.227.112
   ```

## Step 5: Set Up the Server Environment

Once connected to your instance, run the following commands:

```bash
# Update package lists
sudo apt update
sudo apt upgrade -y

# Install Git
sudo apt install -y git

# Create directory for the application
# mkdir -p ~/job-tracker

# Clone the repository (if you're doing a manual setup)
git clone https://github.com/naveenmorla1901/job-tracker.git ~/job-tracker
cd ~/job-tracker
python3 -m venv venv
source venv/bin/activate
# Run the install script
bash scripts/install.sh
pip install -r requirements.txt
python create_database.py  # Create the database itself (if it doesn't exist)
alembic upgrade head 
# Initialize the database
python run.py reset_db

# Start the services manually (if not using systemd)
python run.py api
python run.py dashboard
```

The install script will:
1. Install system dependencies
2. Set up PostgreSQL
3. Configure Python environment
4. Set up systemd services
5. Configure Nginx
6. Start the application

## Step 6: Configure GitHub Actions for Automatic Deployment

To set up automatic deployment, you need to add these secrets to your GitHub repository:

1. Go to your GitHub repository
2. Click on "Settings" > "Secrets and variables" > "Actions"
3. Click "New repository secret"
4. Add the following secrets:
   - `DEPLOYMENT_PRIVATE_KEY`: Your private SSH key (contents of `~/.ssh/deployment_key`)
   - `ORACLE_HOST`: Your instance's public IP address
   - `ORACLE_USER`: `ubuntu`
   - `ORACLE_KNOWN_HOSTS`: Run `ssh-keyscan 170.9.227.112` to get this value

### Generate Known Hosts Value
```bash
# Run this command locally, replacing with your instance IP
ssh-keyscan -t ed25519 170.9.227.112
```
Copy the entire output and add it as the `ORACLE_KNOWN_HOSTS` secret.

### Set Up GitHub Action Workflow

The repository includes a GitHub Actions workflow file (`.github/workflows/deploy.yml`) that handles deployment to Oracle Cloud. Make sure this file contains the correct IP address for your instance.

## Step 7: Access Your Application

After the deployment is complete, you can access your application at:

- Dashboard: `http://170.9.227.112:8501`
- API: `http://170.9.227.112:8000/api`
- API Documentation: `http://170.9.227.112:8000/docs`

## Step 8: Set Up Systemd Services for Reliability

For long-term reliability, set up systemd services:

```bash
# Ensure the service files exist
ls -la ~/job-tracker/scripts/job-tracker-*.service

# If they exist, copy them to systemd
sudo cp ~/job-tracker/scripts/job-tracker-api.service /etc/systemd/system/
sudo cp ~/job-tracker/scripts/job-tracker-dashboard.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable job-tracker-api
sudo systemctl enable job-tracker-dashboard
sudo systemctl start job-tracker-api
sudo systemctl start job-tracker-dashboard

# Check status
sudo systemctl status job-tracker-api
sudo systemctl status job-tracker-dashboard
```

## Troubleshooting

If you encounter issues:

### 1. GitHub Actions SSH Key Issues
If GitHub Actions fails with "Permission denied (publickey)" or key format errors:

1. Generate a fresh key specifically for deployment:
   ```bash
   ssh-keygen -t ed25519 -f deployment_key -N ""
   ```

2. Add the public key to your server:
   ```bash
   # On your server
   echo "content-of-deployment_key.pub" >> ~/.ssh/authorized_keys
   ```

3. Update the GitHub secret with the private key content

### 2. Check Service Status
```bash
# Check service status
sudo systemctl status job-tracker-api
sudo systemctl status job-tracker-dashboard

# View detailed logs
sudo journalctl -u job-tracker-api
sudo journalctl -u job-tracker-dashboard
```

### 3. Manual Service Start
If services won't start through systemd:
```bash
# Activate environment
cd ~/job-tracker
source venv/bin/activate

# Start services manually
mkdir -p logs
nohup uvicorn main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &
nohup streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0 > logs/dashboard.log 2>&1 &
```

### 4. Check Process Status
```bash
# Check if processes are running
ps aux | grep uvicorn
ps aux | grep streamlit
```

### 5. Check Database Connection
```bash
# Check if database exists
sudo -u postgres psql -c "\l" | grep job_tracker

# Check database connection
cd ~/job-tracker
source venv/bin/activate
python -c "from app.db.database import get_db; from app.db.models import Job; db = next(get_db()); print(f'Total jobs: {db.query(Job).count()}')"
```

### 6. Verify Ports are Open
Make sure ports 8000 and 8501 are accessible:
```bash
# Check if ports are open
sudo netstat -tulpn | grep -E '8000|8501'

# Test ports from your local machine
curl http://<your-instance-ip>:8000
curl http://<your-instance-ip>:8501
```

## Maintenance

### Manual Deployment

If you need to manually deploy changes:

```bash
cd ~/job-tracker
git pull
bash scripts/deploy.sh
```

### Database Backups

To back up your database:

```bash
pg_dump -U job_tracker -d job_tracker > backup-$(date +%Y%m%d).sql
```

### Cleaning Up Old Job Records

The system automatically cleans up old job records, but you can manually trigger it:

```bash
cd ~/job-tracker
source venv/bin/activate
python run.py purge
```

### Monitoring Application Logs

To monitor logs in real-time:

```bash
# API logs
tail -f ~/job-tracker/logs/api.log

# Dashboard logs
tail -f ~/job-tracker/logs/dashboard.log
```
