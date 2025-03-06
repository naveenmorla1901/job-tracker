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
from app.dashboard.auth import login_page, user_settings_page, user_menu, is_authenticated, is_admin, auth_required, admin_required
from app.dashboard.user_jobs import tracked_jobs_page
from app.dashboard.admin import admin_users_page

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
    
    # Setup page configuration - MUST be the first Streamlit command
    st.set_page_config(
        page_title="Job Tracker Dashboard",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Load custom CSS
    with open(os.path.join(os.path.dirname(__file__), "static", "custom.css")) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Add a custom header with base tag to help with Google Analytics
    st.markdown(
        """
        <head>
            <!-- Global site tag (gtag.js) - Google Analytics -->
            <script async src="https://www.googletagmanager.com/gtag/js?id=G-EGVJQG5M34"></script>
            <script>
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', 'G-EGVJQG5M34');
            </script>
        </head>
        """,
        unsafe_allow_html=True
    )
    
    # API URL is configured behind the scenes
    from dashboard_components.utils import get_api_url
    current_api_url = get_api_url()
    
    # Initialize session state for page navigation if not exists
    if 'page' not in st.session_state:
        st.session_state.page = 'jobs'
    
    # Display user auth menu in sidebar
    user_menu()
    
    # Add page navigation to sidebar
    st.sidebar.title("Navigation")
    
    # Different navigation options based on auth status
    if is_authenticated():
        pages = ["Jobs Dashboard", "My Tracked Jobs"]
        
        # Add admin pages if user is admin
        if is_admin():
            pages.extend(["User Management", "System Logs"])
            
        page = st.sidebar.radio("Go to", pages)
        
        # Map selected page to session state
        if page == "Jobs Dashboard":
            st.session_state.page = 'jobs'
        elif page == "My Tracked Jobs":
            st.session_state.page = 'tracked_jobs'
        elif page == "User Management" and is_admin():
            st.session_state.page = 'admin_users'
        elif page == "System Logs" and is_admin():
            st.session_state.page = 'system_logs'
    else:
        # Not authenticated, simplified menu
        pages = ["Jobs Dashboard", "Login"]
        page = st.sidebar.radio("Go to", pages)
        
        if page == "Jobs Dashboard":
            st.session_state.page = 'jobs'
        elif page == "Login":
            st.session_state.page = 'login'
    
    # Display the selected page based on session state
    current_page = st.session_state.page
    
    if current_page == 'jobs':
        display_jobs_page()
    elif current_page == 'tracked_jobs':
        tracked_jobs_page()
    elif current_page == 'admin_users':
        # Check if user is admin for protected pages
        if is_admin():
            admin_users_page()
        else:
            st.error("You don't have permission to view this page")
            st.session_state.page = 'jobs'
            st.rerun()
    elif current_page == 'system_logs':
        # Check if user is admin for protected pages
        if is_admin():
            display_logs_page()
        else:
            st.error("You don't have permission to view this page")
            st.session_state.page = 'jobs'
            st.rerun()
    elif current_page == 'login':
        login_page()
    elif current_page == 'settings':
        user_settings_page()
    else:
        # Default to jobs page
        display_jobs_page()

if __name__ == "__main__":
    main()
