"""Donor Network West jobs from its lever board."""
from app.scrapers.ats_boards import fetch_lever_jobs


def get_dnwest_jobs(roles, days=7):
    """Return Donor Network West jobs posted in the last `days` days, grouped by role."""
    return fetch_lever_jobs("dnwest", roles, days)
