"""
Jobs table with colour-coded Apply button that auto-tracks applications.
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


def _get_user_by_email(db, email):
    return db.query(User).filter(User.email == email).first()


def get_tracked_jobs(user_email):
    """Return a set of job-id strings the user has already applied to."""
    try:
        db = next(get_db())
        user = _get_user_by_email(db, user_email)
        if not user:
            return set()
        rows = db.query(UserJob.job_id).filter(
            UserJob.user_id == user.id,
            UserJob.is_applied == True,  # noqa: E712
        ).all()
        return {str(r.job_id) for r in rows}
    except Exception as e:
        logger.error(f"Error getting tracked jobs: {e}")
        return set()


def mark_job_applied(user_email, job_id):
    """Upsert a UserJob row with is_applied=True."""
    try:
        db = next(get_db())
        user = _get_user_by_email(db, user_email)
        if not user:
            return False
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return False

        user_job = db.query(UserJob).filter(
            UserJob.user_id == user.id,
            UserJob.job_id == job_id,
        ).first()

        if user_job:
            user_job.is_applied = True
            user_job.date_updated = datetime.now(timezone.utc)
        else:
            user_job = UserJob(
                user_id=user.id,
                job_id=job_id,
                is_applied=True,
                date_saved=datetime.now(timezone.utc),
            )
            db.add(user_job)

        db.commit()
        return True
    except Exception as e:
        logger.error(f"Error marking job applied: {e}")
        db.rollback()
        return False


def display_custom_jobs_table(df_jobs):
    """Render the jobs table.

    Logged-in users: clicking "Apply Now" opens the external URL *and*
    marks the job as applied in the DB.  Already-applied jobs show a
    green "Applied" button instead of blue.
    """

    user_email = None
    if is_authenticated():
        user = get_current_user()
        if user and "email" in user:
            user_email = user["email"]

    applied_ids: set = set()
    if user_email:
        applied_ids = get_tracked_jobs(user_email)

    # --- Handle incoming "mark applied" callback via query params ----------
    if user_email and "mark_applied" in st.query_params:
        job_id_str = st.query_params["mark_applied"]
        if job_id_str not in applied_ids:
            mark_job_applied(user_email, int(job_id_str))
        st.query_params.clear()
        st.rerun()

    # --- CSS ---------------------------------------------------------------
    st.markdown("""
    <style>
    .stContainer, .block-container, .element-container {
        padding-top: 0 !important;
        padding-bottom: 0 !important;
        margin-top: 0 !important;
        margin-bottom: 0 !important;
    }
    div.stMarkdown p {
        margin-bottom: 0 !important;
        margin-top: 0 !important;
        line-height: 1 !important;
        padding: 0 !important;
    }
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

    table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 20px;
        table-layout: fixed;
        max-width: 100%;
    }
    .stMarkdown {
        margin-left: -20px;
        margin-right: -20px;
        width: calc(100% + 40px);
    }

    /* Column widths */
    table th:nth-child(1), table td:nth-child(1) { width: 25%; }              /* Job Title */
    table th:nth-child(2), table td:nth-child(2) { width: 18%; }              /* Company */
    table th:nth-child(3), table td:nth-child(3) { width: 17%; }              /* Location */
    table th:nth-child(4), table td:nth-child(4) {                            /* Posted Date */
        width: 20%;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-weight: bold;
    }
    table th:nth-child(5), table td:nth-child(5) { width: 12%; }              /* Job Type */
    table th:nth-child(6), table td:nth-child(6) { width: 8%; text-align: center; }  /* Apply */

    th {
        background-color: #1E1E1E; color: white;
        text-align: left; padding: 8px;
        font-size: 0.9rem; font-weight: bold;
        border-bottom: 1px solid #444;
    }
    td { padding: 8px; border-bottom: 1px solid #333; vertical-align: middle; }
    tr:hover { background-color: rgba(200, 200, 200, 0.1); }

    /* Apply / Applied button */
    .apply-btn {
        display: inline-block; padding: 4px 10px;
        text-decoration: none; border-radius: 4px;
        font-size: 0.78rem; text-align: center;
        min-width: 80px; cursor: pointer; border: none;
        transition: opacity 0.2s;
    }
    .apply-btn:hover { opacity: 0.85; }
    .apply-btn-new {
        background-color: #1E90FF; color: white;
    }
    .apply-btn-done {
        background-color: #4CAF50; color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    st.header("Job Listings")

    # --- Sort ---------------------------------------------------------------
    if "first_seen" in df_jobs.columns:
        df_jobs = df_jobs.sort_values(by="first_seen", ascending=False)
    else:
        df_jobs = df_jobs.sort_values(by="date_posted", ascending=False)

    # --- Build table rows ---------------------------------------------------
    table_data = []
    for _, row in df_jobs.iterrows():
        job_id = str(row["id"])
        date_posted = format_job_date(row.get("first_seen", row["date_posted"]))
        job_url = row["job_url"].strip() if isinstance(row.get("job_url"), str) else "#"
        already_applied = job_id in applied_ids

        if user_email:
            if already_applied:
                btn = (
                    f"<a href='{job_url}' target='_blank' "
                    f"class='apply-btn apply-btn-done'>Applied</a>"
                )
            else:
                btn = (
                    f"<a href='{job_url}' target='_blank' "
                    f"class='apply-btn apply-btn-new' "
                    f"onclick=\"markApplied('{job_id}')\">Apply Now</a>"
                )
        else:
            btn = (
                f"<a href='{job_url}' target='_blank' "
                f"class='apply-btn apply-btn-new'>Apply Now</a>"
            )

        table_data.append({
            "Job Title": row["job_title"],
            "Company": row["company"],
            "Location": row["location"],
            "Posted Date": date_posted,
            "Job Type": row.get("employment_type", "N/A"),
            "Apply": btn,
        })

    df_display = pd.DataFrame(table_data)
    html_table = df_display.to_html(escape=False, index=False)
    st.markdown(html_table, unsafe_allow_html=True)

    # --- JS: mark applied via query-param round-trip ------------------------
    if user_email:
        st.markdown("""
        <script>
        function markApplied(jobId) {
            const url = new URL(window.location.href);
            url.searchParams.set('mark_applied', jobId);
            // Small delay so the browser opens the job link first
            setTimeout(() => { window.location.href = url.toString(); }, 300);
        }
        </script>
        """, unsafe_allow_html=True)
