"""Tubi jobs from its greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_tubitv_jobs(roles, days=7):
    """Return Tubi jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("tubitv", roles, days)
