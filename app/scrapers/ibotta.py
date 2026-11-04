"""Ibotta jobs. Ibotta moved from Workday to Ashby (jobs.ashbyhq.com/ibotta)."""
from app.scrapers.ats_boards import fetch_ashby_jobs


def get_ibotta_jobs(roles, days=7):
    """Return Ibotta jobs posted in the last `days` days, grouped by role."""
    return fetch_ashby_jobs("ibotta", roles, days)
