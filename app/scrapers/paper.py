"""Paper jobs. Paper moved from Workday to Rippling
(https://ats.rippling.com/paper-careers/jobs)."""
from app.scrapers.ats_boards import fetch_rippling_jobs


def get_paper_jobs(roles, days=7):
    """Return Paper jobs posted in the last `days` days, grouped by role."""
    return fetch_rippling_jobs("paper-careers", roles, days)
