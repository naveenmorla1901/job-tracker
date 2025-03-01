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
                    cores = f"{system_info['cpu'].get('count_physical', 0)} physical, {system_info['cpu'].get('count_logical', 0)} logical"
                    st.metric("CPU Usage", f"{cpu_usage:.1f}%", f"{cores} cores")
                
                # Memory Usage
                if "memory" in system_info and "used_percent" in system_info["memory"]:
                    memory_usage = system_info["memory"]["used_percent"]
                    memory_total = system_info["memory"].get("total_mb", 0) / 1024  # Convert to GB
                    memory_used = system_info["memory"].get("used_mb", 0) / 1024  # Convert to GB
                    st.metric("Memory Usage", f"{memory_usage:.1f}%", f"{memory_used:.1f} GB of {memory_total:.1f} GB")
                
                # Disk Usage
                if "disk" in system_info and "root" in system_info["disk"]:
                    disk_usage = system_info["disk"]["root"]["used_percent"]
                    disk_total = system_info["disk"]["root"]["total_gb"]
                    disk_used = system_info["disk"]["root"]["used_gb"]
                    st.metric("Disk Usage", f"{disk_usage:.1f}%", f"{disk_used:.1f} GB of {disk_total:.1f} GB")
                
                # System Uptime
                if "uptime" in system_info and "uptime_formatted" in system_info["uptime"]:
                    st.metric("System Uptime", system_info["uptime"]["uptime_formatted"])
                    
                # Running Processes
                if "processes" in system_info:
                    processes = system_info["processes"]
                    process_count = processes.get("total_count", 0)
                    
                    # Count app-specific processes
                    app_process_count = 0
                    if "application_processes" in processes:
                        for proc_type, procs in processes["application_processes"].items():
                            app_process_count += len(procs)
                            
                    st.metric("Running Processes", f"{process_count}", f"{app_process_count} application processes")
                
                # Directory Structure
                if "project" in system_info:
                    project = system_info["project"]
                    
                    # Show both main folders and subfolders
                    st.markdown("#### Directory Sizes")
                    
                    # Combine folder and subfolder information
                    all_folders = []
                    
                    # Add top-level folders
                    if "folder_sizes_mb" in project:
                        for folder, size in project["folders_by_size"]:
                            if folder != "root" and size > 0.1:  # Skip very small folders
                                folder_type = "Directory"
                                all_folders.append({"Path": folder, "Size (MB)": size, "Type": folder_type})
                    
                    # Add sub-folders
                    if "subfolder_sizes_mb" in project:
                        for folder, size in project["subfolders_by_size"]:
                            if size > 0.1:  # Skip very small folders
                                folder_type = "Subdirectory"
                                all_folders.append({"Path": folder, "Size (MB)": size, "Type": folder_type})
                                
                    if all_folders:
                        folder_df = pd.DataFrame(all_folders)
                        st.dataframe(folder_df, use_container_width=True)
            
            with col2:
                st.markdown("### Application Stats")
                
                # Database Stats
                if "database" in api_stats:
                    db_stats = api_stats["database"]
                    total_jobs = db_stats.get("total_jobs", 0)
                    st.metric("Total Jobs", total_jobs)
                    st.metric("Active Jobs", total_jobs)  # Show total as active
                    st.metric("Companies", db_stats.get("companies", 0))
                    
                    # Scraper success rate
                    if "success_rate" in db_stats:
                        st.metric("Scraper Success Rate", f"{db_stats['success_rate']:.1f}%")
                
                # Project Information
                if "project" in system_info:
                    project_size = system_info["project"].get("size_mb", 0)
                    file_count = system_info["project"].get("file_count", 0)
                    
                    st.metric("Project Size", f"{project_size:.1f} MB", f"{file_count} files")
                    
                    # Log files size
                    log_size = 0
                    log_count = 0
                    
                    if "logs_size_mb" in project:
                        log_size = project["logs_size_mb"]
                        log_count = project["logs_count"]
                    
                    if "main_log_files" in project:
                        for log_name, log_info in project["main_log_files"].items():
                            log_size += log_info["size_mb"]
                            log_count += 1
                            
                    st.metric("Log Files Size", f"{log_size:.1f} MB", f"{log_count} files")
                
                # Show running application processes
                if "processes" in system_info and "application_processes" in system_info["processes"]:
                    app_processes = system_info["processes"]["application_processes"]
                    
                    st.markdown("#### Running Application Processes")
                    
                    # Convert to a list for display
                    process_list = []
                    for proc_type, processes in app_processes.items():
                        for proc in processes:
                            process_list.append({
                                "Type": proc_type,
                                "PID": proc["pid"],
                                "Memory (MB)": proc.get("memory_mb", 0),
                                "CPU (%)": proc.get("cpu_percent", 0)
                            })
                    
                    if process_list:
                        process_df = pd.DataFrame(process_list)
                        st.dataframe(process_df, use_container_width=True)
                    else:
                        st.info("No application processes detected")
            
            # Detailed system information
            with st.expander("View Detailed System Information", expanded=False):
                formatted_info = format_system_info(system_info)
                st.text(formatted_info)
                
        except Exception as e:
            st.error(f"Error getting system information: {str(e)}")
    
    # Information about logs cleanup
    st.sidebar.info("Logs are automatically cleaned up every 2 days")
