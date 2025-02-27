"""
Basic tests that don't require database connections
"""
import os
import sys
import pytest

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_app_imports():
    """Test that we can import main modules without errors"""
    import main
    import dashboard
    import run
    assert True

def test_app_modules():
    """Test that we can import app modules without errors"""
    from app import config
    from app.db import models
    from app.db import crud
    assert True

def test_scrapers_import():
    """Test that we can import scrapers without errors"""
    from app.scrapers import base
    assert hasattr(base, 'BaseScraper')
    
    from app.scrapers.base import BaseScraper
    assert BaseScraper

def test_config():
    """Test that config values are reasonable"""
    from app import config
    assert hasattr(config, 'SQLALCHEMY_DATABASE_URL')
    assert hasattr(config, 'ENVIRONMENT')
    assert hasattr(config, 'API_HOST')
    assert hasattr(config, 'API_PORT')
