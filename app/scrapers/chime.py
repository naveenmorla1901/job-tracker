"""Chime jobs from its Greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_chime_jobs(roles, days=7):
    """Return Chime jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("chime", roles, days)
