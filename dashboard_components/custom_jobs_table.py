"""
Simple jobs table with direct database updates
"""
import streamlit as st
import pandas as pd
import time
import os
import sys
from dashboard_components.utils import format_job_date
from app.dashboard.auth import is_authenticated, get_current_user
from app.db.database import get_db
from app.db.models import UserJob, Job, User
from datetime import datetime
import logging

# Configure logging
logger = logging.getLogger("job_tracker.dashboard.custom_jobs_table")

def get_user_by_email(db, email):
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def get_tracked_jobs(user_email):
    """Get all jobs tracked by a user with their applied status"""
    result = {}
    try:
        # Get database session
        db = next(get_db())
        
        # Get user
        user = get_user_by_email(db, user_email)
        if not user:
            return {}
        
        # Get all tracked jobs
        tracked_jobs = db.query(UserJob).filter(UserJob.user_id == user.id).all()
        
        # Create dictionary mapping job_id to applied status
        for job in tracked_jobs:
            result[str(job.job_id)] = job.is_applied
        
        db.close()
    except Exception as e:
        st.error(f"Error getting tracked jobs: {e}")
    
    return result

def update_job_status(user_email, job_id, applied):
    """Update a job's applied status directly in the database"""
    try:
        # Get database session
        db = next(get_db())
        
        # Get user
        user = get_user_by_email(db, user_email)
        if not user:
            return False
        
        # Check if job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return False
        
        # Get or create UserJob record
        user_job = db.query(UserJob).filter(
            UserJob.user_id == user.id,
            UserJob.job_id == job_id
        ).first()
        
        if user_job:
            # Update existing record
            user_job.is_applied = applied
            user_job.date_updated = datetime.utcnow()
        else:
            # Create new record
            user_job = UserJob(
                user_id=user.id,
                job_id=job_id,
                is_applied=applied,
                date_saved=datetime.utcnow()
            )
            db.add(user_job)
        
        # Commit changes
        db.commit()
        db.close()
        return True
    except Exception as e:
        st.error(f"Error updating job status: {e}")
        try:
            db.rollback()
            db.close()
        except:
            pass
        return False

def display_custom_jobs_table(df_jobs):
    """Display a simple, reliable jobs table with status tracking"""
    
    # Get user information if authenticated
    user_email = None
    if is_authenticated():
        user = get_current_user()
        if user and "email" in user:
            user_email = user["email"]
    
    # Display header
    st.header("Job Listings")
    
    # Show direct job status tool for manual updates
    with st.expander("Job Status Update Tool"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            job_id = st.text_input("Job ID")
        
        with col2:
            applied_status = st.checkbox("Mark as Applied")
        
        with col3:
            if st.button("Update Status"):
                if not user_email:
                    st.error("You must be logged in to update job status")
                elif not job_id:
                    st.error("Please enter a job ID")
                else:
                    success = update_job_status(user_email, int(job_id), applied_status)
                    if success:
                        st.success(f"Job {job_id} marked as {'applied' if applied_status else 'not applied'}")
                        # Force reload after 1 second
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"Failed to update job {job_id}")
    
    # Get tracked jobs for current user
    tracked_jobs = {}
    if user_email:
        tracked_jobs = get_tracked_jobs(user_email)
        st.write(f"You have {len(tracked_jobs)} tracked jobs")
    
    # Add a simple form for each job
    if is_authenticated():
        for i, row in df_jobs.iterrows():
            # Limit display to 100 jobs for performance
            if i >= 100:
                break
            
            job_id = str(row['id'])
            job_title = row['job_title']
            company = row['company']
            location = row['location']
            date_posted = format_job_date(row['date_posted'])
            job_url = row['job_url']
            
            # Is this job tracked and applied?
            is_applied = tracked_jobs.get(job_id, False)
            
            # Create job card with columns
            with st.form(key=f"job_form_{job_id}_{i}"):
                cols = st.columns([1, 4, 3, 3, 2, 2])
                
                # Column 1: Number
                cols[0].write(f"#{i+1}")
                
                # Column 2: Job Title and Company
                cols[1].markdown(f"**{job_title}**")
                cols[1].write(f"{company}")
                
                # Column 3: Location
                cols[2].write(location)
                
                # Column 4: Date Posted
                cols[3].write(f"Posted: {date_posted}")
                
                # Column 5: Applied Status
                applied = cols[4].checkbox("Applied", value=is_applied, key=f"applied_{job_id}_{i}")
                
                # Column 6: Submit Button
                submit = cols[5].form_submit_button("Save")
                
                # Process form submission
                if submit:
                    # Only update if status changed
                    if applied != is_applied:
                        success = update_job_status(user_email, int(job_id), applied)
                        if success:
                            st.success(f"Job {job_id} marked as {'applied' if applied else 'not applied'}")
                            # Force reload after 1 second
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Failed to update job {job_id}")
            
            # Add apply button outside the form
            st.markdown(f"[Apply to this job]({job_url})")
            
            # Add separator
            st.markdown("---")
        
        # Show message if limiting results
        if len(df_jobs) > 100:
            st.info(f"Showing 100 of {len(df_jobs)} jobs. Use filters to narrow results.")
    else:
        # Display simple table for non-authenticated users
        st.warning("Please log in to track job applications")
        
        # Create table data
        table_data = []
        for i, row in df_jobs.iterrows():
            table_data.append({
                "No.": i+1,
                "Job Title": row['job_title'],
                "Company": row['company'],
                "Location": row['location'],
                "Posted": format_job_date(row['date_posted']),
                "Apply": row['job_url']
            })
        
        # Display as dataframe
        st.dataframe(
            pd.DataFrame(table_data),
            column_config={
                "Apply": st.column_config.LinkColumn("Apply", display_text="Apply")
            },
            hide_index=True
        )
