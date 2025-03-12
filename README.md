# Job Tracker

![Dashboard](https://img.shields.io/badge/dashboard-Streamlit-FF4B4B)
![API](https://img.shields.io/badge/api-FastAPI-009688)
![Database](https://img.shields.io/badge/database-PostgreSQL-336791)
![Monitoring](https://img.shields.io/badge/monitoring-psutil-4EAA25)
![Deployment](https://img.shields.io/badge/deployment-GitHub_Actions-2088FF)
![Scrapers](https://img.shields.io/badge/scrapers-30+-FFA500)

A comprehensive job tracking system that automatically scrapes, stores, and visualizes job postings from over 30 company career sites, helping you stay on top of the job market.

## Features

- **Multi-Source Scraping**: Automated collection from 30+ company career sites
- **Interactive Dashboard**: Filter and visualize job trends with Streamlit
- **Time-Based Filtering**: View jobs from the last 24 hours, 3 days, or 7 days
- **Advanced Filtering**: Filter by role, company, location, and more
- **Direct Application Links**: One-click access to original job postings
- **Automatic Updates**: Hourly job scraping during business hours
- **Data Management**: Automatic cleanup of older job records
- **System Monitoring**: Resource usage tracking and log management
- **Automated Deployment**: CI/CD with GitHub Actions
- **Nginx Integration**: Reverse proxy for unified access
- **Dark Mode**: Toggleable dark theme for better viewing experience
- **Mobile Responsiveness**: Optimized layout for mobile devices
- **Pagination**: Navigate through large sets of job listings
- **Rate Limiting**: Protection against API abuse
- **Custom Error Pages**: User-friendly error messages

## Screenshots

[Dashboard Screenshot - To Be Added]  
[Job Listings Screenshot - To Be Added]  
[System Monitoring Screenshot - To Be Added]

## Architecture

The system consists of four main components:

1. **API Backend** (FastAPI): Handles data storage, scraping and job management
2. **Web Dashboard** (Streamlit): Interactive visualization and filtering
3. **Scheduler** (APScheduler): Manages regular scraping and maintenance
4. **Monitoring System**: Tracks resources, logs, and system performance

## Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL database
- Git

### Installation

1. Clone the repository
```bash
git clone https://github.com/naveenmorla1901/job-tracker.git
cd job-tracker
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure the database
```bash
# Create a .env file with your database credentials
echo "DATABASE_URL=postgresql://postgres:1901@localhost/job_tracker" > .env
```

5. Initialize the database
```bash
python run.py reset_db
```

6. Start the application
```bash
# In one terminal
python run.py api

# In another terminal
python run.py dashboard
```

7. Open the dashboard in your browser
```
http://localhost:8501
```

## Usage

- **View Job Listings**: Browse all jobs or filter by role, company, etc.
- **Track New Postings**: See jobs posted in the last 24 hours
- **Apply Directly**: Click 'Apply' to go to the original job posting
- **Monitor Trends**: View charts of job postings by role and employment type
- **System Monitoring**: Check resource usage, process status, and logs
- **Log Management**: View and manage application logs
- **Dark Mode**: Toggle between light and dark themes
- **Mobile Access**: Use on mobile devices with optimized layout
- **Pagination**: Navigate through large job listing result sets

## System Monitoring

The application includes a comprehensive system monitoring interface:

- **Resource Usage**: CPU, memory, and disk utilization
- **Process Tracking**: View running application processes
- **Log Viewing**: Browse recent logs with auto-refresh
- **Directory Analysis**: Size breakdown of project folders
- **Database Stats**: Job counts, active records, and more

Access the monitoring interface from the main dashboard via the "System Logs" navigation option.

For detailed information, see the [System Monitoring Guide](docs/SYSTEM_MONITORING.md).

## Server Monitoring Commands

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

# View Git hook execution log (if restart isn't working)
journalctl -u job-tracker-api.service | grep post-receive
journalctl -u job-tracker-dashboard.service | grep post-receive
```

> **Note:** Services now automatically restart after pushing changes to the repository. See [Auto Restart Documentation](docs/AUTO_RESTART.md) for details.

## API Reference

The system provides a RESTful API for accessing job data:

- `GET /api/jobs` - Get job listings with filtering options
- `GET /api/jobs/companies` - Get all available companies
- `GET /api/jobs/roles` - Get all job role categories
- `GET /api/stats` - Get statistics about job listings

All list endpoints support pagination with navigation links.

## Deployment

This project can be easily deployed to Oracle Cloud Infrastructure Free Tier:

- For a quick setup, follow the [Quick Deployment Guide](docs/QUICK_DEPLOY.md)
- For a more comprehensive setup, see the [Oracle Cloud Setup Guide](docs/ORACLE_CLOUD_SETUP.md)

The project includes GitHub Actions workflows for automated deployment, and Nginx configuration for reverse proxy.

## Command-line Interface

The project includes a comprehensive CLI for management:

```bash
# Core Application
python run.py api           # Start API server
python run.py dashboard     # Start dashboard

# Database Management
python run.py reset_db      # RESET DATABASE - Delete ALL data and start fresh
python run.py purge         # Manually delete job records older than 7 days
python run.py cleanup       # Clean up database (remove duplicates, fix issues)
python run.py update_db     # Update database schema after model changes

# Utilities
python run.py quick_clean   # Remove test files
python run.py free          # Free port 8000 if occupied
python run.py help          # Show all available commands
```

## Recent Enhancements

- **Automatic Service Restart**: Added Git hook to automatically restart services after pushing changes
- **Dark Mode Toggle**: Added user-selectable dark theme for better viewing experience
- **Mobile Responsiveness**: Optimized layout for mobile devices
- **Pagination**: Added navigation controls for large result sets
- **Database Indexing**: Improved performance with strategic indexes
- **API Pagination**: Enhanced API with proper pagination support
- **Rate Limiting**: Added protection against API abuse
- **Custom Error Pages**: Created user-friendly error messages
- **Caching Strategy**: Implemented basic caching for improved performance

## Development

For detailed information about the development process, features, and progress, see the [Development Progress](development_progress.md) document.

The [Project Structure](docs/PROJECT_STRUCTURE.md) guide provides an overview of the codebase organization.

For future enhancements, see the [Future Enhancements](docs/FUTURE_ENHANCEMENTS.md) document.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [Streamlit](https://streamlit.io/)
- System monitoring with [psutil](https://psutil.readthedocs.io/)
- Deployed on Oracle Cloud Infrastructure
- Reverse proxy with [Nginx](https://nginx.org/)
