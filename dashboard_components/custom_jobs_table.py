"""
Jobs table with save button for application status changes
"""
import streamlit as st
import pandas as pd
from dashboard_components.utils import format_job_date
from app.dashboard.auth import is_authenticated, get_current_user
from app.db.database import get_db
from app.db.models import UserJob, Job, User
from datetime import datetime, timezone
from sqlalchemy import and_
import logging

logger = logging.getLogger(__name__)

def get_user_by_email(db, email):
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def get_tracked_jobs(user_email):
    """Get tracked jobs for a user"""
    try:
        # Get database session
        db = next(get_db())
        
        # Get user
        user = get_user_by_email(db, user_email)
        if not user:
            return {}
        
        # Get tracked jobs
        user_jobs = db.query(UserJob).filter(
            UserJob.user_id == user.id
        ).all()
        
        # Convert to dictionary for easy lookup
        tracked_jobs = {}
        for user_job in user_jobs:
            tracked_jobs[str(user_job.job_id)] = user_job.is_applied
        
        return tracked_jobs
    except Exception as e:
        logger.error(f"Error getting tracked jobs: {str(e)}")
        return {}

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
            user_job.date_updated = datetime.now(timezone.utc)
        else:
            # Create new record
            user_job = UserJob(
                user_id=user.id,
                job_id=job_id,
                is_applied=applied,
                date_saved=datetime.now(timezone.utc)
            )
            db.add(user_job)

        # Commit changes
        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error updating job status: {str(e)}")
        db.rollback()
        return False

def display_custom_jobs_table(df_jobs):
    """Display a clean jobs table with save button for application status changes"""

    # Get user information if authenticated
    user_email = None
    if is_authenticated():
        user = get_current_user()
        if user and "email" in user:
            user_email = user["email"]

    # Apply ultra-compact styling
    st.markdown("""
    <style>
    /* Compact table styling - ULTRA COMPACT */
    .stContainer, .block-container, .element-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    
    /* Reduce space between elements to absolute minimum */
    div.stMarkdown p {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
        line-height: 1 !important;
        padding: 0 !important;
    }
    
    /* Reduce gap between job listings */
    .job-container {
        margin-bottom: -35px !important;
        margin-top: -15px !important;
        padding-bottom: 0 !important;
        padding-top: 0 !important;
    }
    
    /* Target Streamlit's container divs */
    div[data-testid="column"] > div, 
    div[data-testid="stVerticalBlock"] > div {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    
    /* Target Streamlit's container classes for logged-in view */
    .st-emotion-cache-ocqkz7, .st-emotion-cache-16txtl3, .st-emotion-cache-1r6slb0, .st-emotion-cache-1kyxreq {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    
    /* Target the row container */
    .row-widget {
        padding: 0 !important;
        margin: 0 !important;
    }
    
    /* Target the stHorizontal class */
    .stHorizontal {
        gap: 0 !important;
        margin-top: -10px !important;
        margin-bottom: -10px !important;
    }
    
    /* Target the checkbox container */
    .stCheckbox > div {
        min-height: 0 !important;
    }
    
    /* Remove gap between checkbox and its label */
    .stCheckbox > div:first-child {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

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

        # Create column headers
        cols = st.columns([0.5, 3, 2, 2, 1, 1])
        cols[0].markdown("**#**")
        cols[1].markdown("**Job Title**")
        cols[2].markdown("**Location**")
        cols[3].markdown("**Posted**")
        cols[4].markdown("**Applied**")
        cols[5].markdown("**Apply**")
        
        # Add a separator
        st.markdown("<hr style='margin: 0; padding: 0;'>", unsafe_allow_html=True)
        
        # Define a callback function for checkbox changes
        def on_checkbox_change(job_id):
            # Get the current value from session state
            is_checked = st.session_state[f"applied_{job_id}"]
            
            # Get the previous value
            prev_value = st.session_state.job_checkboxes.get(job_id, False)
            
            # Only update if the value has changed
            if is_checked != prev_value:
                # Update the session state
                st.session_state.job_checkboxes[job_id] = is_checked
                
                # Auto-save the change to the database
                success = update_job_status(user_email, int(job_id), is_checked)
                
                if success:
                    # Update tracked jobs dictionary for display silently
                    tracked_jobs[job_id] = is_checked
                    # Show success message
                    st.toast(f"Job marked as {'applied' if is_checked else 'not applied'}", icon="✅")
                else:
                    # Show error message
                    st.toast("Failed to update status", icon="❌")
                    # Revert the checkbox in session state
                    st.session_state[f"applied_{job_id}"] = prev_value
                    st.session_state.job_checkboxes[job_id] = prev_value
        
        # Display each job with columns
        for i, row in df_jobs.iterrows():
            # Get job details
            job_id = str(row['id'])
            job_title = row['job_title']
            company = row['company']
            location = row['location']
            date_posted = format_job_date(row['date_posted'])
            job_type = row.get('employment_type', '')
            job_url = row['job_url']

            # Default to False if not in tracked jobs
            is_applied = tracked_jobs.get(job_id, False)

            # Add job to session state if not present
            if job_id not in st.session_state.job_checkboxes:
                st.session_state.job_checkboxes[job_id] = is_applied

            # Create job card with columns in a single container
            with st.container():
                # Apply ultra-compact styling to this container
                st.markdown("""
                <style>
                .job-row {
                    margin-top: -25px !important;
                    margin-bottom: -25px !important;
                    padding-top: 0 !important;
                    padding-bottom: 0 !important;
                }
                </style>
                <div class="job-row">
                """, unsafe_allow_html=True)
                
                # Create columns for this job
                job_cols = st.columns([0.5, 3, 2, 2, 1, 1])
                
                # Column 1: Number
                job_cols[0].markdown(f"<p style='font-size:0.9rem;'>#{i+1}</p>", unsafe_allow_html=True)
                
                # Column 2: Job Title and Company
                job_cols[1].markdown(f"<div style='margin-bottom: 0;'><strong>{job_title}</strong></div>", unsafe_allow_html=True)
                job_cols[1].markdown(f"<div style='font-size:0.8rem; color:#888;'>{company}</div>", unsafe_allow_html=True)
                
                # Column 3: Location
                job_cols[2].markdown(f"<p style='font-size:0.9rem;'>{location}</p>", unsafe_allow_html=True)
                
                # Column 4: Date Posted and Type
                job_cols[3].markdown(f"<p style='font-size:0.8rem; color:#888;'>{date_posted} • {job_type}</p>", unsafe_allow_html=True)
                
                # Column 5: Applied Status with auto-save
                # Use session state to maintain checkbox values between renders
                checkbox_key = f"applied_{job_id}"
                
                # Get the previous value to detect changes
                prev_value = st.session_state.job_checkboxes.get(job_id, False)
                
                # Initialize the checkbox state in session state if not present
                if checkbox_key not in st.session_state:
                    st.session_state[checkbox_key] = prev_value
                
                # Display the checkbox with on_change callback
                job_cols[4].checkbox(
                    "Applied", 
                    value=prev_value, 
                    key=checkbox_key, 
                    help="Mark as applied (saves automatically)", 
                    label_visibility="collapsed",
                    on_change=on_checkbox_change,
                    args=(job_id,)
                )
                
                # Column 6: Apply button
                job_cols[5].markdown(f"<a href='{job_url}' target='_blank' style='display:inline-block; padding:2px 8px; background-color:#1E90FF; color:white; text-decoration:none; border-radius:3px; font-size:0.8rem;'>Apply</a>", unsafe_allow_html=True)
                
                # Close the container div
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Add a minimal separator between jobs
            st.markdown("<hr style='margin: 0; padding: 0; opacity: 0.1;'>", unsafe_allow_html=True)
    else:
        # For non-logged-in users, show all jobs in a compact table with the same styling as logged-in view
        # Create column headers
        cols = st.columns([0.5, 3, 2, 2, 1, 1])
        cols[0].markdown("**#**")
        cols[1].markdown("**Job Title**")
        cols[2].markdown("**Location**")
        cols[3].markdown("**Posted**")
        cols[4].markdown("**Type**")
        cols[5].markdown("**Apply**")
        
        # Add a separator
        st.markdown("<hr style='margin: 0; padding: 0;'>", unsafe_allow_html=True)
        
        # Display each job with columns
        for i, row in df_jobs.iterrows():
            # Get job details
            job_id = str(row['id'])
            job_title = row['job_title']
            company = row['company']
            location = row['location']
            date_posted = format_job_date(row['date_posted'])
            job_type = row.get('employment_type', '')
            job_url = row['job_url']

            # Create job card with columns in a single container
            with st.container():
                # Apply ultra-compact styling to this container
                st.markdown("""
                <style>
                .job-row {
                    margin-top: -25px !important;
                    margin-bottom: -25px !important;
                    padding-top: 0 !important;
                    padding-bottom: 0 !important;
                }
                </style>
                <div class="job-row">
                """, unsafe_allow_html=True)
                
                # Create columns for this job
                job_cols = st.columns([0.5, 3, 2, 2, 1, 1])
                
                # Column 1: Number
                job_cols[0].markdown(f"<p style='font-size:0.9rem;'>#{i+1}</p>", unsafe_allow_html=True)
                
                # Column 2: Job Title and Company
                job_cols[1].markdown(f"<div style='margin-bottom: 0;'><strong>{job_title}</strong></div>", unsafe_allow_html=True)
                job_cols[1].markdown(f"<div style='font-size:0.8rem; color:#888;'>{company}</div>", unsafe_allow_html=True)
                
                # Column 3: Location
                job_cols[2].markdown(f"<p style='font-size:0.9rem;'>{location}</p>", unsafe_allow_html=True)
                
                # Column 4: Date Posted
                job_cols[3].markdown(f"<p style='font-size:0.8rem; color:#888;'>{date_posted}</p>", unsafe_allow_html=True)
                
                # Column 5: Job Type
                job_cols[4].markdown(f"<p style='font-size:0.8rem; color:#888;'>{job_type}</p>", unsafe_allow_html=True)
                
                # Column 6: Apply button
                job_cols[5].markdown(f"<a href='{job_url}' target='_blank' style='display:inline-block; padding:2px 8px; background-color:#1E90FF; color:white; text-decoration:none; border-radius:3px; font-size:0.8rem;'>Apply</a>", unsafe_allow_html=True)
                
                # Close the container div
                st.markdown("</div>", unsafe_allow_html=True)
            
            # Add a minimal separator between jobs
            st.markdown("<hr style='margin: 0; padding: 0; opacity: 0.1;'>", unsafe_allow_html=True)

        # Show login message
        st.info("Log in to track job applications")
