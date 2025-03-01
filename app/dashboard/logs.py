"""
Logs page for the Job Tracker dashboard
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import time
import sys
import os

# Add parent directory to path to import log_manager
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from log_manager import get_log_files, read_log_content, extract_scraper_runs, cleanup_old_logs

def display_logs_page():
    """Display the logs page in the Streamlit dashboard"""
    st.title("Job Tracker Logs")
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto refresh", value=True)
    if auto_refresh:
        refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 
                                          min_value=10, 
                                          max_value=300, 
                                          value=30)
        st.sidebar.write(f"Next refresh in: {refresh_interval} seconds")
    
    # Manual refresh button
    if st.sidebar.button("Refresh Now"):
        st.experimental_rerun()
    
    # Clean up old logs
    clean_logs = st.sidebar.button("Clean Up Old Logs (> 2 days)")
    if clean_logs:
        deleted_count = cleanup_old_logs(days=2)
        st.sidebar.success(f"Deleted {deleted_count} old log files")
    
    # Get all available log files
    log_files = get_log_files()
    
    if not log_files:
        st.warning("No log files found.")
        return
    
    # Create tabs for different log views
    tab1, tab2 = st.tabs(["Scraper Runs", "Raw Logs"])
    
    with tab1:
        st.subheader("Recent Scraper Runs")
        
        # Read main log file
        main_log = "job_tracker.log"
        if main_log in log_files:
            log_content = read_log_content(main_log, max_lines=10000)
            
            # Extract scraper runs
            scraper_runs = extract_scraper_runs(log_content)
            
            if not scraper_runs:
                st.info("No scraper runs found in logs.")
            else:
                # Display runs from newest to oldest
                for i, run in enumerate(reversed(scraper_runs)):
                    if i >= 5:  # Show only last 5 runs
                        break
                        
                    # Format start time
                    start_time = run.get("start_time", "Unknown")
                    
                    with st.expander(f"Run: {start_time}", expanded=(i == 0)):
                        # Summary at the top
                        if run.get("summary"):
                            st.markdown("### Summary")
                            for line in run.get("summary", []):
                                st.text(line)
                        
                        # Show stats in a dataframe
                        if run.get("scrapers"):
                            st.markdown("### Scrapers")
                            df = pd.DataFrame(run["scrapers"])
                            
                            # Calculate duration
                            if len(run["scrapers"]) > 1:
                                start = datetime.strptime(run["scrapers"][0]["time"], "%Y-%m-%d %H:%M:%S,%f")
                                end = datetime.strptime(run["scrapers"][-1]["time"], "%Y-%m-%d %H:%M:%S,%f")
                                duration = (end - start).total_seconds()
                                st.text(f"Duration: {duration:.2f} seconds")
                            
                            # Count totals
                            total_added = sum(s["added"] for s in run["scrapers"])
                            total_updated = sum(s["updated"] for s in run["scrapers"])
                            total_expired = sum(s["expired"] for s in run["scrapers"])
                            
                            # Show totals
                            st.text(f"Total: {total_added} added, {total_updated} updated, {total_expired} expired")
                            
                            # Display scrapers with metrics
                            st.dataframe(df)
        else:
            st.warning("Main log file (job_tracker.log) not found.")
    
    with tab2:
        st.subheader("Raw Logs")
        
        # Select which log file to view
        selected_log = st.selectbox("Select Log File", log_files)
        
        # Read and display the log content
        log_content = read_log_content(selected_log)
        
        if log_content:
            # Filter options
            filter_text = st.text_input("Filter log content (case-insensitive)")
            level_filter = st.multiselect(
                "Filter by log level", 
                ["INFO", "WARNING", "ERROR", "DEBUG"],
                default=["INFO", "WARNING", "ERROR"]
            )
            
            # Apply filters
            filtered_lines = []
            for line in log_content:
                # Apply level filter
                if not any(f" {level} " in line for level in level_filter):
                    continue
                    
                # Apply text filter
                if filter_text and filter_text.lower() not in line.lower():
                    continue
                    
                filtered_lines.append(line)
            
            # Display the filtered log content
            if filtered_lines:
                st.text_area("Log Content", "".join(filtered_lines), height=500)
            else:
                st.info("No log entries match the selected filters.")
        else:
            st.warning(f"No content found in {selected_log}.")
    
    # Auto-refresh logic
    if auto_refresh:
        time.sleep(1)  # Small delay to ensure UI updates properly
        st.empty()  # Create a placeholder
        time.sleep(refresh_interval - 1)  # Wait for remaining time
        st.experimental_rerun()  # Rerun the app
