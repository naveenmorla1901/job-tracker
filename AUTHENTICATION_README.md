# Authentication System Documentation

This document describes the optimized authentication system implemented for the Job Tracker application.

## Overview

The authentication system provides:

- User registration and login
- Role-based access control (regular, premium, admin)
- Token refresh mechanism
- Job tracking functionality (save jobs, mark as applied)
- Protected API routes with detailed error messages
- Rate limiting to prevent brute force attacks
- Streamlit dashboard integration

## User Roles

The system supports three user roles:

1. **Regular**: Basic user with job tracking capabilities
2. **Premium**: Same as regular for now (prepared for future premium features)
3. **Admin**: Additional access to system logs and user management

## Features

### User Management

- User registration with email/password
- Login with JWT token authentication
- Password changing
- Admin-only user management

### Job Tracking

- Save jobs to user's tracked list
- Mark jobs as applied/not applied
- View personalized job listing

### Dashboard Interface

- Login/register pages
- User profile settings
- Role-based navigation
- Job tracking UI integrated with job listings

## API Endpoints

### Authentication

- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login (form-based)
- `POST /api/auth/login/json` - Login (JSON-based)
- `POST /api/auth/refresh` - Refresh authentication token
- `GET /api/auth/me` - Get current user information
- `PUT /api/auth/me` - Update current user information

### Job Tracking

- `GET /api/user/jobs` - Get user's tracked jobs
- `POST /api/user/jobs/{job_id}/track` - Track a job
- `DELETE /api/user/jobs/{job_id}/track` - Untrack a job
- `PUT /api/user/jobs/{job_id}/applied` - Mark job as applied/not applied

### Admin Endpoints

- `GET /api/auth/users` - List all users (admin only)
- `GET /api/auth/users/{user_id}` - Get specific user (admin only)
- `PUT /api/auth/users/{user_id}` - Update user (admin only)

### Health Endpoints

- `GET /api` - API root with available endpoints
- `GET /api/health` - Simple health check
- `GET /api/health/detailed` - Detailed health check with component status

## Setup Instructions

### 1. Setup Database

The authentication system adds new models to the database. Run the Alembic migration to update your database schema:

```bash
python run.py update_db
```

### 2. Create Admin User

Create an initial admin user that can manage the system:

```bash
python run.py create_admin admin@example.com your_password
```

### 3. Start the Application

Start the API and dashboard servers:

```bash
# Terminal 1: Start API
python run.py api

# Terminal 2: Start dashboard
python run.py dashboard
```

### 4. Login

Access the dashboard at http://localhost:8501 and navigate to the Login page to sign in or register.

## Technical Implementation

### Database Models

- **User**: Stores user accounts with email, hashed_password, and role
- **UserJob**: Junction table linking users to jobs they're tracking

### Authentication Flow

1. User enters credentials in login form
2. API validates credentials and returns JWT token
3. Dashboard stores token in session state
4. Subsequent API requests include token in Authorization header
5. Protected routes validate token and user permissions
6. Token can be refreshed using the /api/auth/refresh endpoint

### Security Considerations

- Passwords are hashed using bcrypt
- JWT tokens expire after 24 hours (configurable)
- Token refresh mechanism to extend sessions
- Rate limiting to prevent brute force attacks (5 auth requests per minute)
- Detailed error messages for better troubleshooting
- Admin features are protected by role-based access control
- Comprehensive logging for security auditing
- JWT secret key management through environment variables

## Development Guidelines

When adding new features:

1. Use the `auth_required` decorator for pages requiring authentication
2. Use the `admin_required` decorator for admin-only pages
3. Use the `api_request` helper function for authenticated API requests
4. Add proper error handling for authentication failures
5. Ensure proper access control on all new API endpoints

## Environment Variables

The authentication system relies on the following environment variables:

- `JWT_SECRET_KEY`: Secret key used for signing JWT tokens (IMPORTANT: set this in production)
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Token lifetime in minutes (default: 1440 - 24 hours)
- `DATABASE_URL`: Database connection string
- `ENVIRONMENT`: Application environment (development, production, test)

These variables should be set in the `.env` file at the project root or in the environment where the application is running.

## Troubleshooting

### Common Issues

1. **Login Failures**: Verify correct email/password and check API connection
2. **Access Denied**: Check if your user has the required role
3. **API Connection Issues**: Ensure the API server is running at the expected URL
4. **Token Expiration**: Use the refresh endpoint or re-login if your session has expired
5. **Rate Limiting**: If you receive 429 responses, wait before retrying
6. **Database Connection**: Verify database credentials and connection

### Authentication Errors

The system provides detailed error messages to help diagnose issues:

- "Authentication token has expired" - Use the refresh endpoint or login again
- "Invalid authentication token" - Token is malformed or signature is invalid
- "User no longer exists" - The user associated with the token has been deleted
- "This account has been deactivated" - Contact an administrator to reactivate
- "Rate limit exceeded" - Too many requests, wait and try again

### Accessing System Logs

For admin users, system logs are available from the dashboard navigation menu.
