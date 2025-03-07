"""
Jobs table with save button for application status changes
"""
import streamlit as st
import pandas as pd
import time
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
        logger.error(f"Error getting tracked jobs: {e}")
    
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
        logger.error(f"Error updating job status: {e}")
        try:
            db.rollback()
            db.close()
        except:
            pass
        return False

def display_custom_jobs_table(df_jobs):
    """Display a clean jobs table with save button for application status changes"""
    
    # Get user information if authenticated
    user_email = None
    if is_authenticated():
        user = get_current_user()
        if user and "email" in user:
            user_email = user["email"]
    
    # Display header
    st.header("Job Listings")
    
    # Get tracked jobs for current user
    tracked_jobs = {}
    if user_email:
        tracked_jobs = get_tracked_jobs(user_email)
    
    # Display jobs table
    if is_authenticated():
        # Store checkbox states in session state
        if "job_checkboxes" not in st.session_state:
            st.session_state.job_checkboxes = {}
        
        # Initialize checkbox states with tracked jobs
        for job_id, is_applied in tracked_jobs.items():
            if job_id not in st.session_state.job_checkboxes:
                st.session_state.job_checkboxes[job_id] = is_applied
        
        # Display each job with columns
        for i, row in df_jobs.iterrows():
            # Limit to 100 jobs for performance
            if i >= 100:
                break
                
            # Get job details
            job_id = str(row['id'])
            job_title = row['job_title']
            company = row['company']
            location = row['location']
            date_posted = format_job_date(row['date_posted'])
            job_type = row.get('employment_type', '')
            job_url = row['job_url']
            
            # Default to False if not in tracked jobs
            is_tracked = job_id in tracked_jobs
            is_applied = tracked_jobs.get(job_id, False)
            
            # Add job to session state if not present
            if job_id not in st.session_state.job_checkboxes:
                st.session_state.job_checkboxes[job_id] = is_applied
            
            # Create job card with columns
            with st.container():
                cols = st.columns([1, 4, 3, 3, 2, 2, 2, 2])
                
                # Column 1: Number
                cols[0].write(f"#{i+1}")
                
                # Column 2: Job Title and Company
                cols[1].markdown(f"**{job_title}**")
                cols[1].write(f"{company}")
                
                # Column 3: Location
                cols[2].write(location)
                
                # Column 4: Date Posted and Type
                cols[3].write(f"Posted: {date_posted}")
                cols[3].write(f"Type: {job_type}")
                
                # Column 5: Applied Status
                # Use session state to maintain checkbox values between renders
                checkbox_key = f"applied_{job_id}"
                is_checked = cols[4].checkbox("Applied", value=st.session_state.job_checkboxes[job_id], key=checkbox_key)
                
                # Update session state if checkbox changed
                if is_checked != st.session_state.job_checkboxes[job_id]:
                    st.session_state.job_checkboxes[job_id] = is_checked
                
                # Column 6: Save Button
                if cols[5].button("Save", key=f"save_{job_id}"):
                    new_status = st.session_state.job_checkboxes[job_id]
                    
                    # Show saving indicator
                    with st.spinner(f"Updating job status..."):
                        success = update_job_status(user_email, int(job_id), new_status)
                        
                        if success:
                            st.success(f"Job status updated: {'Applied' if new_status else 'Not Applied'}")
                            
                            # Update tracked jobs dictionary for display
                            tracked_jobs[job_id] = new_status
                        else:
                            st.error("Failed to update job status")
                
                # Column 7: Apply Button
                cols[6].markdown(f"[Apply]({job_url})")
            
            # Add separator
            st.markdown("---")
        
        # Show message if limiting results
        if len(df_jobs) > 100:
            st.info(f"Showing 100 of {len(df_jobs)} jobs. Use filters to narrow results.")
    else:
        # For non-logged-in users, show a simple table
        table_data = []
        for i, row in df_jobs.iterrows():
            table_data.append({
                "No.": i+1,
                "Job Title": row['job_title'],
                "Company": row['company'],
                "Location": row['location'],
                "Posted": format_job_date(row['date_posted']),
                "Type": row.get('employment_type', ''),
                "Apply": row['job_url']
            })
        
        # Convert to DataFrame for display
        df_display = pd.DataFrame(table_data)
        
        # Display table
        st.dataframe(
            df_display,
            column_config={
                "Apply": st.column_config.LinkColumn("Apply", display_text="Apply")
            },
            hide_index=True,
            use_container_width=True,
            height=600
        )
        
        # Show login message
        st.info("Log in to track job applications")
