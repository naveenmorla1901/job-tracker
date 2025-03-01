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
        st.experimental_rerun()
    
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
            
            # Group logs by hour
            hourly_logs = {}
            
            for line in log_content:
                # Try to extract timestamp
                try:
                    # Format is typically: 2025-02-25 23:46:05,500 - ...
                    timestamp_str = line.split(" - ", 1)[0]
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    
                    if hour_key not in hourly_logs:
                        hourly_logs[hour_key] = []
                    
                    hourly_logs[hour_key].append(line)
                except:
                    # If timestamp parsing fails, add to "Unknown" hour
                    if "Unknown" not in hourly_logs:
                        hourly_logs["Unknown"] = []
                    hourly_logs["Unknown"].append(line)
            
            # Display logs grouped by hour (most recent first)
            for hour in sorted(hourly_logs.keys(), reverse=True):
                with st.expander(f"Logs from {hour}", expanded=(hour == sorted(hourly_logs.keys(), reverse=True)[0])):
                    st.text("".join(hourly_logs[hour]))
        else:
            st.warning("API log file (job_tracker.log) not found")
    
    # Read Dashboard logs
    with tab2:
        st.subheader("Dashboard Logs (dashboard.log)")
        
        # Check if dashboard log file exists
        if os.path.exists("dashboard.log"):
            # Read content
            log_content = read_log_content("dashboard.log")
            
            # Group logs by hour
            hourly_logs = {}
            
            for line in log_content:
                # Try to extract timestamp
                try:
                    # Format is typically: 2025-02-25 23:46:05,500 - ...
                    timestamp_str = line.split(" - ", 1)[0]
                    timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
                    hour_key = timestamp.strftime("%Y-%m-%d %H:00")
                    
                    if hour_key not in hourly_logs:
                        hourly_logs[hour_key] = []
                    
                    hourly_logs[hour_key].append(line)
                except:
                    # If timestamp parsing fails, add to "Unknown" hour
                    if "Unknown" not in hourly_logs:
                        hourly_logs["Unknown"] = []
                    hourly_logs["Unknown"].append(line)
            
            # Display logs grouped by hour (most recent first)
            for hour in sorted(hourly_logs.keys(), reverse=True):
                with st.expander(f"Logs from {hour}", expanded=(hour == sorted(hourly_logs.keys(), reverse=True)[0])):
                    st.text("".join(hourly_logs[hour]))
        else:
            st.warning("Dashboard log file (dashboard.log) not found")
    
    # Information about logs cleanup
    st.sidebar.info("Logs are automatically cleaned up every 2 days")
