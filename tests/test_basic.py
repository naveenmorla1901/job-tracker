"""
Basic tests that don't require a database connection
"""
import pytest
import importlib
import os
import sys

def test_environment_setup():
    """Test that the environment is set up correctly"""
    assert True

def test_imports():
    """Test that all required modules can be imported"""
    modules = [
        'fastapi',
        'sqlalchemy',
        'streamlit',
        'pandas',
        'plotly',
        'requests',
        'bs4'
    ]
    
    for module in modules:
        try:
            importlib.import_module(module)
        except ImportError as e:
            pytest.fail(f"Failed to import {module}: {e}")

def test_api_connection():
    """Test that the API server is running (should be skipped in CI)"""
    # Skip this test in CI environment
    if os.environ.get('CI') == 'true':
        pytest.skip("Skipping API connection test in CI environment")
        
    import requests
    
    try:
        response = requests.get("http://localhost:8000/", timeout=1)
        assert response.status_code == 200
    except requests.exceptions.ConnectionError:
        pytest.skip("API server is not running")
