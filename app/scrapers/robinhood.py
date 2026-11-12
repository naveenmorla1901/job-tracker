"""Robinhood jobs from its greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_robinhood_jobs(roles, days=7):
    """Return Robinhood jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("Robinhood", roles, days)
