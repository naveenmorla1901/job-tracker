"""Moloco jobs from its greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_moloco_jobs(roles, days=7):
    """Return Moloco jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("moloco", roles, days)
