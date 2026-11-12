"""Haus jobs from its Ashby board."""
from app.scrapers.ats_boards import fetch_ashby_jobs


def get_haus_jobs(roles, days=7):
    """Return Haus jobs posted in the last `days` days, grouped by role."""
    return fetch_ashby_jobs("haus", roles, days)
