"""
Utility functions for dashboard components
"""
import os
import streamlit as st
import requests
import time
import logging
import traceback
from datetime import datetime
import pandas as pd

# Configure logging
logger = logging.getLogger('job_tracker.dashboard.utils')

# Read API URL from environment or use default
def get_api_url():
    """Get API URL from environment variable or use default localhost"""
    return os.environ.get('JOB_TRACKER_API_URL', 'http://localhost:8000/api')

# Constants
API_URL = get_api_url()

@st.cache_data(ttl=300)  # Cache data for 5 minutes
def fetch_data(endpoint, params=None):
    """Fetch data from API with optional parameters"""
    # Ensure endpoint doesn't have trailing slash for consistent URLs
    if endpoint.endswith('/'):
        endpoint = endpoint[:-1]
    
    # Get current API URL (in case it was updated)
    api_url = get_api_url()
        
    url = f"{api_url}/{endpoint}"
    if params:
        query_params = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
        if query_params:
            url = f"{url}?{query_params}"
    
    try:
        logger.info(f"Fetching data from: {url}")
        fetch_start = time.time()
        response = requests.get(url)
        
        # Check for redirect and log it (but still proceed)
        if response.history:
            logger.info(f"Redirected from {url} to {response.url}")
            
        response.raise_for_status()
        data = response.json()
        logger.info(f"Fetched data in {time.time() - fetch_start:.2f} seconds")
        return data
    except Exception as e:
        logger.error(f"Error fetching data from API: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def fetch_data_with_params(endpoint, params_list):
    """Fetch data from API with params as a list of tuples for multi-select support"""
    # Ensure endpoint doesn't have trailing slash for consistent URLs
    if endpoint.endswith('/'):
        endpoint = endpoint[:-1]
    
    # Get current API URL (in case it was updated)
    api_url = get_api_url()
        
    url = f"{api_url}/{endpoint}"
    
    try:
        logger.info(f"Fetching data from {endpoint} with params: {params_list}")
        fetch_start = time.time()
        
        # Use requests with params as a list of tuples
        # This ensures multiple values for the same key are properly encoded
        response = requests.get(url, params=params_list)
        
        # Log the actual URL for debugging
        logger.info(f"Actual request URL: {response.url}")
            
        # Check for redirect and log it (but still proceed)
        if response.history:
            logger.info(f"Redirected from {url} to {response.url}")
            
        response.raise_for_status()
        data = response.json()
        logger.info(f"Fetched data in {time.time() - fetch_start:.2f} seconds")
        return data
    except Exception as e:
        logger.error(f"Error fetching data from API: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def format_job_date(date_str):
    """Format job date with better handling of parsing and display"""
    try:
        date_obj = pd.to_datetime(date_str)
        today = pd.Timestamp.now().normalize()
        yesterday = today - pd.Timedelta(days=1)
        
        if date_obj.normalize() == today:
            return "Today"
        elif date_obj.normalize() == yesterday:
            return "Yesterday"
        else:
            return date_obj.strftime("%Y-%m-%d")
    except:
        return date_str

def check_api_status():
    """Check if the API is available and return status"""
    try:
        # Get current API URL
        api_url = get_api_url()
        api_status = requests.get(api_url, timeout=2)
        if api_status.status_code == 200:
            return True, f"✅ API Connection: Good ({api_url})"
        else:
            return False, f"⚠️ API Connection: Issue (Status {api_status.status_code})"
    except:
        api_url = get_api_url()
        return False, f"❌ API Connection Failed: Could not connect to {api_url}"
