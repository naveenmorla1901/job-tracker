"""
Enhanced dashboard for the Job Tracker application with dynamic filters and role visualization
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import time
import logging
import traceback

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('job_tracker.dashboard')

# Constants
API_URL = "http://localhost:8000/api"

# Helper functions
@st.cache_data(ttl=300)  # Cache data for 5 minutes
def fetch_data(endpoint, params=None):
    """Fetch data from API with optional parameters"""
    # Ensure endpoint doesn't have trailing slash for consistent URLs
    if endpoint.endswith('/'):
        endpoint = endpoint[:-1]
        
    url = f"{API_URL}/{endpoint}"
    if params:
        query_params = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
        if query_params:
            url = f"{url}?{query_params}"
    
    try:
        logger.info(f"Fetching data from: {url}")
        fetch_start = time.time()
        response = requests.get(url)
        
        # Check for redirect and log it (but still proceed)
        if response.history:
            logger.info(f"Redirected from {url} to {response.url}")
            
        response.raise_for_status()
        data = response.json()
        logger.info(f"Fetched data in {time.time() - fetch_start:.2f} seconds")
        return data
    except Exception as e:
        logger.error(f"Error fetching data from API: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def fetch_data_with_params(endpoint, params_list):
    """Fetch data from API with params as a list of tuples for multi-select support"""
    # Ensure endpoint doesn't have trailing slash for consistent URLs
    if endpoint.endswith('/'):
        endpoint = endpoint[:-1]
        
    url = f"{API_URL}/{endpoint}"
    
    try:
        logger.info(f"Fetching data from {endpoint} with params: {params_list}")
        fetch_start = time.time()
        
        # Use requests with params as a list of tuples
        # This ensures multiple values for the same key are properly encoded
        response = requests.get(url, params=params_list)
        
        # Log the actual URL for debugging
        logger.info(f"Actual request URL: {response.url}")
            
        # Check for redirect and log it (but still proceed)
        if response.history:
            logger.info(f"Redirected from {url} to {response.url}")
            
        response.raise_for_status()
        data = response.json()
        logger.info(f"Fetched data in {time.time() - fetch_start:.2f} seconds")
        return data
    except Exception as e:
        logger.error(f"Error fetching data from API: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def format_job_date(date_str):
    """Format job date with better handling of parsing and display"""
    try:
        date_obj = pd.to_datetime(date_str)
        today = pd.Timestamp.now().normalize()
        yesterday = today - pd.Timedelta(days=1)
        
        if date_obj.normalize() == today:
            return "Today"
        elif date_obj.normalize() == yesterday:
            return "Yesterday"
        else:
            return date_obj.strftime("%Y-%m-%d")
    except:
        return date_str

def main():
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
            st.experimental_rerun()
    
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
    
    # Show total job count
    total_jobs = jobs_data.get("total", 0)
    st.subheader(f"Found {total_jobs} jobs matching your criteria")
    
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
                    # 2. Date by employment type visualization
                    if "employment_type" in df_jobs.columns:
                        # Ensure employment_type exists
                        df_jobs["employment_type"] = df_jobs["employment_type"].fillna("Unknown")
                        
                        # Count jobs by date and employment type
                        df_jobs["count"] = 1
                        type_viz_df = df_jobs.groupby([
                            pd.Grouper(key="date_posted", freq="D"),
                            "employment_type"
                        ])["count"].sum().reset_index()
                        
                        # Create bar chart
                        fig2 = px.bar(
                            type_viz_df,
                            x="date_posted",
                            y="count",
                            color="employment_type",
                            title="Jobs by Employment Type",
                            labels={
                                "date_posted": "Date Posted",
                                "count": "Number of Jobs",
                                "employment_type": "Job Type"
                            }
                        )
                        
                        # Add date range
                        min_date = df_jobs["date_posted"].min()
                        max_date = df_jobs["date_posted"].max()
                        
                        # Optimize layout
                        fig2.update_layout(
                            height=350,
                            margin=dict(l=20, r=20, t=40, b=20),
                            xaxis_title="Date Posted",
                            yaxis_title="Number of Jobs",
                            legend_title="Job Type",
                            xaxis=dict(
                                range=[min_date - pd.Timedelta(hours=12), max_date + pd.Timedelta(hours=12)],
                                tickformat="%Y-%m-%d"
                            )
                        )
                        
                        # Display chart
                        st.plotly_chart(fig2, use_container_width=True)
                    else:
                        st.info("Employment type data not available for visualization")
            
            # Display job listings table
            st.subheader("Job Listings")
            
            # Prepare display columns
            display_columns = []
            for col in ["job_title", "company", "location", "date_posted", "employment_type", "roles"]:
                if col in df_jobs.columns:
                    display_columns.append(col)
            
            # Create display DataFrame
            if display_columns:
                df_display = df_jobs[display_columns].copy()
                
                # Format roles column if it exists
                if "roles" in df_display.columns:
                    df_display["roles"] = df_display["roles"].apply(
                        lambda x: ", ".join(x) if isinstance(x, list) else x
                    )
                
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
                    "roles": "Roles"
                }
                df_display = df_display.rename(columns=column_mapping)
                
                # Add apply links - ensure URLs are correct and direct to the original job posting
                apply_links = []
                for url in df_jobs["job_url"]:
                    # Clean URL and ensure it's valid
                    clean_url = url.strip() if isinstance(url, str) else ""
                    if not clean_url:
                        clean_url = "#"
                        
                    # Create HTML link that opens in new tab
                    link_html = f'<a href="{clean_url}" target="_blank" rel="noopener noreferrer">Apply</a>'
                    apply_links.append(link_html)
                
                df_display["Apply"] = apply_links
                
                # Display the table with recent jobs highlighted
                st.markdown("""
                <style>
                /* Style for Today/Yesterday highlights */
                td:contains('Today') { 
                    background-color: #e6f7e6 !important; 
                    font-weight: bold;
                }
                td:contains('Yesterday') { 
                    background-color: #f7f7e6 !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Sort by date (newest first) - depends on original order 
                # since format_job_date changes the values
                st.write(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
            else:
                st.warning("No data available to display.")
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
    try:
        api_status = requests.get(f"{API_URL}", timeout=2)
        if api_status.status_code == 200:
            st.sidebar.success("✅ API Connection: Good")
        else:
            st.sidebar.warning(f"⚠️ API Connection: Issue (Status {api_status.status_code})")
    except:
        st.sidebar.error("❌ API Connection: Failed")

if __name__ == "__main__":
    st.set_page_config(
        page_title="Job Tracker Dashboard",
        page_icon="💼",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    main()
