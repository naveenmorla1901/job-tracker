"""Palantir jobs from its Lever board."""
from app.scrapers.ats_boards import fetch_lever_jobs


def get_palantir_jobs(roles, days=7):
    """Return Palantir jobs posted in the last `days` days, grouped by role."""
    return fetch_lever_jobs("palantir", roles, days)
