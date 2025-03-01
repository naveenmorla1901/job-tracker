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
from system_info import get_system_info, get_api_stats, format_system_info

def display_logs_page():
    """Display a simplified logs page in the Streamlit dashboard"""
    st.title("System Logs & Information")
    
    # Add refresh button at the top
    if st.button("Refresh Data"):
        st.rerun()
    
    # Clean up old logs
    st.sidebar.title("Log Management")
    if st.sidebar.button("Clean Up Old Logs (> 2 days)"):
        deleted_count = cleanup_old_logs(days=2)
        st.sidebar.success(f"Deleted {deleted_count} old log files")
    
    # Display API logs, Dashboard logs, and System info in tabs
    tab1, tab2, tab3 = st.tabs(["API Logs", "Dashboard Logs", "System Info"])
    
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
    
    # System Information
    with tab3:
        st.subheader("System Information")
        
        # Get system info
        try:
            refresh_system_info = st.checkbox("Auto-refresh system info", value=False)
            
            # Add a timestamp
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.caption(f"Last updated: {current_time}")
            
            # Get system information
            system_info = get_system_info()
            api_stats = get_api_stats()
            
            # Create columns for layout
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("### Server Resources")
                
                # CPU Usage
                if "cpu" in system_info and "used_percent" in system_info["cpu"]:
                    cpu_usage = system_info["cpu"]["used_percent"]
                    st.metric("CPU Usage", f"{cpu_usage:.1f}%")
                
                # Memory Usage
                if "memory" in system_info and "used_percent" in system_info["memory"]:
                    memory_usage = system_info["memory"]["used_percent"]
                    memory_total = system_info["memory"].get("total_mb", 0) / 1024  # Convert to GB
                    st.metric("Memory Usage", f"{memory_usage:.1f}%", f"{memory_total:.1f} GB Total")
                
                # Disk Usage
                if "disk" in system_info and "root" in system_info["disk"]:
                    disk_usage = system_info["disk"]["root"]["used_percent"]
                    disk_total = system_info["disk"]["root"]["total_gb"]
                    st.metric("Disk Usage", f"{disk_usage:.1f}%", f"{disk_total:.1f} GB Total")
                
                # System Uptime
                if "uptime" in system_info and "uptime_formatted" in system_info["uptime"]:
                    st.metric("System Uptime", system_info["uptime"]["uptime_formatted"])
            
            with col2:
                st.markdown("### Application Stats")
                
                # Project Information
                if "project" in system_info:
                    project_size = system_info["project"].get("size_mb", 0)
                    st.metric("Project Size", f"{project_size:.1f} MB")
                    
                    # Log files size
                    log_size = 0
                    if "log_files" in system_info["project"]:
                        for log_name, log_info in system_info["project"]["log_files"].items():
                            log_size += log_info["size_mb"]
                    st.metric("Log Files Size", f"{log_size:.1f} MB")
                
                # Network Status
                if "network" in system_info:
                    api_running = system_info["network"].get("api_port_active", False)
                    dashboard_running = system_info["network"].get("dashboard_port_active", False)
                    
                    st.metric("API Service", "✅ Running" if api_running else "❌ Not Running")
                    st.metric("Dashboard Service", "✅ Running" if dashboard_running else "❌ Not Running")
                
                # Database Stats
                if "database" in api_stats:
                    db_stats = api_stats["database"]
                    st.metric("Total Jobs", db_stats.get("total_jobs", 0))
                    st.metric("Active Jobs", db_stats.get("active_jobs", 0))
                    st.metric("Companies", db_stats.get("companies", 0))
                    
                    # Scraper success rate
                    if "success_rate" in db_stats:
                        st.metric("Scraper Success Rate", f"{db_stats['success_rate']:.1f}%")
            
            # Detailed system information
            with st.expander("View Detailed System Information", expanded=False):
                formatted_info = format_system_info(system_info)
                st.text(formatted_info)
            
            # Auto-refresh if enabled
            if refresh_system_info:
                time.sleep(5)
                st.rerun()
                
        except Exception as e:
            st.error(f"Error getting system information: {str(e)}")
    
    # Information about logs cleanup
    st.sidebar.info("Logs are automatically cleaned up every 2 days")
