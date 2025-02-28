# Job Tracker

![Dashboard](https://img.shields.io/badge/dashboard-Streamlit-FF4B4B)
![API](https://img.shields.io/badge/api-FastAPI-009688)
![Database](https://img.shields.io/badge/database-PostgreSQL-336791)

A comprehensive job tracking system that automatically scrapes, stores, and visualizes job postings from over 30 company career sites, helping you stay on top of the job market.

## Features

- **Multi-Source Scraping**: Automated collection from 30+ company career sites
- **Interactive Dashboard**: Filter and visualize job trends with Streamlit
- **Time-Based Filtering**: View jobs from the last 24 hours, 3 days, or 7 days
- **Advanced Filtering**: Filter by role, company, location, and more
- **Direct Application Links**: One-click access to original job postings
- **Automatic Updates**: Hourly job scraping during business hours
- **Data Management**: Automatic cleanup of older job records

## Screenshots

[Dashboard Screenshot - To Be Added]  
[Job Listings Screenshot - To Be Added]

## Architecture

The system consists of three main components:

1. **API Backend** (FastAPI): Handles data storage, scraping and job management
2. **Web Dashboard** (Streamlit): Interactive visualization and filtering
3. **Scheduler** (APScheduler): Manages regular scraping and maintenance

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
http://170.9.227.112:8501
```

## Usage

- **View Job Listings**: Browse all jobs or filter by role, company, etc.
- **Track New Postings**: See jobs posted in the last 24 hours
- **Apply Directly**: Click 'Apply' to go to the original job posting
- **Monitor Trends**: View charts of job postings by role and employment type

## API Reference

The system provides a RESTful API for accessing job data:

- `GET /api/jobs` - Get job listings with filtering options
- `GET /api/jobs/companies` - Get all available companies
- `GET /api/jobs/roles` - Get all job role categories
- `GET /api/stats` - Get statistics about job listings

## Deployment

This project can be easily deployed to Oracle Cloud Infrastructure Free Tier:

- For a quick setup, follow the [Quick Deployment Guide](docs/QUICK_DEPLOY.md)
- For a more comprehensive setup, see the [Oracle Cloud Setup Guide](docs/ORACLE_CLOUD_SETUP.md)

The project includes GitHub Actions workflows for automated deployment.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/) and [Streamlit](https://streamlit.io/)
- Deployed on Oracle Cloud Infrastructure
