"""Miro jobs from its Ashby board."""
from app.scrapers.ats_boards import fetch_ashby_jobs


def get_miro_jobs(roles, days=7):
    """Return Miro jobs posted in the last `days` days, grouped by role."""
    return fetch_ashby_jobs("miro", roles, days)
