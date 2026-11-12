"""Adswerve jobs from its greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_adswerveinc_jobs(roles, days=7):
    """Return Adswerve jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("adswerveinc", roles, days)
