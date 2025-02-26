"""
Pytest configuration file
"""
import pytest
import os
import sys
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import Base, get_db
from app.db.models import Job, Role
from main import app

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def test_db():
    """Create a fresh database for each test"""
    Base.metadata.create_all(bind=engine)
    
    # Create test data
    db = TestingSessionLocal()
    
    # Add test roles
    role1 = Role(name="Data Scientist")
    role2 = Role(name="Software Engineer")
    db.add(role1)
    db.add(role2)
    
    # Add a test job
    job = Job(
        job_id="TEST-123",
        job_title="Test Job",
        location="Test Location",
        job_url="https://example.com/job",
        company="Test Company",
        employment_type="Full-time",
        description="This is a test job description",
        is_active=True
    )
    job.roles.append(role1)
    db.add(job)
    
    db.commit()
    db.close()
    
    yield engine
    
    # Teardown - drop all tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def test_client(test_db):
    """Create a test client for the FastAPI application"""
    # Override the get_db dependency
    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client
    
    # Remove the override
    app.dependency_overrides = {}
