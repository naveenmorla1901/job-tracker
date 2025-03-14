# app/dashboard/user_jobs.py
import streamlit as st
import pandas as pd
from datetime import datetime
import logging

from app.dashboard.auth import api_request, auth_required, get_current_user

# Configure logging
logger = logging.getLogger("job_tracker.dashboard.user_jobs")

@auth_required
def tracked_jobs_page():
    """Display and manage the user's tracked jobs"""
    st.title("My Tracked Jobs")
    
    # Fetch tracked jobs
    tracked_jobs = api_request("user/jobs")
    if not tracked_jobs:
        st.info("You haven't tracked any jobs yet. Browse the job listings and save jobs to track them here.")
        return
    
    # Create DataFrame for display
    df = pd.DataFrame(tracked_jobs)
    
    # Apply filters
    st.subheader("Filters")
    col1, col2 = st.columns(2)
    
    with col1:
        applied_filter = st.checkbox("Show only applied jobs")
    
    # Filter if needed
    if applied_filter:
        df = df[df["tracking"].apply(lambda x: x.get("is_applied", False) == True)]
    
    if len(df) == 0:
        st.info("No jobs match your current filters.")
        return
    
    # Load compact CSS styling
    import os
    css_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                          "static", "css", "compact.css")
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        
    # Display jobs
    st.subheader(f"Your Tracked Jobs ({len(df)})")
    
    # Apply more compact job styling
    st.markdown('''
    <style>
    .job-container {
        margin-bottom: 0.5rem !important;
        padding: 0.3rem !important;
    }
    </style>
    ''', unsafe_allow_html=True)
    
    for index, row in df.iterrows():
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"### [{row['job_title']}]({row['job_url']})")
                st.markdown(f"**{row['company']}** | {row['location']}")
                st.markdown(f"Posted: {row['date_posted'].split('T')[0] if isinstance(row['date_posted'], str) else row['date_posted'].strftime('%Y-%m-%d')}")
            
            with col2:
                # Show job status
                if row["tracking"].get("is_applied", False):
                    st.markdown("✅ Applied")
                else:
                    st.markdown("📝 Saved")
            
            with col3:
                # Action buttons
                if row["tracking"].get("is_applied", False):
                    if st.button("Mark as Not Applied", key=f"unapply_{row['id']}"):
                        if api_request(
                            f"user/jobs/{row['id']}/applied",
                            method="PUT",
                            data={"applied": False}
                        ):
                            st.success("Updated successfully")
                            st.rerun()
                        else:
                            st.error("Failed to update status")
                else:
                    if st.button("Mark as Applied", key=f"apply_{row['id']}"):
                        if api_request(
                            f"user/jobs/{row['id']}/applied",
                            method="PUT",
                            data={"applied": True}
                        ):
                            st.success("Updated successfully")
                            st.rerun()
                        else:
                            st.error("Failed to update status")
                
                if st.button("Remove", key=f"remove_{row['id']}"):
                    if api_request(
                        f"user/jobs/{row['id']}/track",
                        method="DELETE"
                    ):
                        st.success("Job removed from tracking")
                        st.rerun()
                    else:
                        st.error("Failed to remove job")
            
            st.markdown("---")

def add_job_tracking_buttons(job_id, job_data=None):
    """
    Add job tracking buttons to a job listing.
    
    Args:
        job_id: ID of the job
        job_data: Optional job data from tracking API (if already fetched)
    
    Returns:
        None
    """
    from app.dashboard.auth import is_authenticated
    
    if not is_authenticated():
        # Not authenticated, don't show tracking buttons
        return
    
    # Check if job is already tracked
    tracked_data = None
    if job_data:
        tracked_data = job_data
    else:
        # Fetch data for this specific job
        user_jobs = api_request("user/jobs")
        if user_jobs:
            # Find this job in the tracked jobs
            tracked_job = next((j for j in user_jobs if j["id"] == job_id), None)
            if tracked_job:
                tracked_data = tracked_job.get("tracking")
    
    col1, col2 = st.columns(2)
    
    # Job is tracked
    if tracked_data:
        with col1:
            # Toggle applied status
            is_applied = tracked_data.get("is_applied", False)
            
            if is_applied:
                if st.button("Mark as Not Applied", key=f"unapply_btn_{job_id}"):
                    if api_request(
                        f"user/jobs/{job_id}/applied",
                        method="PUT",
                        data={"applied": False}
                    ):
                        st.success("Updated successfully")
                        st.rerun()
                    else:
                        st.error("Failed to update status")
            else:
                if st.button("Mark as Applied", key=f"apply_btn_{job_id}"):
                    if api_request(
                        f"user/jobs/{job_id}/applied",
                        method="PUT",
                        data={"applied": True}
                    ):
                        st.success("Updated successfully")
                        st.rerun()
                    else:
                        st.error("Failed to update status")
        
        with col2:
            # Remove from tracking
            if st.button("Remove from Saved", key=f"remove_btn_{job_id}"):
                if api_request(
                    f"user/jobs/{job_id}/track",
                    method="DELETE"
                ):
                    st.success("Job removed from tracking")
                    st.rerun()
                else:
                    st.error("Failed to remove job")
    
    # Job is not tracked
    else:
        with col1:
            if st.button("Save Job", key=f"save_btn_{job_id}"):
                if api_request(
                    f"user/jobs/{job_id}/track",
                    method="POST"
                ):
                    st.success("Job saved successfully")
                    st.rerun()
                else:
                    st.error("Failed to save job")
