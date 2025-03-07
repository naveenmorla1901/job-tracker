"""
Custom jobs table component for the dashboard - fixes spacing and checkbox issues
Uses direct database access to ensure job status updates work reliably
"""
import streamlit as st
import pandas as pd
import time
from dashboard_components.utils import format_job_date, get_api_url
from app.dashboard.auth import is_authenticated, get_current_user
from dashboard_components.direct_job_actions import (
    mark_job_applied_direct,
    get_user_tracked_jobs_direct
)

def display_custom_jobs_table(df_jobs):
    """A clean, simplified implementation of the jobs table with proper checkbox handling"""
    
    # Store tracking changes in session state to prevent loss on errors
    if "tracked_jobs_status" not in st.session_state:
        st.session_state.tracked_jobs_status = {}
    
    # Get current user if authenticated
    user_email = None
    if is_authenticated():
        user_data = get_current_user()
        if user_data and "email" in user_data:
            user_email = user_data["email"]
    
    # Get tracked jobs directly from the database
    tracked_jobs = {}
    if user_email:
        # Get tracked jobs directly from database
        tracked_jobs = get_user_tracked_jobs_direct(user_email)
        st.session_state.tracked_jobs_status = tracked_jobs
        
        # Show debug info
        st.write(f"User: {user_email} | Tracked jobs: {len(tracked_jobs)}")
    
    # Display table header
    st.header("Job Listings")
    
    # Add direct job status management tool
    with st.expander("Job Application Status Tool"):
        st.write("Use this tool to directly update your job application status")
        
        col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
        
        with col1:
            job_id = st.text_input("Job ID", "1")
        
        with col2:
            applied = st.checkbox("Applied")
        
        with col3:
            if st.button("Update Status"):
                if not user_email:
                    st.error("You must be logged in to use this feature")
                else:
                    # Update job status directly in the database
                    success = mark_job_applied_direct(user_email, int(job_id), applied)
                    if success:
                        st.success(f"Job {job_id} marked as {'applied' if applied else 'not applied'}")
                        # Update cached status
                        tracked_jobs[job_id] = applied
                        st.session_state.tracked_jobs_status = tracked_jobs
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to update job status")
        
        with col4:
            if st.button("Refresh Status"):
                if user_email:
                    tracked_jobs = get_user_tracked_jobs_direct(user_email)
                    st.session_state.tracked_jobs_status = tracked_jobs
                    st.success("Refreshed job status")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("You must be logged in to use this feature")
    
    # Custom table with row numbers and apply button column
    if is_authenticated():
        # Convert dataframe to list for simple display
        job_data = []
        for i, row in df_jobs.iterrows():
            job_id = str(row['id'])
            job_data.append({
                "Number": i + 1, 
                "Job ID": job_id,
                "Job Title": row['job_title'],
                "Company": row['company'],
                "Location": row['location'],
                "Posted": format_job_date(row['date_posted']),
                "Type": row.get('employment_type', ''),
                "Applied": tracked_jobs.get(job_id, False),
                "URL": row['job_url']
            })
            
        # Create DataFrame for display
        jobs_df = pd.DataFrame(job_data)
        
        # Add checkboxes for applied status - each with a callback
        for index, job in enumerate(job_data):
            with st.container():
                cols = st.columns([1, 6, 3, 3, 2, 2, 1])
                
                # Row number
                cols[0].write(f"#{job['Number']}")
                
                # Job title with URL
                cols[1].markdown(f"**[{job['Job Title']}]({job['URL']})**")
                
                # Company
                cols[2].write(job['Company'])
                
                # Location
                cols[3].write(job['Location'])
                
                # Posted date
                cols[4].write(job['Posted'])
                
                # Current status
                is_applied = job['Applied']
                
                # Applied checkbox - directly update on change
                new_status = cols[5].checkbox(
                    "Applied", 
                    value=is_applied,
                    key=f"job_{job['Job ID']}_{int(time.time())}"  # Unique key with timestamp
                )
                
                # Handle status change
                if new_status != is_applied:
                    if user_email:
                        with st.spinner(f"Updating job {job['Job ID']}..."):
                            # Directly update in database
                            success = mark_job_applied_direct(
                                user_email, 
                                int(job['Job ID']), 
                                new_status
                            )
                            
                            if success:
                                # Update tracked jobs in memory
                                tracked_jobs[job['Job ID']] = new_status
                                st.session_state.tracked_jobs_status[job['Job ID']] = new_status
                                
                                # Show success message
                                if new_status:
                                    st.success(f"Job {job['Job ID']} marked as applied")
                                else:
                                    st.success(f"Job {job['Job ID']} marked as not applied")
                            else:
                                st.error(f"Failed to update job {job['Job ID']}")
                
                # Apply button
                cols[6].markdown(f"[Apply]({job['URL']})")
                
            # Add separator
            st.markdown("---")
    else:
        # Simpler table for unauthenticated users
        st.warning("Please log in to track job applications")
        
        # Convert dataframe to list for simple display
        job_data = []
        for i, row in df_jobs.iterrows():
            job_data.append({
                "Number": i + 1, 
                "Job Title": row['job_title'],
                "Company": row['company'],
                "Location": row['location'],
                "Posted": format_job_date(row['date_posted']),
                "Type": row.get('employment_type', ''),
                "URL": row['job_url']
            })
            
        # Create DataFrame for display
        jobs_df = pd.DataFrame(job_data)
        
        # Display jobs table without applied column
        st.dataframe(
            jobs_df,
            column_config={
                "Number": st.column_config.NumberColumn(
                    "No.",
                    width="small"
                ),
                "Job Title": st.column_config.TextColumn(
                    "Job Title",
                    width="large"
                ),
                "Company": st.column_config.TextColumn(
                    "Company",
                    width="medium"
                ),
                "Location": st.column_config.TextColumn(
                    "Location",
                    width="medium"
                ),
                "Posted": st.column_config.TextColumn(
                    "Posted",
                    width="small"
                ),
                "Type": st.column_config.TextColumn(
                    "Type",
                    width="small"
                ),
                "URL": st.column_config.LinkColumn(
                    "Apply",
                    width="small",
                    display_text="Apply"
                )
            },
            hide_index=True,
            use_container_width=True
        )
