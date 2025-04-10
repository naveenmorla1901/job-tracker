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

    # Apply ultra-compact styling for table format
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

    /* Hide the warning message about session state */
    [data-testid="stAppViewBlockContainer"] > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) > div:nth-child(1) {
        display: none !important;
    }

    /* Override Streamlit's default table styling */
    div[data-testid="stTable"] table {
        width: 100%;
        border-collapse: collapse;
        margin: 0;
        padding: 0;
        font-size: 0.9rem;
    }

    div[data-testid="stTable"] th {
        background-color: #1E1E1E !important;
        color: white !important;
        text-align: left !important;
        padding: 8px !important;
        font-size: 0.9rem !important;
        font-weight: bold !important;
        border-bottom: 1px solid #444 !important;
    }

    div[data-testid="stTable"] td {
        padding: 8px !important;
        border-bottom: 1px solid #333 !important;
        vertical-align: middle !important;
    }

    div[data-testid="stTable"] tr:hover {
        background-color: rgba(200, 200, 200, 0.1) !important;
    }

    /* Style for the applied buttons */
    .applied-button {
        padding: 5px 10px;
        border-radius: 4px;
        cursor: pointer;
        font-size: 0.8rem;
        border: none;
        transition: all 0.3s;
        width: 100%;
        text-align: center;
    }

    .applied {
        background-color: #4CAF50;
        color: white;
    }

    .not-applied {
        background-color: #f1f1f1;
        color: #333;
    }

    .applied-button:hover {
        opacity: 0.8;
    }

    .applied-button[disabled] {
        opacity: 0.6;
        cursor: not-allowed;
        background-color: #ddd;
        color: #666;
    }

    /* Styling for the HTML table */
    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
    }

    th {
        background-color: #1E1E1E;
        color: white;
        text-align: left;
        padding: 8px;
        font-size: 0.9rem;
        font-weight: bold;
        border-bottom: 1px solid #444;
    }

    td {
        padding: 8px;
        border-bottom: 1px solid #333;
        vertical-align: middle;
    }

    tr:hover {
        background-color: rgba(200, 200, 200, 0.1);
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

    /* Center checkbox and apply button */
    .center-content {
        text-align: center;
    }

    /* Apply button styling */
    .apply-button {
        display: inline-block;
        padding: 2px 8px;
        background-color: #1E90FF;
        color: white;
        text-decoration: none;
        border-radius: 3px;
        font-size: 0.8rem;
        text-align: center;
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

        # Create a simple table with pandas and use Streamlit's native table display

        # Create table data for display
        table_data = []
        for _, row in df_jobs.iterrows():
            job_id = str(row['id'])
            job_title = row['job_title']
            company = row['company']
            location = row['location']
            date_posted = format_job_date(row['date_posted'])
            job_type = row.get('employment_type', '')

            # Default to False if not in tracked jobs
            is_applied = tracked_jobs.get(job_id, False)

            # Add job to session state if not present
            if job_id not in st.session_state.job_checkboxes:
                st.session_state.job_checkboxes[job_id] = is_applied

            # Create the button HTML with appropriate styling
            applied_button = f"""
            <button
                id="applied-{job_id}"
                class="applied-button {'applied' if is_applied else 'not-applied'}"
                onclick="toggleApplied('{job_id}', {str(is_applied).lower()})">
                {'Applied' if is_applied else 'Mark Applied'}
            </button>
            """

            # Add to table data
            table_data.append({
                "Job Title": job_title,
                "Company": company,
                "Location": location,
                "Posted": f"{date_posted} • {job_type}",
                "Applied": applied_button,
                "Apply": f"<a href='{row['job_url']}' target='_blank' class='apply-button'>Apply</a>"
            })

        # Convert to DataFrame for display
        df_display = pd.DataFrame(table_data)

        # Convert the DataFrame to HTML and render it with unsafe_allow_html
        html_table = df_display.to_html(escape=False, index=False)
        st.markdown(html_table, unsafe_allow_html=True)

        # Add JavaScript for handling button clicks
        # Add a handler for form submissions
        if 'job_id' in st.experimental_get_query_params() and 'applied' in st.experimental_get_query_params():
            job_id = st.experimental_get_query_params()['job_id'][0]
            applied_str = st.experimental_get_query_params()['applied'][0]
            applied = applied_str.lower() == 'true'

            # Update the job status in the database
            success = update_job_status(user_email, int(job_id), applied)

            if success:
                # Update session state
                st.session_state.job_checkboxes[job_id] = applied
                st.toast(f"Job marked as {'applied' if applied else 'not applied'}", icon="✅")
                # Force a rerun to update the UI
                st.rerun()
            else:
                st.toast("Failed to update status", icon="❌")

        # Add JavaScript for handling button clicks
        js_code = """
        <script>
        function toggleApplied(jobId, currentStatus) {
            // Get the button element
            const button = document.getElementById('applied-' + jobId);

            // Toggle the status (convert string to boolean and negate)
            const newStatus = !(currentStatus === 'true');

            // Update button appearance immediately for better UX
            if (newStatus) {
                button.classList.remove('not-applied');
                button.classList.add('applied');
                button.innerText = 'Applied';
            } else {
                button.classList.remove('applied');
                button.classList.add('not-applied');
                button.innerText = 'Mark Applied';
            }

            // Create a form to submit the update to Streamlit
            const form = document.createElement('form');
            form.method = 'GET';
            form.action = window.location.pathname;

            // Add job ID field
            const jobIdField = document.createElement('input');
            jobIdField.type = 'hidden';
            jobIdField.name = 'job_id';
            jobIdField.value = jobId;
            form.appendChild(jobIdField);

            // Add applied status field
            const appliedField = document.createElement('input');
            appliedField.type = 'hidden';
            appliedField.name = 'applied';
            appliedField.value = newStatus;
            form.appendChild(appliedField);

            // Add to document and submit
            document.body.appendChild(form);
            form.submit();
        }
        </script>
        """

        # Add the JavaScript to the page
        st.markdown(js_code, unsafe_allow_html=True)

        # No need for separate links as they're now in the table
    else:
        # For non-logged-in users, show all jobs in a compact table with the same styling as logged-in view
        # Create a simple table with pandas and use Streamlit's native table display

        # Create table data for display
        table_data = []
        for _, row in df_jobs.iterrows():
            job_id = str(row['id'])
            job_title = row['job_title']
            company = row['company']
            location = row['location']
            date_posted = format_job_date(row['date_posted'])
            job_type = row.get('employment_type', '')

            # Add to table data
            table_data.append({
                "Job Title": job_title,
                "Company": company,
                "Location": location,
                "Posted": f"{date_posted}",
                "Type": job_type,
                "Applied": "<button class='applied-button not-applied' disabled>Login to Track</button>",
                "Apply": f"<a href='{row['job_url']}' target='_blank' class='apply-button'>Apply</a>"
            })

        # Convert to DataFrame for display
        df_display = pd.DataFrame(table_data)

        # Convert the DataFrame to HTML and render it with unsafe_allow_html
        html_table = df_display.to_html(escape=False, index=False)
        st.markdown(html_table, unsafe_allow_html=True)

        # No need for separate links as they're now in the table

        # Show login message
        st.info("Log in to track job applications")
