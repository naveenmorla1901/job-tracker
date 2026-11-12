"""Reveleer jobs from its Breezy HR board."""
from app.scrapers.ats_boards import fetch_breezy_jobs


def get_reveleer_jobs(roles, days=7):
    """Return Reveleer jobs posted in the last `days` days, grouped by role."""
    return fetch_breezy_jobs("reveleer", roles, days)
