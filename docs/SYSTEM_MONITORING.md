# System Monitoring

This document provides an overview of the system monitoring capabilities in the Job Tracker application.

## Overview

The Job Tracker includes a comprehensive system monitoring interface that helps you track resource usage, view logs, and monitor the health of your application. This functionality is especially useful for deployment in cloud environments like Oracle Cloud.

## Accessing System Monitoring

The monitoring interface is accessible through the main dashboard:

1. Navigate to the dashboard URL (typically `http://your-server-ip:8501`)
2. Click on "System Logs" in the navigation sidebar
3. The System Logs page offers three tabs:
   - API Logs
   - Dashboard Logs
   - System Info

## Features

### Resource Monitoring

The System Info tab provides real-time monitoring of:

- **CPU Usage**: Current utilization percentage and core count
- **Memory Usage**: RAM utilization, total, and used memory
- **Disk Usage**: Storage utilization, total, and available space
- **System Uptime**: How long the server has been running
- **Running Processes**: Count of all processes and application-specific processes

### Log Management

The log viewing tabs provide:

- **Real-time Log Access**: View the most recent logs first
- **Scrollable Interface**: Navigate through log entries easily
- **Automatic Cleanup**: Logs older than 2 days are automatically removed
- **Manual Cleanup**: Option to manually trigger log cleanup

### Project Analysis

The system monitoring also provides:

- **Directory Structure Analysis**: Size breakdown of project folders and subfolders
- **Log File Size**: Track the size of individual log files
- **Total Project Size**: Monitor the overall project footprint
- **Database Statistics**: Job counts, active records, and more

### Process Monitoring

Track running application processes including:

- **Process Types**: Identify different application components (API, dashboard, etc.)
- **Resource Usage**: Memory and CPU usage per process
- **Process Details**: Process IDs and command lines
- **User Breakdown**: Process distribution by user

## Automatic Maintenance

The monitoring system includes automatic maintenance features:

1. **Log Rotation**: Large log files are automatically rotated
2. **Log Cleanup**: Logs older than 2 days are removed
3. **Twice-Daily Checks**: Cleanup runs at 3 AM and 3 PM daily
4. **Manual Triggers**: Force cleanup via the dashboard interface

## Server Monitoring Commands

To monitor your deployment from the command line:

```bash
# View API logs
tail -f /home/ubuntu/job-tracker/job_tracker.log

# View Streamlit dashboard logs
tail -f /home/ubuntu/job-tracker/dashboard.log

# Check if FastAPI server is running
ps aux | grep uvicorn

# Check if Streamlit dashboard is running
ps aux | grep streamlit

# Check service status
sudo systemctl status job-tracker-api.service
sudo systemctl status job-tracker-dashboard.service

# Check Nginx configuration
sudo nginx -t

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## Implementation Details

The monitoring system consists of several components:

- `system_info.py`: Collects resource usage information
- `system_info_utils.py`: Provides additional monitoring functions
- `log_manager.py`: Handles log rotation and cleanup
- `app/dashboard/logs.py`: Streamlit interface for the monitoring system
- `scheduled_cleanup.py`: Manages automatic maintenance tasks

## Technical Requirements

The monitoring system uses `psutil` for resource tracking, which is automatically installed during deployment via:

```bash
pip install psutil
```

## Extending the Monitoring System

You can extend the monitoring system by:

1. Adding new metrics to `system_info.py`
2. Creating additional visualizations in `app/dashboard/logs.py`
3. Implementing alerts or thresholds for critical resources
4. Adding more detailed log analysis capabilities

## Troubleshooting

Common issues and solutions:

- **Missing psutil**: If system information isn't displaying, ensure `psutil` is installed
- **Permission Issues**: Some monitoring features require elevated permissions
- **High Resource Usage**: Consider reducing the log retention period if disk space is limited
- **Slow Dashboard**: Reduce the amount of log data loaded at once by adjusting `max_lines` in `log_manager.py`

## Best Practices

For optimal monitoring:

1. Check the System Info tab regularly to monitor resource usage
2. Review logs when troubleshooting application issues
3. Set up server monitoring alerts for critical thresholds
4. Ensure log rotation is working to prevent disk space issues
5. Monitor database statistics for unexpected growth or issues
