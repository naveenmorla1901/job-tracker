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
- **Authentication**: JWT tokens, bcrypt password hashing
- **User Management**: Role-based access control, user job tracking

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

### Authentication & User Management (Recent Updates)
- ✅ Fixed authentication error with dependencies and imports
- ✅ Enhanced token management with 24-hour expiration
- ✅ Added token refresh functionality for longer sessions
- ✅ Integrated job application tracking directly in job listings
- ✅ Added visual checkmarks for applied jobs in main table
- ✅ Streamlined navigation by consolidating tracked jobs in main view
- ✅ Implemented admin user management interface
- ✅ Added detailed error handling and logging for auth issues
- ✅ Implemented rate limiting for authentication endpoints
- ✅ Created CLI tools for user management and database viewing
- ✅ Fixed Streamlit experimental function deprecations

### UI/UX Optimizations (Recent Updates)
- ✅ Reorganized job listings table to appear at the top of the dashboard
- ✅ Added clear visual indicators for applied jobs (green checkmarks)
- ✅ Improved table styling and readability
- ✅ Simplified sidebar user menu
- ✅ Added "Mark Jobs as Applied" expander section below table
- ✅ Added better help text for user interactions
- ✅ Enhanced navigation using dashboard sections

### Authentication & User Management
- ✅ Implemented JWT-based authentication system
- ✅ Added user registration and login functionality
- ✅ Created role-based access control (regular, premium, admin)
- ✅ Implemented job tracking for users (save/apply status)
- ✅ Added user management interface for admins
- ✅ Integrated applied status directly in job listings
- ✅ Enhanced security with password hashing using bcrypt
- ✅ Added token refresh functionality
- ✅ Improved error handling for authentication failures
- ✅ Added rate limiting for authentication endpoints

### Expanded Coverage
- ✅ Added 30+ company scrapers
- ✅ Implemented auto-discovery of scrapers
- ✅ Created consistent company name display
- ✅ Focused on data science/ML roles

## Key Features Implemented

### Authentication & User Management
- **User Registration/Login**: Email and password based authentication
- **Role-Based Access**: Regular, premium, and admin user types
- **JWT Implementation**: Secure token-based authentication
- **Token Management**: Automatic refresh for long sessions
- **Job Tracking**: Save jobs and mark as applied
- **Admin Dashboard**: User management interface for admins
- **Application Tracking**: Visual checkmarks for applied jobs
- **Security Features**: Bcrypt password hashing, rate limiting
- **Error Handling**: Detailed error messages for auth issues

### API Functionality
- **Job Filtering**: By role, company, date, location, and type
- **Multi-select Support**: For roles and companies
- **Data Aggregation**: Endpoints for unique values and statistics
- **Error Handling**: Robust error handling and logging
- **API Pagination**: Clean pagination with navigation links
- **Rate Limiting**: Protection against excessive requests
- **Protected Endpoints**: Authentication required for certain operations

### Dashboard Interface
- **Time Period Selection**: 24h, 3-day, and 7-day views
- **Role Checkboxes**: Visual selection of multiple roles
- **Company Multi-select**: Choose multiple companies
- **Dual Visualizations**: Jobs by role and employment type
- **Interactive Table**: With direct application links and apply status
- **Application Tracking**: Checkmarks for applied jobs directly in table
- **Admin Dashboard**: User management interface for administrators
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
- **User Activity**: Monitor user logins and actions

### Database Management
- **Automatic Cleanup**: Twice-daily removal of old records
- **Duplicate Handling**: Prevention of duplicate job entries
- **Role Validation**: Mapping and standardization of roles
- **Database Reset**: Complete reset capability for fresh starts
- **Log Rotation**: Automatic log rotation and cleanup
- **Database Indexing**: Optimized performance for common queries
- **User Data**: Storage of user accounts and job tracking data

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
- **Authentication Workflow**: Proper JWT token handling and validation

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

# Command-line Interface Reference

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

# User Management (New)
python manage_users.py list               # List all users
python manage_users.py create <email> <password> [--role admin|premium|regular]  # Create new user
python manage_users.py info <user_id>     # View user details
python manage_users.py delete <user_id>   # Delete a user
python manage_users.py change-password <user_id> <new_password>  # Change user password
python manage_users.py change-role <user_id> <new_role>  # Change user role

# Database Viewing (New)
python view_database.py tables            # List all database tables
python view_database.py users [--limit N] # View users in database
python view_database.py jobs [--limit N] [--company COMPANY]  # View jobs
python view_database.py roles             # View roles and job counts
python view_database.py stats             # View database statistics

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
- No email notifications for new listings (still planned)
- Limited to 7-day job history to keep database manageable
- No integration with external job boards (only company career sites)
- Limited to specific role categories focused on tech

### Recent Improvements (Last Update)
- **Authentication System**: Fixed and enhanced authentication with JWT tokens
- **User Management**: Added admin interface for managing users
- **Job Application Tracking**: Integrated directly in main job table with checkmarks
- **User Experience**: Streamlined UI with better information organization
- **Command-line Tools**: New tools for user management and database viewing
- **Security Enhancements**: Rate limiting and better error handling
- **Modern UI Components**: Updated for latest Streamlit compatibility
- **Code Quality**: Fixed dependency issues and improved error handling
- **Documentation**: Updated with all new features and improvements

### Potential Future Enhancements
- Email notifications for new job matches
- Integration with external job boards (LinkedIn, Indeed, etc.)
- AI-powered job matching and recommendations
- Additional role categories beyond tech
- Enhanced analytics and reporting
- Performance optimizations for larger datasets
- Mobile app version
- Export feature for tracked jobs
- Integration with calendar for interview scheduling

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
- `dashboard_components/jobs_page.py`: Job listings and visualization
- `app/dashboard/auth.py`: Authentication and user session management
- `app/dashboard/admin.py`: Admin user management interface
- `app/dashboard/logs.py`: System monitoring and log viewer

### Authentication & User Management
- `app/auth/security.py`: JWT token handling and password hashing
- `app/auth/dependencies.py`: Authentication middleware and guards
- `app/auth/schemas.py`: User and token data models
- `app/db/crud_user.py`: User database operations
- `manage_users.py`: Command-line user management tool
- `view_database.py`: Database viewing and inspection tool

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

Recent enhancements including authentication, user management, job application tracking, command-line tools, and streamlined UI have significantly improved the user experience and system performance. The addition of security features like rate limiting and better error handling has made the application more robust for production use.

The system offers flexible filtering, visualization, and a clean user interface. It is designed to be maintainable with automatic data cleanup, log rotation, and a focus on recent job postings (last 7 days). The foundation is now in place for further enhancements and customizations to meet specific needs and preferences.

The addition of system monitoring and log viewing capabilities has significantly improved the maintainability and manageability of the application, making it easier to track performance, diagnose issues, and monitor resource usage.
