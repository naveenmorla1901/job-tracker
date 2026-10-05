"""Socure jobs. Socure moved from Workday to Ashby (jobs.ashbyhq.com/socure)."""
from app.scrapers.ats_boards import fetch_ashby_jobs


def get_socure_jobs(roles, days=7):
    """Return Socure jobs posted in the last `days` days, grouped by role."""
    return fetch_ashby_jobs("socure", roles, days)
