"""Instacart jobs from its Greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_instacart_jobs(roles, days=7):
    """Return Instacart jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("instacart", roles, days)
