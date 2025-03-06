"""
Jobs page component for the dashboard
"""
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import logging
import traceback

from dashboard_components.utils import (
    fetch_data, 
    fetch_data_with_params, 
    format_job_date,
    check_api_status,
    get_api_url
)
from app.dashboard.auth import is_authenticated, api_request
from app.dashboard.user_jobs import add_job_tracking_buttons
from dashboard_components.custom_jobs_table import display_custom_jobs_table

# Configure logging
logger = logging.getLogger('job_tracker.dashboard.jobs_page')

def display_jobs_page():
    """Display the main jobs page in the Streamlit dashboard"""
    # Start timing the dashboard rendering
    dashboard_start = time.time()
    
    # Page header
    st.title("Job Tracker Dashboard")
    
    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Get job statistics for display
    try:
        stats = fetch_data("jobs/stats") or {}
        if stats and not stats.get("error"):
            # Create a metrics row
            metrics_cols = st.columns(3)
            metrics_cols[0].metric("Total Active Jobs", stats.get("total_active_jobs", 0))
            metrics_cols[1].metric("Added Today", stats.get("added_today", 0))
            
            # Calculate jobs by date for display
            jobs_by_date = stats.get("jobs_by_date", [])
            recent_count = sum(item.get("count", 0) for item in jobs_by_date[:3]) if jobs_by_date else 0
            metrics_cols[2].metric("Last 3 Days", recent_count)
    except Exception as e:
        logger.error(f"Error displaying job statistics: {str(e)}")
    
    # Fetch filter data (roles, companies, employment types)
    # Get existing roles from job data rather than from roles endpoint
    jobs_data_all = fetch_data("jobs", {"days": 7, "limit": 1000}) or {"jobs": []}
    
    # Extract roles from actual job data with validation
    available_roles = set()
    if jobs_data_all.get("jobs"):
        for job in jobs_data_all.get("jobs"):
            if job.get("roles"):
                for role in job.get("roles"):
                    if role and role.strip() and role != "General":
                        # Only include non-empty, non-General roles
                        available_roles.add(role.strip())
    
    # If no roles were found, add some defaults to prevent empty dropdown
    if not available_roles:
        available_roles = {"Software Engineer", "Data Scientist", "Data Analyst"}
    
    # Get companies and employment types
    companies_data = fetch_data("jobs/companies") or {"companies": []}
    employment_types_data = fetch_data("jobs/employment-types") or {"employment_types": []}
    
    # Time period selector
    period_options = {
        "Last 24 hours": 1,
        "Last 3 days": 3,
        "Last 7 days": 7,
    }
    selected_period = st.sidebar.radio("Time Period", list(period_options.keys()), index=2)  # Default to 7 days
    selected_days = period_options[selected_period]
    
    # Update date range information
    today = datetime.now().date()
    start_date = today - timedelta(days=selected_days)
    st.markdown(f"Showing jobs posted from **{start_date.strftime('%Y-%m-%d')}** to **{today.strftime('%Y-%m-%d')}**")
    
    # Search box
    search_term = st.sidebar.text_input("Search by Keyword")
    
    # Role filter (multi-select based on available data from actual jobs)
    # Show all roles directly without dropdown for better visibility
    st.sidebar.subheader("Select Roles")
    selected_roles = []
    
    # Create columns to display roles in multiple columns
    role_cols = st.sidebar.columns(2)
    sorted_roles = sorted(list(available_roles))
    half_length = len(sorted_roles) // 2 + len(sorted_roles) % 2
    
    # Display roles in two columns
    for i, role in enumerate(sorted_roles[:half_length]):
        if role_cols[0].checkbox(role, key=f"role_{i}"):
            selected_roles.append(role)
    
    for i, role in enumerate(sorted_roles[half_length:]):
        if role_cols[1].checkbox(role, key=f"role_{i+half_length}"):
            selected_roles.append(role)
    
    # Company filter (multi-select based on available data)
    companies = sorted(companies_data["companies"])
    selected_companies = st.sidebar.multiselect("Companies (select multiple)", companies, default=[])
    
    # Location filter
    location = st.sidebar.text_input("Location", "")
    
    # Employment type filter (dynamic based on available data)
    employment_types = ["All"] + sorted([t for t in employment_types_data.get("employment_types", []) if t])
    selected_employment_type = st.sidebar.selectbox("Employment Type", employment_types)
    
    # Add Clear Filters button if any filters are applied
    if search_term or selected_roles or selected_companies or location or selected_employment_type != "All":
        if st.sidebar.button("Clear All Filters"):
            st.session_state.clear()
            st.rerun()
    
    # Create requests-compatible params
    # For single parameters, use simple key-value
    # For lists (multi-select), use multiple instances of the same key
    request_params = []
    
    # Add days parameter
    request_params.append(("days", selected_days))
    
    # Add multi-select filters if any options are selected
    if selected_roles:
        for role in selected_roles:
            request_params.append(("role", role))
    
    if selected_companies:
        for company in selected_companies:
            request_params.append(("company", company))
            
    if location:
        request_params.append(("location", location))
        
    if selected_employment_type != "All":
        request_params.append(("employment_type", selected_employment_type))
        
    if search_term:
        request_params.append(("search", search_term))
    
    # Add limit parameter to get more results
    request_params.append(("limit", 1000))
    
    # Fetch job listings with custom params
    jobs_data = fetch_data_with_params("jobs", request_params) or {"jobs": [], "total": 0}
    
    # Show total job count with improved styling
    total_jobs = jobs_data.get("total", 0)
    st.markdown(f"<h4 class='job-listing-header' style='margin-bottom:0; padding-bottom:0;'>Found {total_jobs} jobs matching your criteria</h4>", unsafe_allow_html=True)
    
    # Process data for visualization and display
    if jobs_data.get("jobs"):
        try:
            df_jobs = pd.DataFrame(jobs_data["jobs"])
            
            # Create visualizations
            if "date_posted" in df_jobs.columns:
                # Convert to datetime
                df_jobs["date_posted"] = pd.to_datetime(df_jobs["date_posted"])
                
                # Setup the visualization layout
                viz_col1, viz_col2 = st.columns(2)
                
                with viz_col1:
                    # 1. Date by roles visualization
                    if "roles" in df_jobs.columns:
                        # Explode roles to handle multiple roles per job
                        roles_df = df_jobs.explode("roles")
                        
                        # Count by date and role
                        roles_df["count"] = 1
                        roles_viz_df = roles_df.groupby([
                            pd.Grouper(key="date_posted", freq="D"),
                            "roles"
                        ])["count"].sum().reset_index()
                        
                        # Only keep the top 7 roles for clarity
                        top_roles = roles_df["roles"].value_counts().nlargest(7).index.tolist()
                        roles_viz_df = roles_viz_df[roles_viz_df["roles"].isin(top_roles)]
                        
                        # Create bar chart
                        fig1 = px.bar(
                            roles_viz_df,
                            x="date_posted",
                            y="count",
                            color="roles",
                            title=f"Jobs by Role (Top {len(top_roles)})",
                            labels={
                                "date_posted": "Date Posted",
                                "count": "Number of Jobs",
                                "roles": "Job Role"
                            }
                        )
                        
                        # Add date range
                        min_date = df_jobs["date_posted"].min()
                        max_date = df_jobs["date_posted"].max()
                        
                        # Optimize layout
                        fig1.update_layout(
                            height=350,
                            margin=dict(l=20, r=20, t=40, b=20),
                            xaxis_title="Date Posted",
                            yaxis_title="Number of Jobs",
                            legend_title="Job Role",
                            xaxis=dict(
                                range=[min_date - pd.Timedelta(hours=12), max_date + pd.Timedelta(hours=12)],
                                tickformat="%Y-%m-%d"
                            )
                        )
                        
                        # Display chart
                        st.plotly_chart(fig1, use_container_width=True)
                    else:
                        st.info("Role data not available for visualization")
                
                with viz_col2:
                    # 2. Jobs per company heatmap visualization
                    if "company" in df_jobs.columns:
                        # Count jobs by company
                        company_counts = df_jobs["company"].value_counts().reset_index()
                        company_counts.columns = ["company", "count"]
                        
                        # Get top companies for better visualization
                        top_companies = company_counts.nlargest(15, "count")
                        
                        # Create heatmap-style visualization
                        fig2 = px.treemap(
                            top_companies,
                            path=["company"],
                            values="count",
                            color="count",
                            color_continuous_scale="blues",
                            title="Jobs per Company (Top 15)",
                        )
                        
                        # Update layout for better appearance
                        fig2.update_layout(
                            height=350,
                            margin=dict(l=20, r=20, t=40, b=20),
                        )
                        
                        # Update treemap text for better readability
                        fig2.update_traces(
                            textinfo="label+value",
                            hovertemplate="<b>%{label}</b><br>Jobs: %{value}<extra></extra>"
                        )
                        
                        # Display chart
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Company data not available for visualization")
            
            # Display job listings table using our custom component
            display_custom_jobs_table(df_jobs)
        except Exception as e:
            st.error(f"Error processing job data: {str(e)}")
            logger.error(f"Error processing job data: {str(e)}")
            logger.error(traceback.format_exc())
    else:
        st.info("No job listings match your criteria")
    
    # Performance statistics
    dashboard_time = time.time() - dashboard_start
    logger.info(f"Dashboard rendered in {dashboard_time:.2f} seconds")
    
    st.sidebar.write("---")
    st.sidebar.info(f"Dashboard loaded in {dashboard_time:.2f} seconds")
    
    # Add API connection status
    api_status, status_message = check_api_status()
    if api_status:
        st.sidebar.success(status_message)
    else:
        st.sidebar.error(status_message)

def _display_jobs_table(df_jobs):
    """Helper function to display jobs table with formatting"""
    # Use a more direct approach to eliminate the gap
    st.markdown("<h3 class='job-listing-header' style='margin-bottom:0; padding-bottom:0;'>Job Listings</h3>", unsafe_allow_html=True)
    
    # Prepare display columns
    display_columns = []
    for col in ["job_title", "company", "location", "date_posted", "employment_type"]:
        if col in df_jobs.columns:
            display_columns.append(col)
    
    # Create display DataFrame
    if display_columns:
        df_display = df_jobs[display_columns].copy()
        
        # Format date column with human-friendly display
        if "date_posted" in df_display.columns:
            df_display["date_posted"] = df_display["date_posted"].apply(format_job_date)
        
        # Rename columns for display
        column_mapping = {
            "job_title": "Job Title",
            "company": "Company",
            "location": "Location",
            "date_posted": "Posted",
            "employment_type": "Type",
        }
        df_display = df_display.rename(columns=column_mapping)
        
        # Get user's tracked jobs if authenticated
        tracked_jobs = {}
        if is_authenticated():
            user_jobs = api_request("user/jobs")
            if user_jobs:
                for job in user_jobs:
                    tracked_jobs[job['id']] = {
                        'is_tracked': True,
                        'is_applied': job['tracking'].get('is_applied', False)
                    }
        
        # Add Applied column if user is authenticated
        if is_authenticated():
            # Add an Applied column with checkboxes
            applied_status = []
            for i, row in df_jobs.iterrows():
                job_id = row['id']
                job_status = tracked_jobs.get(job_id, {'is_tracked': False, 'is_applied': False})
                
                # Create a checkbox for applied status with onclick handler
                checkbox_html = f'<input type="checkbox" id="applied_{job_id}" name="applied_{job_id}" value="applied" {"checked" if job_status["is_applied"] else ""} onclick="handleCheckboxChange({job_id}, this.checked)"/>'
                applied_status.append(checkbox_html)
            
            df_display["Applied"] = applied_status
        
        # Add apply and track links
        actions = []
        for i, job in df_jobs.iterrows():
            job_id = job["id"]
            job_url = job["job_url"].strip() if isinstance(job["job_url"], str) else "#"
            
            # Check if job is tracked
            job_status = tracked_jobs.get(job_id, {'is_tracked': False, 'is_applied': False})
            
            # Create HTML for actions - only include Apply button
            action_html = f'<a href="{job_url}" target="_blank" class="action-btn apply-btn">Apply</a>'
            
            actions.append(action_html)
        
        df_display["Actions"] = actions
        
        # Set a height for the scrollable area
        st.markdown("""
        <style>
        /* Fix spacing between heading and table */
        h3 {
            margin-bottom: 0px !important;
            padding-bottom: 0px !important;
        }

        .dataframe-container {
            height: 600px;
            overflow-y: auto;
            margin-top: 0;
            margin-bottom: 10px;
            padding-top: 0 !important;
        }
        
        /* Force content together with no gaps */
        .stMarkdown > div > p {
            margin-bottom: 0px !important;
            padding-bottom: 0px !important;
        }
        
        /* Streamlit adds this element that causes spacing */
        .stMarkdown + div {
            margin-top: 0px !important;
        }

        /* Table styling */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 0 !important;
        }

        /* Cell styling */
        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 150px;
        }

        /* Header styling - make sure text is clearly visible */
        th {
            background-color: #1E1E1E !important;
            color: white !important;
            position: sticky;
            top: 0;
            z-index: 10;
            font-weight: bold;
        }

        /* Alternating row colors */
        tr:nth-child(even) {
            background-color: rgba(240, 240, 240, 0.1);
        }
        tr:nth-child(odd) {
            background-color: rgba(255, 255, 255, 0.05);
        }

        /* Hover effect */
        tr:hover {
            background-color: rgba(200, 200, 200, 0.2);
        }

        /* Ensure text in cells is visible against dark background */
        td {
            color: white;
        }
        
        /* Style action buttons */
        .action-btn {
            padding: 3px 8px;
            margin: 2px;
            border-radius: 4px;
            text-decoration: none;
            display: inline-block;
            text-align: center;
            cursor: pointer;
            font-size: 0.8em;
            border: none;
        }
        
        .apply-btn {
            background-color: #4CAF50;
            color: white;
        }
        
        .track-btn {
            background-color: #2196F3;
            color: white;
        }
        
        /* Style for checkboxes */
        input[type="checkbox"] {
            width: 18px;
            height: 18px;
            cursor: pointer;
        }

        /* Remove extra spacing */
        .stMarkdown {
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* Eliminate spacing between elements */
        .block-container {
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        
        /* Reduce spacing for all elements */
        div.element-container {
            margin-top: 0 !important;
            margin-bottom: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
        }
        </style>
        <div class="dataframe-container">
        """, unsafe_allow_html=True)
        
        # Add JavaScript for interactive elements
        js_code = """
        <script>
        // Run this code when page loads to ensure checkboxes sync with database
        document.addEventListener('DOMContentLoaded', function() {
            // Find all applied checkboxes
            const checkboxes = document.querySelectorAll('input[type="checkbox"][id^="applied_"]');
            
            // Fetch user's tracked jobs data to ensure checkboxes accurately reflect database state
            fetch('/api/user/jobs', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            })
            .then(response => response.json())
            .then(jobs => {
                if (jobs && Array.isArray(jobs)) {
                    // Create a map of job IDs to application status
                    const jobStatusMap = {};
                    jobs.forEach(job => {
                        jobStatusMap[job.id] = job.tracking && job.tracking.is_applied || false;
                    });
                    
                    // Update checkboxes to match database state
                    checkboxes.forEach(checkbox => {
                        const jobId = checkbox.id.split('_')[1];
                        if (jobStatusMap.hasOwnProperty(jobId)) {
                            checkbox.checked = jobStatusMap[jobId];
                        }
                    });
                }
            })
            .catch(error => {
                console.error('Error fetching jobs:', error);
            });
        });
        // Get the authentication token from localStorage, which was set during login
        function getAuthToken() {
            return localStorage.getItem('job_tracker_token') || '';
        }
        
        // Function to handle checkbox changes (applied/not applied)
        function handleCheckboxChange(jobId, isChecked) {
            console.log(`Job ${jobId} application status changed to ${isChecked}`);
            
            // First ensure job is tracked
            ensureJobTracked(jobId).then(isTracked => {
                if (isTracked) {
                    // Now update the applied status
                    updateAppliedStatus(jobId, isChecked);
                } else {
                    console.error('Job must be tracked before marking as applied');
                }
            });
        }
        
        // Ensure a job is tracked before updating applied status
        async function ensureJobTracked(jobId) {
            // Check if job is already tracked
            try {
                const response = await fetch(`/api/user/jobs/${jobId}`, {
                    method: 'GET',
                    headers: {
                        'Authorization': `Bearer ${getAuthToken()}`
                    }
                });
                
                if (response.ok) {
                    return true; // Job is already tracked
                }
                
                // If not found/tracked, track it now
                const trackResponse = await fetch(`/api/user/jobs/${jobId}/track`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${getAuthToken()}`
                    }
                });
                
                return trackResponse.ok;
            } catch (error) {
                console.error('Error ensuring job is tracked:', error);
                return false;
            }
        }
        
        // Function to track a job
        function trackJob(jobId) {
            // Use fetch API to track the job
            fetch(`/api/user/jobs/${jobId}/track`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            })
            .then(response => {
                if (response.ok) {
                    // Reload the page to reflect changes
                    window.location.reload();
                } else {
                    alert('Failed to track job. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            });
        }
        
        // Function to remove job tracking
        function removeJob(jobId) {
            // Use fetch API to remove tracking
            fetch(`/api/user/jobs/${jobId}/track`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${getAuthToken()}`
                }
            })
            .then(response => {
                if (response.ok) {
                    // Reload the page to reflect changes
                    window.location.reload();
                } else {
                    alert('Failed to untrack job. Please try again.');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
            });
        }
        
        // Function to update applied status
        function updateAppliedStatus(jobId, isApplied) {
            // Use fetch API to update applied status
            fetch(`/api/user/jobs/${jobId}/applied`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${getAuthToken()}`
                },
                body: JSON.stringify({ applied: isApplied })
            })
            .then(response => {
                if (!response.ok) {
                    alert('Failed to update applied status. Please try again.');
                    // Revert checkbox if update failed
                    const checkbox = document.getElementById(`applied_${jobId}`);
                    if (checkbox) {
                        checkbox.checked = !isApplied;
                    }
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
                // Revert checkbox on error
                const checkbox = document.getElementById(`applied_${jobId}`);
                if (checkbox) {
                    checkbox.checked = !isApplied;
                }
            });
        }
        </script>
        """
        
        # Display the table with JavaScript and no extra spacing
        # First, close the container div that holds previous content
        st.markdown("</div>\n<div style='margin-top:-50px; padding-top:0;'>\n" + 
                   df_display.to_html(escape=False, index=False) + js_code + "\n</div>", 
                   unsafe_allow_html=True)
        
        # Close the scrollable container
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Create interactive job application status checkboxes with expander
        if is_authenticated():
            with st.expander("Mark Jobs as Applied", expanded=False):
                st.markdown("### Update Application Status")
                st.markdown("Use these checkboxes to mark jobs you've applied to:")
                
                # Create a grid layout for job application checkboxes
                num_jobs = len(df_jobs)
                cols_per_row = 3
                
                for idx in range(0, num_jobs, cols_per_row):
                    cols = st.columns(cols_per_row)
                    
                    for col_idx in range(cols_per_row):
                        job_idx = idx + col_idx
                        if job_idx < num_jobs:
                            job = df_jobs.iloc[job_idx]
                            job_id = job['id']
                            job_status = tracked_jobs.get(job_id, {'is_tracked': False, 'is_applied': False})
                            
                            with cols[col_idx]:
                                # Only show checkbox if job is tracked or if we're showing all jobs
                                job_title = job['job_title']
                                if len(job_title) > 30:
                                    job_title = job_title[:27] + "..."
                                
                                # If job is not tracked, first need to track it
                                is_applied = st.checkbox(
                                    f"{job_title} ({job['company']})", 
                                    value=job_status['is_applied'],
                                    key=f"applied_{job_id}"
                                )
                                
                                # If status changed, update it
                                if is_applied != job_status['is_applied']:
                                    # If job is not tracked yet, track it first
                                    if not job_status['is_tracked']:
                                        track_result = api_request(
                                            f"user/jobs/{job_id}/track",
                                            method="POST"
                                        )
                                        if not track_result:
                                            st.error(f"Failed to track job: {job_title}")
                                            continue
                                    
                                    # Update application status
                                    result = api_request(
                                        f"user/jobs/{job_id}/applied",
                                        method="PUT",
                                        data={"applied": is_applied}
                                    )
                                    
                                    if result:
                                        st.success(f"Updated status for: {job_title}")
                                        # Update local status for display purposes
                                        tracked_jobs[job_id] = {
                                            'is_tracked': True,
                                            'is_applied': is_applied
                                        }
                                    else:
                                        st.error(f"Failed to update status for: {job_title}")
    else:
        st.warning("No data available to display.")
