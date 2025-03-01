"""
Simplified logs page for the Job Tracker dashboard
"""
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import time
import sys
import os
import glob

# Add parent directory to path to import log_manager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from log_manager import get_log_files, read_log_content, cleanup_old_logs

def display_logs_page():
    """Display a simplified logs page in the Streamlit dashboard"""
    st.title("System Logs")
    
    # Add refresh button at the top
    if st.button("Refresh Logs"):
        st.rerun()  # Using st.rerun() instead of deprecated experimental_rerun
    
    # Clean up old logs
    st.sidebar.title("Log Management")
    if st.sidebar.button("Clean Up Old Logs (> 2 days)"):
        deleted_count = cleanup_old_logs(days=2)
        st.sidebar.success(f"Deleted {deleted_count} old log files")
    
    # Display API logs and Dashboard logs in tabs
    tab1, tab2 = st.tabs(["API Logs", "Dashboard Logs"])
    
    # Read API logs
    with tab1:
        st.subheader("API Logs (job_tracker.log)")
        
        # Check if main log file exists
        if os.path.exists("job_tracker.log"):
            # Read content
            log_content = read_log_content("job_tracker.log")
            
            # Reverse the log content to show most recent logs first
            log_content.reverse()
            
            # Display logs in a fixed height text area
            st.text_area("Recent logs first:", "".join(log_content), height=600)
            
        else:
            st.warning("API log file (job_tracker.log) not found")
    
    # Read Dashboard logs
    with tab2:
        st.subheader("Dashboard Logs (dashboard.log)")
        
        # Check if dashboard log file exists
        if os.path.exists("dashboard.log"):
            # Read content
            log_content = read_log_content("dashboard.log")
            
            # Reverse the log content to show most recent logs first
            log_content.reverse()
            
            # Display logs in a fixed height text area
            st.text_area("Recent logs first:", "".join(log_content), height=600)
            
        else:
            st.warning("Dashboard log file (dashboard.log) not found")
    
    # Information about logs cleanup
    st.sidebar.info("Logs are automatically cleaned up every 2 days")
