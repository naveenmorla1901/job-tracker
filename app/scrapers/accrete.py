"""Accrete jobs from its Breezy HR board."""
from app.scrapers.ats_boards import fetch_breezy_jobs


def get_accrete_jobs(roles, days=7):
    """Return Accrete jobs posted in the last `days` days, grouped by role."""
    return fetch_breezy_jobs("accrete-ai", roles, days)
