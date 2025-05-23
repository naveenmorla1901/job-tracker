"""
Configuration settings for the Job Tracker application
"""
import os
from pathlib import Path
from dotenv import load_dotenv
# from app.config import SQLALCHEMY_DATABASE_URL as SQLALCHEMY_DATABASE_URL
# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
DEBUG = ENVIRONMENT == "development"

# Database settings - with fallback to SQLite for tests if PostgreSQL unavailable
DEFAULT_DB_URL = "postgresql://postgres:1901@localhost/job_tracker"

if ENVIRONMENT == "test":
    # Use provided DATABASE_URL or SQLite for testing
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
else:
    # Use provided DATABASE_URL or default PostgreSQL for development
    SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# API settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Dashboard settings
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8501"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Directory settings
BASE_DIR = Path(__file__).parent.parent
LOGS_DIR = BASE_DIR / "logs"

# Ensure logs directory exists
LOGS_DIR.mkdir(exist_ok=True)
