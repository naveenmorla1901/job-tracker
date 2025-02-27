"""
Pytest configuration file for testing
"""
import os
import sys
import pytest
from fastapi.testclient import TestClient

# Set testing environment variable
os.environ["TESTING"] = "True"

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Skip importing database-specific modules for basic tests
# This helps avoid database connection issues during testing
# Full database tests would be run separately

@pytest.fixture
def test_client():
    """Get a test client without database dependencies"""
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    def read_root():
        return {"message": "This is a test API"}
    
    return TestClient(app)
