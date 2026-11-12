"""Affirm jobs from its Greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_affirm_jobs(roles, days=7):
    """Return Affirm jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("affirm", roles, days)
