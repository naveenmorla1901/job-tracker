"""
Database connection handling
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

from app.config import SQLALCHEMY_DATABASE_URL

# Set up logger
logger = logging.getLogger("job_tracker.database")

# Check if we're in testing mode
TESTING = os.environ.get("TESTING", "False").lower() in ("true", "1", "t")

if TESTING:
    # Use SQLite for testing
    logger.info("Using SQLite for testing")
    SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./test.db")
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, 
        connect_args={"check_same_thread": False}
    )
else:
    # Use PostgreSQL for production
    logger.info(f"Using database: {SQLALCHEMY_DATABASE_URL}")
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create database session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()

def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
