"""
Custom jobs table component for the dashboard - fixes spacing and checkbox issues
"""
import streamlit as st
import pandas as pd
from dashboard_components.utils import format_job_date, get_api_url
from app.dashboard.auth import is_authenticated, api_request, get_token

def display_custom_jobs_table(df_jobs):
    """A clean, simplified implementation of the jobs table with proper checkbox handling"""
    
    # Get user's tracked jobs if authenticated
    tracked_jobs = {}
    if is_authenticated():
        try:
            user_jobs = api_request("user/jobs") or []
            if isinstance(user_jobs, list):
                for job in user_jobs:
                    if job and isinstance(job, dict) and 'id' in job:
                        job_id = str(job['id'])
                        is_applied = job.get('tracking', {}).get('is_applied', False)
                        tracked_jobs[job_id] = is_applied
            
            # Debug info - show how many tracked jobs were found
            st.write(f"Tracked jobs found: {len(tracked_jobs)}")
        except Exception as e:
            st.error(f"Error fetching tracked jobs: {str(e)}")
    
    # Display table header
    st.write("### Job Listings")
    
    # Define columns for the job table
    if is_authenticated():
        # Create a form for every job to handle applying
        for i, row in df_jobs.iterrows():
            # Limit rows for performance
            if i >= 100:
                break
                
            # Get job info
            job_id = str(row.get('id', ''))
            job_title = str(row.get('job_title', ''))
            company = str(row.get('company', ''))
            location = str(row.get('location', ''))
            date_posted = format_job_date(row.get('date_posted', ''))
            job_type = str(row.get('employment_type', ''))
            job_url = row.get('job_url', '#')
            
            # Check if job is applied
            is_applied = tracked_jobs.get(job_id, False)
            
            # Create a container for each job with columns
            with st.container():
                cols = st.columns([1, 10, 3, 3, 3, 2, 2, 2])
                
                # Job number
                cols[0].write(f"#{i+1}")
                
                # Job title
                cols[1].markdown(f"**[{job_title}]({job_url})**")
                
                # Company
                cols[2].write(company)
                
                # Location
                cols[3].write(location)
                
                # Date posted
                cols[4].write(date_posted)
                
                # Job type
                cols[5].write(job_type)
                
                # Applied status
                applied_status = cols[6].checkbox("Applied", value=is_applied, key=f"applied_{job_id}")
                
                # Apply button
                cols[7].markdown(f"[Apply]({job_url})")
                
                # Handle checkbox change
                if applied_status != is_applied:
                    # Update the status in the database
                    with st.spinner(f"Updating job status for {job_title}..."):
                        try:
                            # First track the job
                            track_result = api_request(f"user/jobs/{job_id}/track", method="POST")
                            
                            # Then mark it as applied
                            apply_result = api_request(
                                f"user/jobs/{job_id}/applied", 
                                method="PUT", 
                                data={"applied": applied_status}
                            )
                            
                            if track_result and apply_result:
                                # Update the local tracking dict
                                tracked_jobs[job_id] = applied_status
                                st.success(f"Updated job status: {job_title}")
                            else:
                                st.error(f"Failed to update job status: {job_title}")
                                # Reset checkbox to original state next time
                        except Exception as e:
                            st.error(f"Error updating job status: {str(e)}")
                
                # Add a separator
                st.markdown("---")
        
        # Show message if we limited the number of rows
        if len(df_jobs) > 100:
            st.info(f"Showing 100 of {len(df_jobs)} jobs. Use filters to narrow results.")
    else:
        # For non-authenticated users: simplified table
        for i, row in df_jobs.iterrows():
            # Get job info
            job_title = str(row.get('job_title', ''))
            company = str(row.get('company', ''))
            location = str(row.get('location', ''))
            date_posted = format_job_date(row.get('date_posted', ''))
            job_type = str(row.get('employment_type', ''))
            job_url = row.get('job_url', '#')
            
            # Create a container for each job with columns
            with st.container():
                cols = st.columns([1, 10, 3, 3, 3, 2, 2])
                
                # Job number
                cols[0].write(f"#{i+1}")
                
                # Job title
                cols[1].markdown(f"**[{job_title}]({job_url})**")
                
                # Company
                cols[2].write(company)
                
                # Location
                cols[3].write(location)
                
                # Date posted
                cols[4].write(date_posted)
                
                # Job type
                cols[5].write(job_type)
                
                # Apply button
                cols[6].markdown(f"[Apply]({job_url})")
                
                # Add a separator
                st.markdown("---")
