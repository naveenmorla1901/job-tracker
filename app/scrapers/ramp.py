"""Ramp jobs from its ashby board."""
from app.scrapers.ats_boards import fetch_ashby_jobs


def get_ramp_jobs(roles, days=7):
    """Return Ramp jobs posted in the last `days` days, grouped by role."""
    return fetch_ashby_jobs("ramp", roles, days)
