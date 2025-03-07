"""
Simple, clean jobs table with automatic saving of job application status
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
    """Display a simple, clean jobs table with automatic saving of status changes"""
    
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
    
    # Create table data
    table_data = []
    
    for i, row in df_jobs.iterrows():
        job_id = str(row['id'])
        job_title = row['job_title']
        company = row['company']
        location = row['location']
        date_posted = format_job_date(row['date_posted'])
        job_type = row.get('employment_type', '')
        job_url = row['job_url']
        
        # Create dictionary for this job
        job_data = {
            "No.": i+1,
            "Job Title": job_title,
            "Company": company,
            "Location": location,
            "Posted": date_posted,
            "Type": job_type,
            "Apply": job_url,
        }
        
        # Add applied status if user is authenticated
        if user_email:
            job_data["Applied"] = tracked_jobs.get(job_id, False)
            job_data["ID"] = job_id  # renamed from job_id to avoid confusion
        
        table_data.append(job_data)
    
    # Create DataFrame for display
    df_display = pd.DataFrame(table_data)
    
    # Display table based on authentication status
    if is_authenticated():
        # Create column configuration without using the 'visible' parameter
        column_config = {
            "No.": st.column_config.NumberColumn(
                "No.",
                width="small",
                help="Job number"
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
            "Applied": st.column_config.CheckboxColumn(
                "Applied",
                help="Check to mark as applied",
                width="small"
            ),
            "Apply": st.column_config.LinkColumn(
                "Apply",
                display_text="Apply",
                width="small"
            )
        }
        
        # Exclude ID from displayed columns
        editor = st.data_editor(
            df_display.drop(columns=["ID"], errors="ignore"),  # Drop ID from display
            column_order=["No.", "Job Title", "Company", "Location", "Posted", "Type", "Applied", "Apply"],
            column_config=column_config,
            disabled=["No.", "Job Title", "Company", "Location", "Posted", "Type", "Apply"],
            hide_index=True,
            use_container_width=True,
            key="job_table"
        )
        
        # We need to keep the ID for tracking changes
        df_with_id = df_display
        
        # Check for changes in the edited_rows
        if "edited_rows" in st.session_state:
            for row_idx, edits in st.session_state.edited_rows.items():
                if "Applied" in edits and int(row_idx) < len(table_data):
                    # Get the job ID and new status
                    job_id = table_data[int(row_idx)]["ID"]  # Using the renamed field
                    new_status = edits["Applied"]
                    
                    # Show a status message
                    with st.spinner(f"Updating job {job_id}..."):
                        success = update_job_status(user_email, int(job_id), new_status)
                        
                        if success:
                            # Show brief success message that auto-dismisses
                            message = st.empty()
                            message.success(f"Job {job_id} status updated")
                            time.sleep(1)
                            message.empty()
                        else:
                            st.error(f"Failed to update job {job_id}")
    else:
        # For non-logged-in users, show a simple table without the Applied column
        columns_to_drop = ["ID", "Applied"]
        display_df = df_display.copy()
        for col in columns_to_drop:
            if col in display_df.columns:
                display_df = display_df.drop(columns=[col])
                
        st.dataframe(
            display_df,
            use_container_width=True,
            column_config={
                "No.": st.column_config.NumberColumn(
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
                "Apply": st.column_config.LinkColumn(
                    "Apply",
                    display_text="Apply",
                    width="small"
                )
            },
            height=600,
            hide_index=True
        )
        
        # Show login message
        st.info("Log in to track job applications")
