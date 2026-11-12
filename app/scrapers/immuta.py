"""Immuta jobs from its lever board."""
from app.scrapers.ats_boards import fetch_lever_jobs


def get_immuta_jobs(roles, days=7):
    """Return Immuta jobs posted in the last `days` days, grouped by role."""
    return fetch_lever_jobs("immuta", roles, days)
