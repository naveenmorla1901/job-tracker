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
   ssh-keygen -t rsa -b 4096 -f "$HOME\.ssh\oci_key"
   ```
3. Press Enter when asked for a passphrase (or enter a passphrase for additional security)
4. Find your keys at:
   - Private key: `C:\Users\YourUsername\.ssh\oci_key`
   - Public key: `C:\Users\YourUsername\.ssh\oci_key.pub`

### On macOS/Linux:

1. Open Terminal
2. Run this command:
   ```bash
   ssh-keygen -t rsa -b 4096 -f ~/.ssh/oci_key
   ```
3. Press Enter when asked for a passphrase (or enter a passphrase for additional security)
4. Find your keys at:
   - Private key: `~/.ssh/oci_key`
   - Public key: `~/.ssh/oci_key.pub`

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
   - Paste the contents of your public key file (e.g., `~/.ssh/oci_key.pub`)
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
   ssh -i "$HOME\.ssh\oci_key" ubuntu@<instance-ip-address>
   ```

   **macOS/Linux:**
   ```bash
   ssh -i ~/.ssh/oci_key ubuntu@<instance-ip-address>
   ```

## Step 5: Set Up the Server Environment

Once connected to your instance, run the following commands:

```bash
# Update package lists
sudo apt update
sudo apt upgrade -y

# Install Git
sudo apt install -y git

# Clone the repository
git clone https://github.com/yourusername/job-tracker.git
cd job-tracker

# Run the install script
bash scripts/install.sh
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
   - `ORACLE_SSH_KEY`: Your private SSH key (contents of `~/.ssh/oci_key`)
   - `ORACLE_HOST`: Your instance's public IP address
   - `ORACLE_USER`: `ubuntu`
   - `ORACLE_KNOWN_HOSTS`: Run `ssh-keyscan <instance-ip>` to get this value

Now when you push changes to the main branch, GitHub Actions will automatically deploy them to your Oracle Cloud instance.

## Step 7: Access Your Application

After the deployment is complete, you can access your application at:

- Dashboard: `http://<instance-ip>:8501`
- API: `http://<instance-ip>:8000/api`

## Troubleshooting

If you encounter issues:

1. **Check service status**:
   ```bash
   sudo systemctl status job-tracker-api
   sudo systemctl status job-tracker-dashboard
   ```

2. **View logs**:
   ```bash
   sudo journalctl -u job-tracker-api
   sudo journalctl -u job-tracker-dashboard
   ```

3. **Restart services**:
   ```bash
   sudo systemctl restart job-tracker-api
   sudo systemctl restart job-tracker-dashboard
   ```

4. **Check the database connection**:
   ```bash
   sudo -u postgres psql -c "\l" | grep job_tracker
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
