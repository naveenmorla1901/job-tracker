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

        # Define a callback function for checkbox changes
        def on_checkbox_change(job_id):
            # Get the current value from session state
            is_checked = st.session_state[f"cb_{job_id}"]

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
                    st.session_state[f"cb_{job_id}"] = prev_value
                    st.session_state.job_checkboxes[job_id] = prev_value

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

            # Create a unique key for each checkbox that doesn't conflict with session state
            checkbox_key = f"cb_{job_id}"

            # Add to table data
            table_data.append({
                "Job Title": f"{job_title}\n{company}",
                "Location": location,
                "Posted": f"{date_posted} • {job_type}",
                "Applied": f"<button class='applied-button {'' if is_applied else 'not-'}applied' onclick='toggleApplied(\"{job_id}\")' id='applied-{job_id}'>{'' if is_applied else 'Mark '} Applied</button>",
                "Apply": f"<a href='{row['job_url']}' target='_blank' class='apply-button'>Apply</a>"
            })

        # Convert to DataFrame for display
        df_display = pd.DataFrame(table_data)

        # Convert the DataFrame to HTML and render it with unsafe_allow_html
        html_table = df_display.to_html(escape=False, index=False)

        # Create a callback for the applied buttons
        def handle_applied_click():
            # Get the clicked job ID from the query parameters
            if 'job_id' in st.session_state and 'new_status' in st.session_state:
                job_id = st.session_state.job_id
                new_status = st.session_state.new_status

                # Update the job status in the database
                success = update_job_status(user_email, int(job_id), new_status)

                if success:
                    # Update session state
                    st.session_state.job_checkboxes[job_id] = new_status
                    st.toast(f"Job marked as {'applied' if new_status else 'not applied'}", icon="✅")
                    # Force a rerun to update the UI
                    st.rerun()
                else:
                    st.toast("Failed to update status", icon="❌")

        # Add JavaScript for toggling applied status
        js_code = """
        <script>
        // Function to create a unique key for Streamlit communication
        function generateUUID() {
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
                var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            });
        }

        // Function to handle button clicks
        function toggleApplied(jobId) {
            // Get the button element
            const button = document.getElementById('applied-' + jobId);

            // Check current state
            const isCurrentlyApplied = button.classList.contains('applied');

            // Toggle the class and text
            if (isCurrentlyApplied) {
                button.classList.remove('applied');
                button.classList.add('not-applied');
                button.textContent = 'Mark Applied';
            } else {
                button.classList.remove('not-applied');
                button.classList.add('applied');
                button.textContent = 'Applied';
            }

            // Create a unique key for this interaction
            const key = 'applied_' + generateUUID();

            // Create a form to submit the update to Streamlit
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = window.location.href;
            form.target = '_self';

            // Add job ID field
            const jobIdField = document.createElement('input');
            jobIdField.type = 'hidden';
            jobIdField.name = 'job_id';
            jobIdField.value = jobId;
            form.appendChild(jobIdField);

            // Add applied status field
            const appliedField = document.createElement('input');
            appliedField.type = 'hidden';
            appliedField.name = 'new_status';
            appliedField.value = !isCurrentlyApplied;
            form.appendChild(appliedField);

            // Add key field
            const keyField = document.createElement('input');
            keyField.type = 'hidden';
            keyField.name = 'form_key';
            keyField.value = key;
            form.appendChild(keyField);

            // Add to document and submit
            document.body.appendChild(form);
            form.submit();
        }
        </script>
        """

        # Combine the table and JavaScript
        st.markdown(html_table + js_code, unsafe_allow_html=True)

        # Check for form submissions
        query_params = st.experimental_get_query_params()
        if 'job_id' in query_params and 'new_status' in query_params:
            job_id = query_params['job_id'][0]
            new_status_str = query_params['new_status'][0]
            new_status = new_status_str.lower() == 'true'

            # Store in session state and trigger callback
            st.session_state.job_id = job_id
            st.session_state.new_status = new_status
            handle_applied_click()

        # No need for separate links as they're now in the table

        # Now add the checkboxes directly in the UI
        st.write("Mark jobs as applied:")
        for _, row in df_jobs.iterrows():
            job_id = str(row['id'])
            job_title = row['job_title']

            # Get the current value from session state
            is_applied = st.session_state.job_checkboxes.get(job_id, False)

            # Create a unique key for the checkbox
            checkbox_key = f"cb_{job_id}"

            # Display the checkbox with the job title
            if checkbox_key not in st.session_state:
                st.session_state[checkbox_key] = is_applied

            # Display the checkbox
            if st.checkbox(
                f"{job_title}",
                value=is_applied,
                key=checkbox_key,
                on_change=on_checkbox_change,
                args=(job_id,)
            ):
                # This will run when the checkbox is checked
                if not st.session_state.job_checkboxes.get(job_id, False):
                    st.session_state.job_checkboxes[job_id] = True
                    update_job_status(user_email, int(job_id), True)
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
                "Job Title": f"{job_title}\n{company}",
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
