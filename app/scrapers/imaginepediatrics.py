"""Imagine Pediatrics jobs from its greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_imaginepediatrics_jobs(roles, days=7):
    """Return Imagine Pediatrics jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("imaginepediatrics", roles, days)
