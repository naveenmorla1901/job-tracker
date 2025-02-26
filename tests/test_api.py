"""
Tests for the API endpoints
"""
import pytest
from fastapi.testclient import TestClient

def test_read_root(test_client):
    """Test the root endpoint"""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()

def test_get_jobs(test_client):
    """Test the jobs endpoint"""
    response = test_client.get("/api/jobs")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert "total" in data

def test_get_jobs_with_filters(test_client):
    """Test the jobs endpoint with filters"""
    # Test role filter
    response = test_client.get("/api/jobs?role=Data%20Scientist")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    
    # Test company filter
    response = test_client.get("/api/jobs?company=Test%20Company")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert len(data["jobs"]) > 0
    
    # Test days filter
    response = test_client.get("/api/jobs?days=7")
    assert response.status_code == 200
    
    # Test combined filters
    response = test_client.get("/api/jobs?role=Data%20Scientist&company=Test%20Company&days=7")
    assert response.status_code == 200

def test_get_companies(test_client):
    """Test the companies endpoint"""
    response = test_client.get("/api/jobs/companies")
    assert response.status_code == 200
    data = response.json()
    assert "companies" in data
    assert "Test Company" in data["companies"]

def test_get_roles(test_client):
    """Test the roles endpoint"""
    response = test_client.get("/api/jobs/roles")
    assert response.status_code == 200
    data = response.json()
    assert "roles" in data
    assert "Data Scientist" in data["roles"]
    assert "Software Engineer" in data["roles"]

def test_health_check(test_client):
    """Test the health check endpoint"""
    response = test_client.get("/api")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
