"""
Jobs table with colour-coded Apply button that auto-tracks applications.
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import html as html_lib
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
            applied_ids.add(job_id_str)
        st.query_params.clear()

    st.header("Job Listings")

    # --- Sort ---------------------------------------------------------------
    if "first_seen" in df_jobs.columns:
        df_jobs = df_jobs.sort_values(by="first_seen", ascending=False)
    else:
        df_jobs = df_jobs.sort_values(by="date_posted", ascending=False)

    # --- Build HTML table rows ----------------------------------------------
    rows_html = ""
    for _, row in df_jobs.iterrows():
        job_id = str(row["id"])
        date_posted = html_lib.escape(str(format_job_date(row.get("first_seen", row["date_posted"]))))
        job_url = html_lib.escape(row["job_url"].strip() if isinstance(row.get("job_url"), str) else "#")
        title = html_lib.escape(str(row["job_title"]))
        company = html_lib.escape(str(row["company"]))
        location = html_lib.escape(str(row["location"]))
        job_type = html_lib.escape(str(row.get("employment_type", "N/A")))
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
                    f"data-job-id='{job_id}'>Apply Now</a>"
                )
        else:
            btn = (
                f"<a href='{job_url}' target='_blank' "
                f"class='apply-btn apply-btn-new'>Apply Now</a>"
            )

        rows_html += (
            f"<tr>"
            f"<td>{title}</td>"
            f"<td>{company}</td>"
            f"<td>{location}</td>"
            f"<td>{date_posted}</td>"
            f"<td>{job_type}</td>"
            f"<td style='text-align:center'>{btn}</td>"
            f"</tr>\n"
        )

    num_rows = len(df_jobs)
    table_height = min(60 + num_rows * 42, 2000)

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Source Sans Pro", sans-serif; font-size: 0.9rem; color: #fafafa; background: transparent; }}
        table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
        th {{ background-color: #1E1E1E; color: white; text-align: left; padding: 8px;
              font-size: 0.9rem; font-weight: bold; border-bottom: 1px solid #444;
              position: sticky; top: 0; z-index: 2; }}
        td {{ padding: 8px; border-bottom: 1px solid #333; vertical-align: middle;
              overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
        tr:hover {{ background-color: rgba(200, 200, 200, 0.1); }}

        th:nth-child(1), td:nth-child(1) {{ width: 25%; }}
        th:nth-child(2), td:nth-child(2) {{ width: 18%; }}
        th:nth-child(3), td:nth-child(3) {{ width: 17%; }}
        th:nth-child(4), td:nth-child(4) {{ width: 20%; font-weight: bold; }}
        th:nth-child(5), td:nth-child(5) {{ width: 12%; }}
        th:nth-child(6), td:nth-child(6) {{ width: 8%; text-align: center; }}

        .apply-btn {{
            display: inline-block; padding: 4px 10px;
            text-decoration: none; border-radius: 4px;
            font-size: 0.78rem; text-align: center;
            min-width: 80px; cursor: pointer; border: none;
            transition: background-color 0.3s;
        }}
        .apply-btn:hover {{ opacity: 0.85; }}
        .apply-btn-new {{ background-color: #1E90FF; color: white; }}
        .apply-btn-done {{ background-color: #4CAF50; color: white; }}
    </style>
    </head>
    <body>
    <table>
        <thead>
            <tr>
                <th>Job Title</th><th>Company</th><th>Location</th>
                <th>Posted Date</th><th>Job Type</th><th>Apply</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    <script>
        document.querySelectorAll('a.apply-btn-new[data-job-id]').forEach(function(btn) {{
            btn.addEventListener('click', function(e) {{
                var jobId = this.getAttribute('data-job-id');

                // Immediately flip the button to green "Applied"
                this.classList.remove('apply-btn-new');
                this.classList.add('apply-btn-done');
                this.textContent = 'Applied';
                this.removeAttribute('data-job-id');

                // Tell Streamlit (parent frame) to persist via query param
                try {{
                    var parentUrl = new URL(window.parent.location.href);
                    parentUrl.searchParams.set('mark_applied', jobId);
                    window.parent.location.href = parentUrl.toString();
                }} catch(err) {{
                    console.error('Could not notify parent:', err);
                }}
            }});
        }});
    </script>
    </body>
    </html>
    """

    components.html(full_html, height=table_height, scrolling=True)
