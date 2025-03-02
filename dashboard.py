"""
Enhanced dashboard for the Job Tracker application with dynamic filters and role visualization
"""
import streamlit as st
import sys
import os
import logging
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('job_tracker.dashboard')

# Add app directory to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Import dashboard components
from dashboard_components.jobs_page import display_jobs_page
from app.dashboard.logs import display_logs_page

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Job Tracker Dashboard')
    parser.add_argument('--api-url', dest='api_url', 
                        help='API URL (e.g., https://api.example.com/api)')
    return parser.parse_args()

def main():
    """Main dashboard application entry point"""
    # Parse command line arguments
    args = parse_arguments()
    
    # Set API URL from command line argument if provided
    if args.api_url:
        os.environ['JOB_TRACKER_API_URL'] = args.api_url
        logger.info(f"Using API URL from command line: {args.api_url}")
    
    # Setup page configuration
    st.set_page_config(
        page_title="Job Tracker Dashboard",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # API URL is configured behind the scenes
    from dashboard_components.utils import get_api_url
    current_api_url = get_api_url()
    
    # Add page navigation to sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Jobs Dashboard", "System Logs"])
    
    # Display the selected page
    if page == "Jobs Dashboard":
        display_jobs_page()
    elif page == "System Logs":
        display_logs_page()

if __name__ == "__main__":
    main()
