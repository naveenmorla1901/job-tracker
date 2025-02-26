# Job Tracker Project: Development Progress & Documentation

## Project Overview

The Job Tracker is a personal tool for monitoring job listings from various company career pages. It automatically scrapes job postings, stores them in a database, and provides a user-friendly dashboard for exploring opportunities.

## Technical Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: Streamlit, Plotly
- **Scheduling**: APScheduler, Schedule
- **Automation**: Python scripts for database maintenance
- **Scraping**: Requests, BeautifulSoup4

## Development Timeline & Progress

### Initial Development Phase
- ✅ Set up project structure with FastAPI and SQLAlchemy
- ✅ Created PostgreSQL database and Alembic migrations
- ✅ Implemented initial CRUD operations
- ✅ Built basic Salesforce scraper
- ✅ Created scheduler for regular scraper execution

### Enhancement Phase
- ✅ Developed Streamlit dashboard with filtering
- ✅ Added visualizations for job distributions
- ✅ Implemented job listing display with links
- ✅ Created database management utilities
- ✅ Added automatic cleanup of older records

### Bugfixes & Improvements
- ✅ Fixed date filtering issues (especially 24-hour view)
- ✅ Implemented multi-select filters for roles and companies
- ✅ Enhanced role display with checkbox interface
- ✅ Improved URL handling and link generation
- ✅ Added better error handling and logging
- ✅ Created database reset functionality

### Expanded Coverage
- ✅ Added 30+ company scrapers
- ✅ Implemented auto-discovery of scrapers
- ✅ Created consistent company name display
- ✅ Focused on data science/ML roles

## Key Features Implemented

### API Functionality
- **Job Filtering**: By role, company, date, location, and type
- **Multi-select Support**: For roles and companies
- **Data Aggregation**: Endpoints for unique values and statistics
- **Error Handling**: Robust error handling and logging

### Dashboard Interface
- **Time Period Selection**: 24h, 3-day, and 7-day views
- **Role Checkboxes**: Visual selection of multiple roles
- **Company Multi-select**: Choose multiple companies
- **Dual Visualizations**: Jobs by role and employment type
- **Interactive Table**: With direct application links

### Database Management
- **Automatic Cleanup**: Twice-daily removal of old records
- **Duplicate Handling**: Prevention of duplicate job entries
- **Role Validation**: Mapping and standardization of roles
- **Database Reset**: Complete reset capability for fresh starts

### Scraper Capabilities
- **Extensive Company Support**: 30+ company career sites
- **Auto-Discovery**: Automatic integration of new scrapers
- **Consistent Data Format**: Standardized job data structure
- **Error Handling**: Robust error management and logging
- **Company Name Mapping**: Proper display of company names

### Code Quality Improvements
- **Robust Error Handling**: Throughout all components
- **Detailed Logging**: For debugging and monitoring
- **Dynamic Module Loading**: Automatic scraper detection
- **Code Organization**: Clean separation of concerns

## Technical Challenges Overcome

### Date Filtering Issues
We addressed challenges with the 24-hour filter not showing today's jobs by:
- Adding timezone handling with buffer time
- Special-casing 24-hour filter to ensure it includes everything from start of day
- Improved date comparison logic in database queries

### Multi-Select Parameter Handling
We solved the challenge of sending multiple role and company selections by:
- Using proper request parameter encoding (multiple keys instead of arrays)
- Creating a custom fetch function that works with arrays of parameters
- Implementing backend support for List parameters in FastAPI

### Role Data Quality
We improved role data consistency by:
- Implementing role validation and standardization
- Mapping similar roles to standard categories
- Filtering out invalid roles
- Providing fallbacks for missing data

### URL and Link Issues
We fixed problems with job links by:
- Implementing URL sanitization
- Adding target="_blank" for new tab opening
- Including proper security attributes (rel="noopener noreferrer")
- Handling invalid URLs gracefully

### Scraper Integration
We improved the scraper system with:
- Dynamic module discovery and loading
- Standardized function naming convention
- Company name capitalization mapping
- Unified role configuration

## Command-line Interface Reference

We created a comprehensive CLI for managing the application:

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

## Current Limitations & Future Improvements

### Current Limitations
- Limited to 7-day job history
- No user authentication or personalization
- No email notifications for new listings
- Limited to specific role categories

### Recent Improvements
- **Expanded Company Coverage**: Added 30+ company career site scrapers
- **Auto-Discovery**: Automatic integration of new scrapers without configuration
- **Company Name Display**: Proper capitalization and formatting of company names
- **Focused Role Set**: Optimization for data science and ML positions

### Potential Future Enhancements
- Email notifications for new job matches
- Application tracking functionality
- User accounts and preferences
- Mobile app version
- AI-powered job matching and recommendations
- Additional role categories

## Getting Started

To continue development on this project:

1. Clone the repository
2. Setup a virtual environment: `python -m venv venv`
3. Activate it: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)
4. Install dependencies: `pip install -r requirements.txt`
5. Reset the database: `python run.py reset_db`
6. Start the API: `python run.py api`
7. Start the dashboard: `python run.py dashboard`

## Core Components & Files

### Backend Components
- `main.py`: API server entry point
- `app/api/endpoints/jobs.py`: Job filtering API endpoints
- `app/db/models.py`: Database schema definitions
- `app/db/crud.py`: Database operations
- `app/scheduler/jobs.py`: Job scheduler setup
- `app/scrapers/__init__.py`: Automatic scraper discovery
- `app/scrapers/*.py`: Company-specific scrapers (30+ companies)

### Frontend Components
- `dashboard.py`: Streamlit dashboard
- Various visualization and filtering components

### Utility Scripts
- `run.py`: Command-line interface
- `reset_database.py`: Database reset utility
- `purge_old_records.py`: Record cleanup utility
- `scheduled_cleanup.py`: Automatic cleanup scheduler

## Conclusion

The Job Tracker project has successfully evolved into a comprehensive system for tracking job postings across numerous company career pages. With the addition of 30+ scrapers and automatic discovery capabilities, it now provides a much broader view of the job market, particularly for data science and machine learning roles.

The system offers flexible filtering, visualization, and a clean user interface. It is designed to be maintainable with automatic data cleanup and a focus on recent job postings (last 7 days). The foundation is now in place for further enhancements and customizations to meet specific needs and preferences.
