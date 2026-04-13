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
    get_api_url
)
from app.dashboard.auth import is_authenticated
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

    # Fetch filter data (companies)
    companies_data = fetch_data("jobs/companies") or {"companies": []}

    # Time period selector with multiple selection options
    st.sidebar.subheader("Time Period")

    # Define time period options
    time_options = [
        {"label": "Today", "days": 1, "key": "today"},
        {"label": "Yesterday", "days": 1, "key": "yesterday"},
        {"label": "Last 3 days", "days": 3, "key": "days_3"},
        {"label": "Last 4 days", "days": 4, "key": "days_4"},
        {"label": "Last 5 days", "days": 5, "key": "days_5"},
        {"label": "Last 6 days", "days": 6, "key": "days_6"},
        {"label": "Last 7 days", "days": 7, "key": "days_7"},
    ]

    # Initialize session state for time filters if not present
    if "time_filters" not in st.session_state:
        st.session_state.time_filters = {"days_7": True}  # Default to 7 days

    # Create checkboxes for each time option
    selected_time_keys = []
    for option in time_options:
        key = f"time_{option['key']}"
        is_checked = st.sidebar.checkbox(
            option["label"],
            value=st.session_state.time_filters.get(option["key"], False),
            key=key
        )
        # Update session state
        st.session_state.time_filters[option["key"]] = is_checked
        if is_checked:
            selected_time_keys.append(option["key"])

    # If nothing selected, default to 7 days
    if not selected_time_keys:
        selected_time_keys = ["days_7"]
        st.session_state.time_filters = {"days_7": True}
        st.rerun()

    # Calculate the maximum days to fetch based on selected options
    max_days = 1  # Default minimum
    for option in time_options:
        if option["key"] in selected_time_keys:
            if option["key"] == "today":
                max_days = max(max_days, 1)
            elif option["key"] == "yesterday":
                max_days = max(max_days, 2)  # Need 2 days to include yesterday
            else:
                max_days = max(max_days, option["days"])

    # Store the selected days for API request
    selected_days = max_days

    # Update date range information with selected time periods
    today = datetime.now().date()
    start_date = today - timedelta(days=selected_days)

    # Create a more descriptive message about the selected time periods
    selected_time_labels = [option['label'] for option in time_options if option['key'] in selected_time_keys]
    time_periods_str = ", ".join(selected_time_labels)

    # Show both the selected time periods and the date range
    st.markdown(f"Showing jobs for: **{time_periods_str}**")
    st.markdown(f"Date range: **{start_date.strftime('%Y-%m-%d')}** to **{today.strftime('%Y-%m-%d')}**")

    # Search box
    search_term = st.sidebar.text_input("Search by Keyword")

    # Company filter (multi-select based on available data)
    companies = sorted(companies_data["companies"])
    selected_companies = st.sidebar.multiselect("Companies (select multiple)", companies, default=[])

    # Add Clear Filters button if any filters are applied
    if search_term or selected_companies:
        if st.sidebar.button("Clear All Filters"):
            st.session_state.clear()
            st.rerun()

    # Build request params
    request_params = []
    request_params.append(("days", selected_days))

    if selected_companies:
        for company in selected_companies:
            request_params.append(("company", company))

    if search_term:
        request_params.append(("search", search_term))

    request_params.append(("limit", 1000))

    # Fetch job listings with custom params
    jobs_data = fetch_data_with_params("jobs", request_params) or {"jobs": [], "total": 0}

    # Show total job count with improved styling
    total_jobs = jobs_data.get("total", 0)
    st.markdown(f"<h4 class='job-listing-header' style='margin-bottom:0; padding-bottom:0;'>Found {total_jobs} jobs matching your criteria</h4>", unsafe_allow_html=True)

    # Add analytics tracking for search
    if search_term:
        st.markdown(f"<script>trackSearch('{search_term}', {total_jobs});</script>", unsafe_allow_html=True)

    # Process data for visualization and display
    if jobs_data.get("jobs"):
        try:
            df_jobs = pd.DataFrame(jobs_data["jobs"])

            # Convert date_posted to datetime for filtering
            if "date_posted" in df_jobs.columns:
                # Log a sample of dates for debugging
                if len(df_jobs) > 0:
                    sample_dates = df_jobs["date_posted"].head(3).tolist()
                    logger.info(f"Sample date_posted values: {sample_dates}")

                # Convert to datetime
                df_jobs["date_posted"] = pd.to_datetime(df_jobs["date_posted"])

                # Log converted dates
                if len(df_jobs) > 0:
                    sample_converted = df_jobs["date_posted"].head(3).tolist()
                    logger.info(f"Sample converted dates: {sample_converted}")

                # Apply client-side time filtering based on selected time periods
                if selected_time_keys:
                    # Create a mask for each selected time period
                    date_masks = []

                    for key in selected_time_keys:
                        if key == "today":
                            # Today's jobs - use normalize() to compare just the date part
                            mask = df_jobs["date_posted"].dt.normalize() == pd.Timestamp(today)
                            date_masks.append(mask)
                            # Log for debugging
                            today_count = mask.sum()
                            logger.info(f"Today's jobs count: {today_count}")
                        elif key == "yesterday":
                            # Yesterday's jobs
                            mask = df_jobs["date_posted"].dt.normalize() == pd.Timestamp(today - timedelta(days=1))
                            date_masks.append(mask)
                            # Log for debugging
                            yesterday_count = mask.sum()
                            logger.info(f"Yesterday's jobs count: {yesterday_count}")
                        elif key.startswith("days_"):
                            # Last N days jobs
                            days = int(key.split("_")[1])
                            # Use normalize() to compare just the date part
                            cutoff_date = pd.Timestamp(today - timedelta(days=days-1))
                            mask = df_jobs["date_posted"].dt.normalize() >= cutoff_date
                            date_masks.append(mask)
                            # Log for debugging
                            days_count = mask.sum()
                            logger.info(f"Last {days} days jobs count: {days_count}")

                    # Combine all masks with OR operation
                    if date_masks:
                        combined_mask = date_masks[0]
                        for mask in date_masks[1:]:
                            combined_mask = combined_mask | mask

                        # Apply the combined filter
                        df_jobs = df_jobs[combined_mask]

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

