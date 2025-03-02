# Project Structure

This document provides an overview of the Job Tracker project structure to help you understand the codebase organization.

## Directory Structure

```
job_tracker/
├── alembic/                 # Database migration files
├── app/                     # Core application code
│   ├── api/                 # API endpoints
│   │   ├── endpoints/       # Individual API routes
│   │   └── __init__.py
│   ├── dashboard/           # Dashboard components
│   │   ├── logs.py          # System logs & monitoring page
│   │   └── __init__.py
│   ├── db/                  # Database operations
│   │   ├── crud.py          # Database CRUD operations
│   │   ├── database.py      # Database connection handling
│   │   ├── models.py        # SQLAlchemy models
│   │   └── __init__.py
│   ├── scheduler/           # Scheduling functionality
│   │   ├── jobs.py          # Scheduled job definitions
│   │   └── __init__.py
│   ├── scrapers/            # Web scrapers for different companies
│   │   ├── base.py          # Base scraper class
│   │   ├── salesforce.py    # Salesforce scraper
│   │   ├── [30+ company scrapers] # Additional company scrapers
│   │   └── __init__.py      # Automatic scraper discovery
│   ├── config.py            # Application configuration
│   └── __init__.py
├── docs/                    # Documentation
│   ├── ORACLE_CLOUD_SETUP.md # Oracle Cloud deployment guide
│   ├── PROJECT_STRUCTURE.md  # This file
│   ├── QUICK_DEPLOY.md      # Quick deployment guide
│   ├── DEVELOPMENT.md       # Development guidelines
│   └── FUTURE_ENHANCEMENTS.md # Future feature ideas
├── logs/                    # Log files directory
├── scripts/                 # Deployment and maintenance scripts
│   ├── deploy.sh            # Deployment script
│   ├── install.sh           # Installation script
│   ├── setup_nginx.sh       # Nginx setup script
│   ├── job-tracker-api.service # Systemd service for API
│   ├── job-tracker-dashboard.service # Systemd service for dashboard
│   └── job-tracker-nginx.conf # Nginx configuration
├── tests/                   # Test files
│   ├── conftest.py          # Test configuration
│   ├── test_api.py          # API tests
│   └── test_scrapers.py     # Scraper tests
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore file
├── .github/                 # GitHub workflows
│   └── workflows/
│       ├── deploy.yml       # Main deployment workflow
│       └── deploy-alternate.yml # Alternative deployment configuration
├── alembic.ini              # Alembic configuration
├── LICENSE                  # License file
├── main.py                  # FastAPI server
├── dashboard.py             # Streamlit dashboard
├── log_manager.py           # Log rotation and cleanup
├── system_info.py           # System resource monitoring
├── system_info_utils.py     # System monitoring utilities
├── README.md                # Project readme
├── development_progress.md  # Development tracking document
├── requirements.txt         # Python dependencies
├── run.py                   # Command-line runner
├── scheduled_cleanup.py     # Automatic log and record cleanup
├── purge_old_records.py     # Database record cleanup
└── pytest.ini               # Pytest configuration
```

## Core Components

### API (FastAPI)

The API backend is built with FastAPI and provides endpoints for:
- Job listings with filtering
- Company and role information
- Statistics and analytics

Main files:
- `main.py`: The API server entry point
- `app/api/endpoints/*.py`: API route handlers
- `app/db/models.py`: Database models

### Dashboard (Streamlit)

The user interface is built with Streamlit and provides:
- Interactive job browsing
- Filtering and searching
- Data visualizations
- System monitoring and log viewing

Main files:
- `dashboard.py`: The Streamlit dashboard application
- `app/dashboard/logs.py`: System monitoring and log viewing interface

### System Monitoring

The monitoring system provides information about:
- Server resource usage (CPU, memory, disk)
- Running processes
- Application logs
- Project directory analysis
- Database statistics

Main files:
- `system_info.py`: System resource monitoring
- `system_info_utils.py`: Additional monitoring functions
- `log_manager.py`: Log rotation and cleanup utilities

### Database (PostgreSQL + SQLAlchemy)

The application uses PostgreSQL as the database and SQLAlchemy as the ORM:
- `app/db/models.py`: Defines database tables and relationships
- `app/db/crud.py`: Contains database operations
- `app/db/database.py`: Handles database connections
- `alembic/`: Contains database migrations

### Scrapers

Job scrapers collect data from various company career sites:
- `app/scrapers/base.py`: Base scraper class
- `app/scrapers/__init__.py`: Automatic scraper discovery
- `app/scrapers/*.py`: 30+ company-specific scrapers

### CLI Interface

The command-line interface is in `run.py` and provides commands for:
- Starting the API server
- Starting the dashboard
- Database maintenance and reset
- Record cleanup
- Testing scrapers

## Key Workflows

### Job Scraping Process

1. Scheduler (`app/scheduler/jobs.py`) triggers scraper runs hourly (7AM-5PM)
2. Scrapers collect job data from 30+ company career sites
3. CRUD operations (`app/db/crud.py`) store job data in the database
4. API endpoints (`app/api/endpoints/jobs.py`) make data available to the dashboard
5. Dashboard (`dashboard.py`) visualizes the data with filtering options

### Deployment Process

1. Changes are pushed to GitHub
2. GitHub Actions workflow (`.github/workflows/deploy.yml`) is triggered
3. Code is deployed to Oracle Cloud instance via SSH
4. `scripts/deploy.sh` script is executed on the server to:
   - Update dependencies
   - Apply database migrations
   - Configure Nginx as reverse proxy
   - Start services properly
   - Set up log rotation and cleanup

### Monitoring and Maintenance

1. Automatic log rotation and cleanup (`log_manager.py`)
2. Scheduled database record purging (`scheduled_cleanup.py`)
3. System resource monitoring (`system_info.py`)
4. Process tracking and management
5. Directory size analysis and reporting

## Configuration

Configuration settings are managed through:
- Environment variables
- `.env` file (created from `.env.example`)
- `app/config.py`
- Command-line options in `run.py`

## Nginx Integration

The project includes Nginx as a reverse proxy:
- `scripts/setup_nginx.sh`: Configures Nginx during deployment
- `scripts/job-tracker-nginx.conf`: Nginx configuration template
- Handles routing for both API (port 8000) and Dashboard (port 8501)
- Provides a unified interface for users at a single domain/IP
