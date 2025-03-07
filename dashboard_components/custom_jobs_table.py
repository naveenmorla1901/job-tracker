"""
Custom jobs table component for the dashboard - fixes spacing and checkbox issues
"""
import streamlit as st
import pandas as pd
import requests
import json
import time
from dashboard_components.utils import format_job_date, get_api_url
from app.dashboard.auth import is_authenticated, api_request, get_token

def display_custom_jobs_table(df_jobs):
    """A clean, simplified implementation of the jobs table with proper checkbox handling"""
    
    # Store tracking changes in session state to prevent loss on errors
    if "tracked_jobs_status" not in st.session_state:
        st.session_state.tracked_jobs_status = {}
    
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
                        # Update session state
                        st.session_state.tracked_jobs_status[job_id] = is_applied
            
            # Debug info - show how many tracked jobs were found
            st.info(f"Tracked jobs found: {len(tracked_jobs)}")
        except Exception as e:
            st.error(f"Error fetching tracked jobs: {str(e)}")
            # If API error, use cached status
            tracked_jobs = st.session_state.tracked_jobs_status
    
    # Display table header
    st.write("### Job Listings")
    
    # Create a direct form for testing API calls
    with st.expander("Direct Job Status Management"):
        st.write("Use this form to directly mark jobs as applied or not applied.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            test_job_id = st.text_input("Job ID", "1")
        with col2:
            test_applied = st.checkbox("Mark as Applied")
        with col3:
            if st.button("Update Status"):
                try:
                    # Use the API directly
                    applied_result = api_request(
                        f"user/jobs/{test_job_id}/applied",
                        method="PUT",
                        data={"applied": test_applied}
                    )
                    
                    if applied_result:
                        st.success(f"Successfully marked job {test_job_id} as {'applied' if test_applied else 'not applied'}")
                        # Update local cache
                        st.session_state.tracked_jobs_status[test_job_id] = test_applied
                        tracked_jobs[test_job_id] = test_applied
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("Failed to update status. Make sure the job exists and you have permissions.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    # Add a job counter
    total_jobs = len(df_jobs)
    applied_jobs = sum(1 for job_id in tracked_jobs if tracked_jobs[job_id])
    
    col1, col2 = st.columns(2)
    col1.metric("Total Jobs", f"{total_jobs}")
    col2.metric("Applied Jobs", f"{applied_jobs}")
    
    # Create a simple table with selection
    if is_authenticated():
        # Convert dataframe to a list of jobs with applied status
        job_rows = []
        for i, row in df_jobs.iterrows():
            # Get job info
            job_id = str(row.get('id', ''))
            job_title = str(row.get('job_title', ''))
            company = str(row.get('company', ''))
            location = str(row.get('location', ''))
            date_posted = format_job_date(row.get('date_posted', ''))
            job_type = str(row.get('employment_type', ''))
            job_url = row.get('job_url', '#')
            
            # Check if job is tracked
            is_applied = tracked_jobs.get(job_id, False)
            
            job_rows.append({
                "number": i+1,
                "id": job_id,
                "title": job_title,
                "company": company,
                "location": location,
                "date_posted": date_posted,
                "type": job_type,
                "url": job_url,
                "applied": is_applied
            })
        
        # Convert to dataframe for display
        display_df = pd.DataFrame(job_rows)
        
        # Add applied status column with checkboxes
        st.data_editor(
            display_df,
            column_order=["number", "title", "company", "location", "date_posted", "type", "applied"],
            column_config={
                "number": st.column_config.NumberColumn(
                    "No.",
                    width="small"
                ),
                "id": st.column_config.NumberColumn(
                    "ID",
                    width="small",
                    disabled=True
                ),
                "title": st.column_config.TextColumn(
                    "Job Title",
                    width="large"
                ),
                "company": st.column_config.TextColumn(
                    "Company",
                    width="medium"
                ),
                "location": st.column_config.TextColumn(
                    "Location",
                    width="medium"
                ),
                "date_posted": st.column_config.TextColumn(
                    "Posted",
                    width="small"
                ),
                "type": st.column_config.TextColumn(
                    "Type",
                    width="small"
                ),
                "url": st.column_config.LinkColumn(
                    "URL",
                    width="small",
                    display_text="Apply"
                ),
                "applied": st.column_config.CheckboxColumn(
                    "Applied",
                    width="small",
                    help="Check to mark as applied"
                )
            },
            hide_index=True,
            use_container_width=True,
            disabled=["number", "title", "company", "location", "date_posted", "type"]
        )
        
        # Check for changes in the applied status
        if "edited_rows" in st.session_state:
            for idx, edits in st.session_state["edited_rows"].items():
                if "applied" in edits:
                    # Get the job that was changed
                    job_idx = int(idx)
                    job_id = job_rows[job_idx]["id"]
                    new_status = edits["applied"]
                    
                    # Show updating status
                    with st.spinner(f"Updating job {job_id} to {'applied' if new_status else 'not applied'}..."):
                        try:
                            # First track the job
                            track_result = api_request(
                                f"user/jobs/{job_id}/track", 
                                method="POST"
                            )
                            
                            # Then update applied status
                            applied_result = api_request(
                                f"user/jobs/{job_id}/applied",
                                method="PUT",
                                data={"applied": new_status}
                            )
                            
                            if applied_result:
                                st.success(f"Updated job {job_id} to {'applied' if new_status else 'not applied'}")
                                # Update local tracking
                                st.session_state.tracked_jobs_status[job_id] = new_status
                            else:
                                st.error(f"Failed to update job {job_id}")
                        except Exception as e:
                            st.error(f"Error updating job: {str(e)}")
        
        # Add links to apply
        st.write("### Apply to Jobs")
        st.write("Click the links below to apply to jobs:")
        
        cols = st.columns(3)
        for i, job in enumerate(job_rows):
            col_idx = i % 3
            with cols[col_idx]:
                st.markdown(f"[{job['title']} @ {job['company']}]({job['url']})")
    
    else:
        # For non-authenticated users, show a simpler table
        job_rows = []
        for i, row in df_jobs.iterrows():
            # Get job info
            job_title = str(row.get('job_title', ''))
            company = str(row.get('company', ''))
            location = str(row.get('location', ''))
            date_posted = format_job_date(row.get('date_posted', ''))
            job_type = str(row.get('employment_type', ''))
            job_url = row.get('job_url', '#')
            
            job_rows.append({
                "number": i+1,
                "title": job_title,
                "company": company,
                "location": location,
                "date_posted": date_posted,
                "type": job_type,
                "url": job_url
            })
        
        # Convert to dataframe for display
        display_df = pd.DataFrame(job_rows)
        
        # Display the table
        st.dataframe(
            display_df,
            column_order=["number", "title", "company", "location", "date_posted", "type"],
            column_config={
                "number": st.column_config.NumberColumn(
                    "No.",
                    width="small"
                ),
                "title": st.column_config.TextColumn(
                    "Job Title",
                    width="large"
                ),
                "company": st.column_config.TextColumn(
                    "Company",
                    width="medium"
                ),
                "location": st.column_config.TextColumn(
                    "Location",
                    width="medium"
                ),
                "date_posted": st.column_config.TextColumn(
                    "Posted",
                    width="small"
                ),
                "type": st.column_config.TextColumn(
                    "Type",
                    width="small"
                ),
                "url": st.column_config.LinkColumn(
                    "Apply",
                    width="small",
                    display_text="Apply"
                )
            },
            hide_index=True,
            use_container_width=True
        )
