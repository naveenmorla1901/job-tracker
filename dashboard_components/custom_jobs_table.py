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

        # Create table data for display - similar to non-logged-in view but with checkbox
        table_data = []
        for i, row in df_jobs.iterrows():
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

            # Create checkbox HTML
            checkbox_id = f"applied_{job_id}"
            checkbox_html = f'<input type="checkbox" id="{checkbox_id}" name="{checkbox_id}" {"checked" if is_applied else ""} onclick="handleCheckboxChange({job_id}, this.checked)"/>'

            # Create apply button HTML
            apply_html = f'<a href="{job_url}" target="_blank" onclick="trackJobApply(\'{job_id}\', \'{company}\', \'{job_title}\'); return true;" style="display:inline-block; padding:1px 5px; font-size:0.75rem; background-color:#1E90FF; color:white; text-decoration:none; border-radius:2px;">Apply</a>'

            # Add to table data
            table_data.append({
                "No.": i+1,
                "Job Title": job_title,
                "Company": company,
                "Location": location,
                "Posted": date_posted,
                "Type": job_type,
                "Applied": checkbox_html,
                "Apply": apply_html
            })

        # Convert to DataFrame for display
        df_display = pd.DataFrame(table_data)

        # Add JavaScript for checkbox handling
        js_code = """
        <script>
        function handleCheckboxChange(jobId, isApplied) {
            // Prevent multiple clicks
            const checkbox = document.getElementById(`applied_${jobId}`);
            if (checkbox) {
                checkbox.disabled = true;
            }

            // Make API call to update status
            fetch(`/api/user/jobs/update`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    job_id: jobId,
                    is_applied: isApplied
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                console.log('Success:', data);
                // Re-enable checkbox
                if (checkbox) {
                    checkbox.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred. Please try again.');
                // Revert checkbox on error
                if (checkbox) {
                    checkbox.checked = !isApplied;
                    checkbox.disabled = false;
                }
            });
        }

        function trackJobApply(jobId, company, jobTitle) {
            console.log(`Applying to job ${jobId}: ${jobTitle} at ${company}`);
            // Add any analytics tracking code here
        }
        </script>
        """

        # Apply table styling for logged-in view
        st.markdown("""
        <style>
        /* Table styling for logged-in view */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 0;
            padding: 0;
        }

        th {
            background-color: #1E1E1E;
            color: white;
            text-align: left;
            padding: 4px 8px;
            font-size: 0.9rem;
            font-weight: bold;
            border-bottom: 1px solid #444;
        }

        td {
            padding: 4px 8px;
            font-size: 0.85rem;
            border-bottom: 1px solid #333;
            vertical-align: middle;
        }

        tr:hover {
            background-color: rgba(200, 200, 200, 0.1);
        }

        /* Checkbox styling */
        input[type="checkbox"] {
            transform: scale(1.2);
            margin: 0;
            padding: 0;
        }

        /* Center checkbox and apply button */
        td:nth-child(7), td:nth-child(8) {
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)

        # Display the table with HTML
        st.markdown(df_display.to_html(escape=False, index=False) + js_code, unsafe_allow_html=True)
    else:
        # For non-logged-in users, show all jobs in a compact table with the same styling as logged-in view
        # Create table data for display
        table_data = []
        for i, row in df_jobs.iterrows():
            job_url = row['job_url']
            # Create apply button HTML
            apply_html = f'<a href="{job_url}" target="_blank" style="display:inline-block; padding:1px 5px; font-size:0.75rem; background-color:#1E90FF; color:white; text-decoration:none; border-radius:2px;">Apply</a>'

            table_data.append({
                "No.": i+1,
                "Job Title": row['job_title'],
                "Company": row['company'],
                "Location": row['location'],
                "Posted": format_job_date(row['date_posted']),
                "Type": row.get('employment_type', ''),
                "Apply": apply_html
            })

        # Convert to DataFrame for display
        df_display = pd.DataFrame(table_data)

        # Apply table styling for non-logged-in view (same as logged-in view)
        st.markdown("""
        <style>
        /* Table styling for non-logged-in view */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 0;
            padding: 0;
        }

        th {
            background-color: #1E1E1E;
            color: white;
            text-align: left;
            padding: 4px 8px;
            font-size: 0.9rem;
            font-weight: bold;
            border-bottom: 1px solid #444;
        }

        td {
            padding: 4px 8px;
            font-size: 0.85rem;
            border-bottom: 1px solid #333;
            vertical-align: middle;
        }

        tr:hover {
            background-color: rgba(200, 200, 200, 0.1);
        }

        /* Center apply button */
        td:nth-child(7) {
            text-align: center;
        }
        </style>
        """, unsafe_allow_html=True)

        # Display the table with HTML
        st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

        # Show login message
        st.info("Log in to track job applications")
