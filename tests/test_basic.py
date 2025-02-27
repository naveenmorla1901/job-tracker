"""
Basic tests to ensure the infrastructure is working
"""
import pytest

def test_environment_setup():
    """Test that the test environment is set up correctly"""
    assert True

def test_imports():
    """Test that key modules import correctly"""
    import app
    import app.db
    import app.api
    import app.scrapers
    assert app is not None
    assert app.db is not None
    assert app.api is not None
    assert app.scrapers is not None

def test_api_connection(test_client):
    """Test that the API is accessible"""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "status" in response.json()
    assert response.json()["status"] == "ok"
