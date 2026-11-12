"""Upgrade jobs from its greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_upgrade_jobs(roles, days=7):
    """Return Upgrade jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("upgrade", roles, days)
