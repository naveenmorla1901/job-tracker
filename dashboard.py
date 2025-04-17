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
from app.dashboard.auth import login_page, user_settings_page, user_menu, is_authenticated, is_admin, auth_required, admin_required, check_for_auth_cookie
from app.dashboard.user_jobs import tracked_jobs_page
from app.dashboard.admin import admin_users_page
from app.dashboard.analytics_routes import display_analytics_page

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
    else:
        # Force API URL to port 8001 if not explicitly set
        os.environ['JOB_TRACKER_API_URL'] = 'http://localhost:8001/api'
        logger.info(f"Setting default API URL to: http://localhost:8001/api")
    
    # Setup page configuration - MUST be the first Streamlit command
    st.set_page_config(
        page_title="Job Tracker Dashboard",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Check for saved authentication cookie before rendering the rest of the page
    if not is_authenticated():
        # Try to restore session from cookie
        check_for_auth_cookie()
    
    # Load custom CSS
    with open(os.path.join(os.path.dirname(__file__), "static", "custom.css")) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        
    # Load compact CSS for more compact tables and UI elements
    compact_css_path = os.path.join(os.path.dirname(__file__), "static", "css", "compact.css")
    if os.path.exists(compact_css_path):
        with open(compact_css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Load custom JavaScript for more compact job listings
    with open(os.path.join(os.path.dirname(__file__), "static", "compact_jobs.js")) as f:
        st.markdown(f"<script>{f.read()}</script>", unsafe_allow_html=True)
        
    # Load enhanced analytics helper functions
    with open(os.path.join(os.path.dirname(__file__), "static", "analytics.js")) as f:
        st.markdown(f"<script>{f.read()}</script>", unsafe_allow_html=True)
        
    # Add analytics debug page link in development mode
    debug_link_html = f'''
    <div style="position: fixed; bottom: 10px; right: 10px; z-index: 1000;">
        <a href="{os.path.join(os.path.dirname(__file__), 'static', 'analytics_debug.html')}" 
           target="_blank" 
           style="background: #f8f9fa; color: #666; padding: 5px 10px; border-radius: 5px; 
                  text-decoration: none; font-size: 12px; border: 1px solid #ddd;">
            GA Debug
        </a>
    </div>
    '''
    st.markdown(debug_link_html, unsafe_allow_html=True)
    
    # Add enhanced Google Analytics implementation
    st.markdown(
        """
        <!-- Google tag (gtag.js) with enhanced configuration -->
        <script async src="https://www.googletagmanager.com/gtag/js?id=G-EGVJQG5M34"></script>
        <script>
            window.dataLayer = window.dataLayer || [];
            function gtag(){dataLayer.push(arguments);}
            gtag('js', new Date());
            
            // Enhanced configuration with IP anonymization and force SSL
            gtag('config', 'G-EGVJQG5M34', {
                'anonymize_ip': true,
                'transport_url': 'https://www.google-analytics.com/g/collect',
                'transport_type': 'beacon',
                'allow_google_signals': true,
                'allow_ad_personalization_signals': false,
                'cookie_domain': 'auto',
                'cookie_flags': 'SameSite=None;Secure',
                'debug_mode': true
            });
            
            console.log("Enhanced Google Analytics configuration loaded");
            
            // Better event handling for Streamlit's single-page application model
            // Track page views when content changes
            document.addEventListener('DOMContentLoaded', function() {
                // Send initial page view
                gtag('event', 'page_view', {
                    'page_title': document.title,
                    'page_location': window.location.href,
                    'page_path': window.location.pathname + window.location.search
                });
                
                // Create a more robust observer for Streamlit content changes
                const observer = new MutationObserver((mutations) => {
                    // Use debouncing to prevent multiple rapid-fire events
                    clearTimeout(window.streamlitNavTimer);
                    window.streamlitNavTimer = setTimeout(() => {
                        gtag('event', 'page_view', {
                            'page_title': document.title,
                            'page_location': window.location.href,
                            'page_path': window.location.pathname + window.location.search
                        });
                        console.log('Google Analytics page view event sent');
                    }, 300);
                });
                
                // Wait for Streamlit to fully load
                setTimeout(() => {
                    const mainContent = document.querySelector('.main');
                    if (mainContent) {
                        observer.observe(mainContent, { 
                            childList: true, 
                            subtree: true,
                            attributes: false,
                            characterData: false
                        });
                        console.log('Google Analytics enhanced tracking initialized');
                    } else {
                        console.error('Could not find Streamlit main content for GA tracking');
                    }
                }, 2000);
                
                // Also track when hash changes (can happen in Streamlit)
                window.addEventListener('hashchange', function() {
                    gtag('event', 'page_view', {
                        'page_title': document.title,
                        'page_location': window.location.href,
                        'page_path': window.location.pathname + window.location.search + window.location.hash
                    });
                });
            });
        </script>
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
        pages = ["Jobs Dashboard"]
        
        # Add admin pages if user is admin
        if is_admin():
            pages.extend(["User Management", "System Logs", "Analytics Dashboard"])
            
        page = st.sidebar.radio("Go to", pages)
        
        # Map selected page to session state
        if page == "Jobs Dashboard":
            st.session_state.page = 'jobs'
        elif page == "User Management" and is_admin():
            st.session_state.page = 'admin_users'
        elif page == "System Logs" and is_admin():
            st.session_state.page = 'system_logs'
        elif page == "Analytics Dashboard" and is_admin():
            st.session_state.page = 'analytics'
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
    elif current_page == 'analytics':
        # Check if user is admin for protected pages
        if is_admin():
            display_analytics_page()
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
