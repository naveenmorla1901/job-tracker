"""
Pytest configuration file
"""
import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set test environment variable to prevent using production database
os.environ["TESTING"] = "True"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"

# Initialize test database
TestBase = declarative_base()
test_engine = create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Import app only after setting test environment
from app.db.database import get_db
from app.db.models import Base, Job, Role
from main import app

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test"""
    # Create test database tables
    Base.metadata.create_all(bind=test_engine)
    
    # Create test session
    db = TestSessionLocal()
    
    try:
        # Add a test role
        role = Role(name="Data Scientist")
        db.add(role)
        db.commit()
        
        # Add a test job
        job = Job(
            job_id="TEST-123",
            job_title="Test Job",
            location="Test Location",
            job_url="https://example.com/job",
            company="Test Company",
            date_posted="2025-02-26",
            employment_type="Full-time",
            description="This is a test job description",
            is_active=True
        )
        
        # Add role to job
        job.roles.append(role)
        db.add(job)
        db.commit()
        
        yield test_engine
    except Exception as e:
        print(f"Error setting up test database: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
        # Drop all tables
        Base.metadata.drop_all(bind=test_engine)
        # Delete the test database file
        if os.path.exists("./test.db"):
            os.remove("./test.db")

@pytest.fixture(scope="function")
def test_client(test_db):
    """Create a test client for the FastAPI application"""
    # Override the get_db dependency
    def override_get_db():
        db = TestSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Remove the override
    app.dependency_overrides = {}
