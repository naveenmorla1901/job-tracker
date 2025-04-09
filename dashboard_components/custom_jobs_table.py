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

    /* Make checkboxes and buttons ultra compact */
    div.stCheckbox, button {
        padding: 0 !important;
        margin: 0 !important;
        height: auto !important;
    }

    /* Remove all spacing from markdown */
    .stMarkdown {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        line-height: 1 !important;
    }

    /* Remove all spacing from containers */
    div.element-container {
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        line-height: 1 !important;
    }

    /* Eliminate column padding */
    div.css-keje6w > div {
        padding-left: 4px !important;
        padding-right: 4px !important;
        margin: 0 !important;
    }

    /* Job title and main text */
    .job-title {
        font-size: 0.95rem !important;
        font-weight: bold;
        margin-bottom: 0 !important;
        margin-top: 0 !important;
        padding-bottom: 0 !important;
        padding-top: 0 !important;
        line-height: 1 !important;
    }

    /* Smaller text for captions */
    .caption-text {
        font-size: 0.85rem !important;
        line-height: 1 !important;
        margin: 0 !important;
        padding: 0 !important;
        color: #888;
    }

    /* Almost invisible separators */
    hr {
        margin: 0 !important;
        padding: 0 !important;
        height: 1px !important;
        border-top: 1px solid rgba(200, 200, 200, 0.05) !important;
    }

    /* Reduce height of each job row */
    .job-container {
        height: auto !important;
        min-height: auto !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
        padding-top: 2px !important;
        padding-bottom: 2px !important;
    }

    /* Make checkboxes more compact */
    input[type="checkbox"] {
        margin: 0 !important;
        padding: 0 !important;
        vertical-align: middle !important;
        transform: scale(0.8) !important;
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
            is_tracked = job_id in tracked_jobs
            is_applied = tracked_jobs.get(job_id, False)

            # Add job to session state if not present
            if job_id not in st.session_state.job_checkboxes:
                st.session_state.job_checkboxes[job_id] = is_applied

            # Create job card with columns in a single container
            with st.container():
                container_style = """
                <style>
                .job-container {
                    margin-top: -40px !important;
                    margin-bottom: -40px !important;
                    padding-top: 0 !important;
                    padding-bottom: 0 !important;
                }
                .compact-text {
                    margin: 0 !important;
                    padding: 0 !important;
                    line-height: 1 !important;
                    font-size: 0.85rem !important;
                }
                /* Target Streamlit's container classes */
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
                </style>
                <div class="job-container">
                """
                st.markdown(container_style, unsafe_allow_html=True)

                cols = st.columns([1, 3, 2, 2, 1, 1])

                # Column 1: Number - more compact
                cols[0].markdown(f"<p class='compact-text' style='font-size:0.8rem;'>#{i+1}</p>", unsafe_allow_html=True)

                # Column 2: Job Title and Company - even more compact
                cols[1].markdown(f"<div class='job-title' style='margin-bottom: 0 !important; line-height: 1 !important; padding: 0 !important;'>{job_title}</div>", unsafe_allow_html=True)
                cols[1].markdown(f"<span class='caption-text' style='margin-top: 0 !important; font-size:0.8rem !important;'>{company}</span>", unsafe_allow_html=True)

                # Column 3: Location - more compact
                cols[2].markdown(f"<p class='compact-text' style='color:#888; font-size:0.8rem; line-height: 1 !important;'>{location}</p>", unsafe_allow_html=True)

                # Column 4: Date Posted and Type - more compact, combined into one line
                # Use a smaller font for the date/time to fit more information
                cols[3].markdown(f"<p class='compact-text' style='color:#888; font-size:0.75rem; line-height: 1 !important;'>Posted: {date_posted} • {job_type}</p>", unsafe_allow_html=True)

                # Column 5: Applied Status with auto-save
                # Use session state to maintain checkbox values between renders
                checkbox_key = f"applied_{job_id}"

                # Get the previous value to detect changes
                prev_value = st.session_state.job_checkboxes.get(job_id, False)

                # Display the checkbox with a custom label for auto-save
                # We'll detect changes and save automatically
                is_checked = cols[4].checkbox("Applied", value=prev_value, key=checkbox_key, help="Mark as applied (saves automatically)", label_visibility="collapsed")

                # Check if the value changed and auto-save
                if is_checked != prev_value:
                    # Update the session state
                    st.session_state.job_checkboxes[job_id] = is_checked

                    # Auto-save the change
                    success = update_job_status(user_email, int(job_id), is_checked)

                    if success:
                        # Update tracked jobs dictionary for display silently
                        tracked_jobs[job_id] = is_checked
                    else:
                        st.error("Failed to update status.")

                # Apply button (column 6) - ultra compact with analytics tracking
                cols[5].markdown(f"<p class='compact-text'><a href='{job_url}' target='_blank' onclick=\"trackJobApply('{job_id}', '{company}', '{job_title}'); return true;\" style='display:inline-block; padding:1px 5px; font-size:0.75rem; background-color:#1E90FF; color:white; text-decoration:none; border-radius:2px;'>Apply</a></p>", unsafe_allow_html=True)

                # Close the container div
                st.markdown("</div>", unsafe_allow_html=True)



            # Ultra minimal separator - completely invisible line
            st.markdown("<hr style='margin: 0; padding: 0; opacity: 0; border: none; margin-top: -25px; margin-bottom: -25px;'>", unsafe_allow_html=True)
    else:
        # For non-logged-in users, show all jobs in a compact table
        # Apply the same compact styling
        st.markdown("""
        <style>
        .dataframe th {
            padding: 3px !important;
            font-size: 0.9rem !important;
        }
        .dataframe td {
            padding: 3px !important;
            font-size: 0.85rem !important;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            max-width: 200px;
        }
        </style>
        """, unsafe_allow_html=True)

        # Create table data for display
        table_data = []
        for i, row in df_jobs.iterrows():
            apply_url = row['job_url']
            table_data.append({
                "No.": i+1,
                "Job Title": row['job_title'],
                "Company": row['company'],
                "Location": row['location'],
                "Posted": format_job_date(row['date_posted']),
                "Type": row.get('employment_type', ''),
                "Apply": apply_url
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
