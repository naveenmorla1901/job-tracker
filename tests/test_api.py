"""
Simplified API tests that don't require database connections
"""
import pytest

def test_read_root(test_client):
    """Test the root endpoint"""
    response = test_client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
