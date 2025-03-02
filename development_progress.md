# Job Tracker Project: Development Progress & Documentation

## Project Overview

The Job Tracker is a personal tool for monitoring job listings from various company career pages. It automatically scrapes job postings, stores them in a database, and provides a user-friendly dashboard for exploring opportunities.

## Technical Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: Streamlit, Plotly
- **Scheduling**: APScheduler, Schedule
- **Automation**: Python scripts for database maintenance
- **Scraping**: Requests, BeautifulSoup4
- **Monitoring**: psutil for system monitoring

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

### System Monitoring & Management
- ✅ Implemented system information monitoring dashboard
- ✅ Added log viewing capabilities with auto-refresh
- ✅ Implemented automatic log rotation and cleanup
- ✅ Added detailed project directory analysis
- ✅ Integrated process monitoring for running services

### Deployment Improvements
- ✅ Enhanced GitHub Actions deployment workflow
- ✅ Added Nginx reverse proxy configuration
- ✅ Implemented proper service management
- ✅ Added database migration during deployment

### UI/UX Enhancements
- ✅ Added dark mode toggle for dashboard
- ✅ Improved mobile responsiveness
- ✅ Added pagination for job listings
- ✅ Enhanced error handling in visualization components
- ✅ Optimized dashboard loading time

### Database & API Optimizations
- ✅ Implemented database indexing for performance
- ✅ Added proper API pagination with navigation links
- ✅ Implemented rate limiting in Nginx
- ✅ Added custom error pages for better user experience
- ✅ Created basic caching strategy for API endpoints

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
- **API Pagination**: Clean pagination with navigation links
- **Rate Limiting**: Protection against excessive requests

### Dashboard Interface
- **Time Period Selection**: 24h, 3-day, and 7-day views
- **Role Checkboxes**: Visual selection of multiple roles
- **Company Multi-select**: Choose multiple companies
- **Dual Visualizations**: Jobs by role and employment type
- **Interactive Table**: With direct application links
- **System Monitoring**: Resource usage, process tracking, and log viewing
- **Directory Analysis**: Breakdown of project structure and disk usage
- **Dark Mode**: User-selectable dark/light themes
- **Mobile Responsiveness**: Optimized layout for small screens
- **Pagination Controls**: Navigate through large result sets

### System Monitoring
- **Resource Tracking**: CPU, memory, and disk usage monitoring
- **Process Monitoring**: Track running application processes
- **Log Viewer**: View and filter application logs in real-time
- **Directory Analysis**: Size breakdown of project folders
- **Database Statistics**: Job counts, active records, and success rates

### Database Management
- **Automatic Cleanup**: Twice-daily removal of old records
- **Duplicate Handling**: Prevention of duplicate job entries
- **Role Validation**: Mapping and standardization of roles
- **Database Reset**: Complete reset capability for fresh starts
- **Log Rotation**: Automatic log rotation and cleanup
- **Database Indexing**: Optimized performance for common queries

### Scraper Capabilities
- **Extensive Company Support**: 30+ company career sites
- **Auto-Discovery**: Automatic integration of new scrapers
- **Consistent Data Format**: Standardized job data structure
- **Error Handling**: Robust error management and logging
- **Company Name Mapping**: Proper display of company names

### Deployment & DevOps
- **GitHub Actions**: Automated deployment workflow
- **Nginx Integration**: Reverse proxy for unified access
- **Service Management**: Proper service handling and monitoring
- **Environment Setup**: Automated environment configuration
- **Database Migrations**: Automated schema updates during deployment
- **Rate Limiting**: Protection against API abuse
- **Custom Error Pages**: User-friendly error messages

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

### System Monitoring Integration
We implemented comprehensive system monitoring by:
- Integrating psutil for cross-platform resource monitoring
- Creating clean visualization of system resources
- Implementing detailed directory analysis
- Setting up log rotation and automatic cleanup

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

### Dark Mode Implementation
We added a dark mode toggle feature:
- Created CSS styling for dark mode
- Added user preference toggle
- Implemented session state for preference persistence
- Optimized Plotly chart themes for dark mode

### Pagination System
We implemented a robust pagination system:
- Added pagination controls in dashboard
- Implemented backend pagination support
- Created navigation links for page traversal
- Added session state for page persistence

### Mobile Responsiveness
We improved mobile support:
- Adjusted layout based on viewport size
- Created responsive chart layouts
- Optimized table display for small screens
- Included scrollable containers for role selection

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
- **System Monitoring**: Added detailed system monitoring and log viewing
- **Deployment Process**: Improved GitHub Actions workflow and service management
- **Directory Analysis**: Detailed breakdown of project structure and disk usage
- **Dark Mode**: Added toggleable dark theme for better night-time viewing
- **Mobile Support**: Enhanced responsiveness for mobile devices
- **Pagination**: Added controls for navigating through large result sets
- **Performance**: Optimized database with proper indexing
- **API Enhancement**: Added proper pagination and rate limiting

### Potential Future Enhancements
- Email notifications for new job matches
- Application tracking functionality
- User accounts and preferences
- Mobile app version
- AI-powered job matching and recommendations
- Additional role categories
- Enhanced analytics and reporting
- Performance optimizations for larger datasets

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
- `app/api/cache.py`: Simple API caching implementation

### Frontend Components
- `dashboard.py`: Streamlit dashboard
- `app/dashboard/logs.py`: System monitoring and log viewer
- Various visualization and filtering components

### System Monitoring
- `system_info.py`: System resource monitoring utilities
- `system_info_utils.py`: Additional monitoring support functions
- `log_manager.py`: Log rotation and cleanup utilities

### Utility Scripts
- `run.py`: Command-line interface
- `reset_database.py`: Database reset utility
- `purge_old_records.py`: Record cleanup utility
- `scheduled_cleanup.py`: Automatic cleanup scheduler

### Deployment Components
- `.github/workflows/deploy.yml`: GitHub Actions deployment workflow
- `scripts/deploy.sh`: Deployment script
- `scripts/setup_nginx.sh`: Nginx configuration script
- `scripts/job-tracker-nginx.conf`: Nginx configuration template
- `scripts/setup_error_pages.sh`: Error pages setup script
- `scripts/error_pages/*.html`: Custom error page templates

## Conclusion

The Job Tracker project has successfully evolved into a comprehensive system for tracking job postings across numerous company career pages. With the addition of 30+ scrapers, automatic discovery capabilities, and detailed system monitoring, it now provides a much broader view of the job market, particularly for data science and machine learning roles.

Recent enhancements including dark mode, mobile responsiveness, pagination, database indexing, and API improvements have significantly improved the user experience and system performance. The addition of custom error pages and rate limiting has made the application more robust for production use.

The system offers flexible filtering, visualization, and a clean user interface. It is designed to be maintainable with automatic data cleanup, log rotation, and a focus on recent job postings (last 7 days). The foundation is now in place for further enhancements and customizations to meet specific needs and preferences.

The addition of system monitoring and log viewing capabilities has significantly improved the maintainability and manageability of the application, making it easier to track performance, diagnose issues, and monitor resource usage.
