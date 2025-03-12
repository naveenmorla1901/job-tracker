# Automatic Service Restart

This documentation explains how the automatic service restart works after pushing changes to the repository.

## Overview

The system is configured to automatically restart the job-tracker services whenever changes are pushed to the main branch. This eliminates the need to manually run `sudo systemctl restart job-tracker-dashboard.service` after each deployment.

## How It Works

1. A Git `post-receive` hook is configured in the server repository
2. When changes are pushed to the repository, this hook is triggered
3. The hook automatically restarts both the API and dashboard services

## Components

### Git Hook

The `post-receive` hook is located at `.git/hooks/post-receive` and performs the following actions:

1. Changes to the repository directory
2. Pulls the latest changes from the main branch
3. Checks if the services are running
4. Restarts or starts the services as needed

### Deployment Process

The automatic restart is set up during the deployment process in `scripts/deploy.sh`, which:

1. Creates or updates the post-receive hook
2. Makes the hook executable
3. Ensures the systemd service files are in place
4. Enables the services to start on system boot

## Manual Setup

If you need to set this up manually on a new server:

1. Make sure the systemd service files are correctly installed:
   ```bash
   sudo cp scripts/job-tracker-api.service /etc/systemd/system/
   sudo cp scripts/job-tracker-dashboard.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable job-tracker-api.service
   sudo systemctl enable job-tracker-dashboard.service
   ```

2. Create the post-receive hook:
   ```bash
   mkdir -p .git/hooks
   touch .git/hooks/post-receive
   chmod +x .git/hooks/post-receive
   ```

3. Add the hook content (see the content in `.git/hooks/post-receive`)

## Troubleshooting

If the automatic restart isn't working:

1. Check if the hook is executable:
   ```bash
   ls -la .git/hooks/post-receive
   ```

2. Verify the systemd services are enabled:
   ```bash
   systemctl status job-tracker-api.service
   systemctl status job-tracker-dashboard.service
   ```

3. Check the logs for any errors:
   ```bash
   journalctl -u job-tracker-api.service
   journalctl -u job-tracker-dashboard.service
   ```
   
4. If needed, run the hook manually to test it:
   ```bash
   bash .git/hooks/post-receive
   ```

## Security Considerations

The hook uses `sudo` to restart the services. Make sure the `ubuntu` user has the necessary sudo permissions to restart these specific services without a password prompt by adding the appropriate entries to `/etc/sudoers.d/job-tracker`:

```
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart job-tracker-api.service
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl restart job-tracker-dashboard.service
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl start job-tracker-api.service
ubuntu ALL=(ALL) NOPASSWD: /bin/systemctl start job-tracker-dashboard.service
```
