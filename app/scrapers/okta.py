"""Okta jobs from its Greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_okta_jobs(roles, days=7):
    """Return Okta jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("okta", roles, days)
