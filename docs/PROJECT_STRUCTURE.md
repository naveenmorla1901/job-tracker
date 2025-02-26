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
│   ├── dashboard/           # Dashboard components (if any)
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
│   │   └── __init__.py
│   ├── config.py            # Application configuration
│   └── __init__.py
├── docs/                    # Documentation
│   ├── ORACLE_CLOUD_SETUP.md # Oracle Cloud deployment guide
│   └── PROJECT_STRUCTURE.md  # This file
├── logs/                    # Log files
├── scripts/                 # Deployment and maintenance scripts
│   ├── deploy.sh            # Deployment script
│   ├── install.sh           # Installation script
│   ├── job-tracker-api.service     # Systemd service for API
│   ├── job-tracker-dashboard.service # Systemd service for dashboard
│   └── job-tracker-nginx.conf       # Nginx configuration
├── tests/                   # Test files
│   ├── conftest.py          # Test configuration
│   ├── test_api.py          # API tests
│   └── test_scrapers.py     # Scraper tests
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore file
├── .github/                 # GitHub workflows
│   └── workflows/
│       └── deploy.yml       # Deployment workflow
├── alembic.ini              # Alembic configuration
├── LICENSE                  # License file
├── main.py                  # FastAPI server
├── dashboard.py             # Streamlit dashboard
├── README.md                # Project readme
├── requirements.txt         # Python dependencies
├── run.py                   # Command-line runner
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

Main files:
- `dashboard.py`: The Streamlit dashboard application

### Database (PostgreSQL + SQLAlchemy)

The application uses PostgreSQL as the database and SQLAlchemy as the ORM:
- `app/db/models.py`: Defines database tables and relationships
- `app/db/crud.py`: Contains database operations
- `app/db/database.py`: Handles database connections
- `alembic/`: Contains database migrations

### Scrapers

Job scrapers collect data from various company career sites:
- `app/scrapers/base.py`: Base scraper class
- `app/scrapers/salesforce.py`: Salesforce-specific scraper
- Other company scrapers follow the same pattern

### CLI Interface

The command-line interface is in `run.py` and provides commands for:
- Starting the API server
- Starting the dashboard
- Database maintenance
- Testing scrapers

## Key Workflows

### Job Scraping Process

1. Scheduler (`app/scheduler/jobs.py`) triggers scraper runs
2. Scrapers collect job data from company career sites
3. CRUD operations (`app/db/crud.py`) store job data in the database
4. API endpoints (`app/api/endpoints/jobs.py`) make data available to the dashboard
5. Dashboard (`dashboard.py`) visualizes the data

### Deployment Process

1. Changes are pushed to GitHub
2. GitHub Actions workflow (`.github/workflows/deploy.yml`) is triggered
3. Code is deployed to Oracle Cloud instance
4. `scripts/deploy.sh` script is executed on the server to:
   - Update dependencies
   - Apply database migrations
   - Restart services

## Configuration

Configuration settings are managed through:
- Environment variables
- `.env` file (created from `.env.example`)
- `app/config.py`
