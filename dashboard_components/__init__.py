"""
Dashboard components for the Job Tracker application
"""
import os
import sys

# Make sure the dashboard_components directory is in the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components with error handling
try:
    from dashboard_components.utils import get_api_url, check_api_status, fetch_data, fetch_data_with_params, format_job_date
except ImportError as e:
    print(f"Error importing utils: {e}")

# Handle import of custom_jobs_table separately with error handling
try:
    from dashboard_components.custom_jobs_table import display_custom_jobs_table
except ImportError as e:
    print(f"Error importing custom_jobs_table: {e}")
    # Create a fallback function
    def display_custom_jobs_table(df_jobs):
        """Fallback function for displaying jobs"""
        import streamlit as st
        st.warning("Custom jobs table module could not be loaded. Using fallback display.")
        st.dataframe(df_jobs)

# Handle import of jobs_page
try:
    from dashboard_components.jobs_page import display_jobs_page
except ImportError as e:
    print(f"Error importing jobs_page: {e}")

__all__ = [
    'get_api_url',
    'check_api_status',
    'fetch_data',
    'fetch_data_with_params',
    'format_job_date',
    'display_custom_jobs_table',
    'display_jobs_page'
]
