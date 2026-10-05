"""Amplify jobs. Amplify moved from Workday to Ashby (jobs.ashbyhq.com/amplify)."""
from app.scrapers.ats_boards import fetch_ashby_jobs


def get_amplify_jobs(roles, days=7):
    """Return Amplify jobs posted in the last `days` days, grouped by role."""
    return fetch_ashby_jobs("amplify", roles, days)
