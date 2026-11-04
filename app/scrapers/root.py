"""Root Insurance jobs. Root moved from Workday to Rippling
(https://ats.rippling.com/joinroot/jobs)."""
from app.scrapers.ats_boards import fetch_rippling_jobs


def get_root_jobs(roles, days=7):
    """Return Root jobs posted in the last `days` days, grouped by role."""
    return fetch_rippling_jobs("joinroot", roles, days)
