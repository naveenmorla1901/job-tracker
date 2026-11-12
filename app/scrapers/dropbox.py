"""Dropbox jobs from its Greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_dropbox_jobs(roles, days=7):
    """Return Dropbox jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("dropbox", roles, days)
