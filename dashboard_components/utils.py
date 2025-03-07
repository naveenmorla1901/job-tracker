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
import streamlit.components.v1 as components

# Configure logging
logger = logging.getLogger('job_tracker.dashboard.utils')

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("Loaded environment variables from .env file")
except ImportError:
    print("dotenv package not found, skipping .env loading")

def inject_google_analytics():
    """Inject Google Analytics tracking code using a dedicated HTML file"""
    try:
        # Get the absolute path to the analytics.html file
        current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        analytics_path = os.path.join(current_dir, "static", "analytics.html")
        
        # Check if the file exists before trying to read it
        if not os.path.exists(analytics_path):
            logger.error(f"Analytics HTML file not found at: {analytics_path}")
            return
        
        # Read the HTML file content
        with open(analytics_path, 'r') as f:
            html_content = f.read()
        
        # Use streamlit component to insert the HTML
        st.components.v1.html(html_content, height=1, width=1, scrolling=False)
        logger.info("Google Analytics tracking code injected successfully")
        
    except Exception as e:
        logger.error(f"Error injecting Google Analytics: {str(e)}")
        logger.error(traceback.format_exc())

# Read API URL from environment or use default
def get_api_url():
    """Get API URL from environment variable or use default localhost"""
    api_url = os.environ.get('JOB_TRACKER_API_URL', 'http://localhost:8001/api')
    
    # Remove trailing slash if present
    if api_url.endswith('/'):
        api_url = api_url[:-1]
    
    logger.info(f"Using API URL: {api_url}")
    return api_url

# Constants
API_URL = get_api_url()

@st.cache_data(ttl=60)  # Cache data for 1 minute only - reduced from 5 minutes
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
        response = requests.get(url, timeout=10)  # Added timeout
        
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
        response = requests.get(url, params=params_list, timeout=10)  # Added timeout
        
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
        
        # First try the health endpoint
        try:
            response = requests.get(f"{api_url}/health", timeout=2)
            if response.status_code == 200:
                return True, f"✅ API Connection: Good ({api_url})"
        except Exception:
            # If health endpoint fails, try the root endpoint
            try:
                response = requests.get(f"{api_url}", timeout=2)
                if response.status_code in [200, 307, 404]:  # Accept 404 as the server is running
                    return True, f"✅ API Connection: Available ({api_url})"
            except Exception as e:
                logger.error(f"API Connection Failed: {str(e)}")
                return False, f"❌ API Connection Failed: Could not connect to {api_url}"
        
        # If we got here, the health endpoint returned non-200
        return False, f"⚠️ API Connection: Issue (Status {response.status_code})"
    except Exception as e:
        api_url = get_api_url()
        logger.error(f"API Connection Failed: {str(e)}")
        return False, f"❌ API Connection Failed: Could not connect to {api_url}"
