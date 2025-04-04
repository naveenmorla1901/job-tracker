"""
Simplified logs page for the Job Tracker dashboard
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import logging

# Add parent directory to path to import log_manager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from log_manager import get_log_files, read_log_content, cleanup_old_logs
from system_info import get_system_info, get_api_stats, format_system_info

# Configure logging
logger = logging.getLogger('job_tracker.dashboard.logs')

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
    
    # Display API logs, Dashboard logs, System info, Nginx logs, and Postgres logs in tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["API Logs", "Dashboard Logs", "System Info", "Nginx Logs", "Postgres Logs"])
    
    # Read API logs
    with tab1:
        _display_api_logs()
    
    # Read Dashboard logs
    with tab2:
        _display_dashboard_logs()
    
    # System Information
    with tab3:
        _display_system_info()
        
    # Nginx Logs
    with tab4:
        _display_nginx_logs()
    
    # Postgres Logs
    with tab5:
        _display_postgres_logs()
    
    # Information about logs cleanup
    st.sidebar.info("Logs are automatically cleaned up every 2 days")

def _display_api_logs():
    """Display API logs in a tab"""
    st.subheader("API Logs (job_tracker.log)")
    
    # Check if main log file exists
    log_files = ["job_tracker.log", "/var/log/job-tracker/api.log", "/home/ubuntu/job-tracker/job_tracker.log"]
    log_content = []
    
    for log_file in log_files:
        if os.path.exists(log_file):
            log_content.extend(read_log_content(log_file))
    
    if log_content:
        # Reverse the log content to show most recent logs first
        log_content.reverse()
        
        # Display logs in a fixed height read-only text area
        st.code("".join(log_content), language="text")
    else:
        st.warning("No API log files found")

def _display_dashboard_logs():
    """Display dashboard logs in a tab"""
    st.subheader("Dashboard Logs (dashboard.log)")
    
    # Check multiple possible log file locations
    log_files = ["dashboard.log", "/var/log/job-tracker/dashboard.log", "/home/ubuntu/job-tracker/dashboard.log"]
    log_content = []
    
    for log_file in log_files:
        if os.path.exists(log_file):
            log_content.extend(read_log_content(log_file))
    
    if log_content:
        # Reverse the log content to show most recent logs first
        log_content.reverse()
        
        # Display logs in a fixed height read-only text area
        st.code("".join(log_content), language="text")
    else:
        st.warning("No dashboard log files found")

def _display_system_info():
    """Display system information in a tab"""
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
                
                # Show comprehensive directory information
                st.markdown("#### Directory Storage Analysis")
                
                # First, show root directory total storage
                if "size_mb" in project:
                    total_size_mb = project["size_mb"]
                    total_size_gb = total_size_mb / 1024 if total_size_mb else 0
                    st.metric("Total Project Storage", f"{total_size_gb:.2f} GB ({total_size_mb:.2f} MB)")
                
                # Combine folder and subfolder information with clearer presentation
                if "folder_sizes_mb" in project and "folders_by_size" in project:
                    # Create tabs for different views
                    storage_tabs = st.tabs(["Top-Level Directories", "Subdirectories", "All"])
                    
                    # Prepare the data
                    top_folders = []
                    for folder, size in project["folders_by_size"]:
                        if folder != "root" and size > 0.1:  # Skip very small folders
                            percent = (size / total_size_mb * 100) if total_size_mb > 0 else 0
                            top_folders.append({
                                "Directory": folder,
                                "Size (MB)": size,
                                "Size (GB)": size / 1024,
                                "% of Total": f"{percent:.1f}%"
                            })
                    
                    sub_folders = []
                    if "subfolder_sizes_mb" in project and "subfolders_by_size" in project:
                        for folder, size in project["subfolders_by_size"]:
                            if size > 0.1:  # Skip very small folders
                                percent = (size / total_size_mb * 100) if total_size_mb > 0 else 0
                                sub_folders.append({
                                    "Directory": folder,
                                    "Size (MB)": size,
                                    "Size (GB)": size / 1024,
                                    "% of Total": f"{percent:.1f}%"
                                })
                    
                    # All folders combined
                    all_folders = top_folders + sub_folders
                    
                    # Display in tabs
                    with storage_tabs[0]:
                        if top_folders:
                            # Create a dataframe
                            df_top = pd.DataFrame(top_folders)
                            st.dataframe(df_top, use_container_width=True)
                            
                            # Add a bar chart for visual comparison
                            if len(top_folders) > 1:
                                st.bar_chart(df_top.set_index("Directory")["Size (MB)"])
                    
                    with storage_tabs[1]:
                        if sub_folders:
                            # Create a dataframe
                            df_sub = pd.DataFrame(sub_folders)
                            st.dataframe(df_sub, use_container_width=True)
                    
                    with storage_tabs[2]:
                        if all_folders:
                            # Create a dataframe
                            df_all = pd.DataFrame(all_folders)
                            st.dataframe(df_all, use_container_width=True)
        
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

def _display_nginx_logs():
    """Display Nginx logs in a tab"""
    st.subheader("Nginx Logs")
    
    # Check common Nginx log file locations
    log_files = ["/var/log/nginx/error.log", "/var/log/nginx/access.log"]
    
    # Use a dropdown to select which Nginx log to view
    log_type = st.radio("Select Nginx log type:", ["Error Log", "Access Log"], horizontal=True)
    
    if log_type == "Error Log":
        log_file = log_files[0]
    else:  # Access Log
        log_file = log_files[1]
    
    # Try to read the log file
    try:
        if os.path.exists(log_file):
            # Read the log file using the system command
            import subprocess
            result = subprocess.run(["sudo", "tail", "-n", "1000", log_file], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                st.code(result.stdout, language="text")
            else:
                # Try a direct file read as fallback
                try:
                    with open(log_file, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.readlines()
                        # Take last 1000 lines
                        if len(content) > 1000:
                            content = content[-1000:]
                        st.code("".join(content), language="text")
                except Exception as e:
                    st.warning(f"Could not read Nginx log file: {str(e)}\nYou may need to run the dashboard with sudo privileges to access system logs.")
        else:
            st.warning(f"Nginx log file {log_file} not found")
    except Exception as e:
        st.error(f"Error accessing Nginx logs: {str(e)}\nYou may need to run the dashboard with sudo privileges to access system logs.")

def _display_postgres_logs():
    """Display PostgreSQL logs in a tab"""
    st.subheader("PostgreSQL Logs")
    
    # Common PostgreSQL log locations
    log_paths = [
        "/var/log/postgresql/postgresql-*.log",  # Debian/Ubuntu
        "/var/lib/pgsql/data/log/*.log",         # RHEL/CentOS
        "/usr/local/var/postgres/server.log"     # macOS Homebrew
    ]
    
    # Find the actual log files
    import glob
    all_logs = []
    for path in log_paths:
        all_logs.extend(glob.glob(path))
    
    if all_logs:
        # Let user select which log file to view
        selected_log = st.selectbox("Select PostgreSQL log file:", all_logs)
        
        # Try to read the selected log file
        try:
            # Use system command to read logs with proper permissions
            import subprocess
            result = subprocess.run(["sudo", "tail", "-n", "1000", selected_log], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                st.code(result.stdout, language="text")
            else:
                # Try a direct file read as fallback
                try:
                    with open(selected_log, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.readlines()
                        # Take last 1000 lines
                        if len(content) > 1000:
                            content = content[-1000:]
                        st.code("".join(content), language="text")
                except Exception as e:
                    st.warning(f"Could not read PostgreSQL log file: {str(e)}\nYou may need to run the dashboard with sudo privileges to access system logs.")
        except Exception as e:
            st.error(f"Error accessing PostgreSQL logs: {str(e)}\nYou may need to run the dashboard with sudo privileges to access system logs.")
    else:
        # If no log files found, show a message about checking PostgreSQL processes
        st.warning("No PostgreSQL log files found at common locations")
        
        # Show PostgreSQL processes
        st.subheader("PostgreSQL Processes")
        try:
            import subprocess
            result = subprocess.run(["ps", "aux", "|", "grep", "postgres"], shell=True, capture_output=True, text=True)
            st.code(result.stdout, language="text")
        except Exception as e:
            st.error(f"Error checking PostgreSQL processes: {str(e)}")
