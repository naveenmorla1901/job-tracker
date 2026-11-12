"""The Trade Desk jobs from its greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_thetradedesk_jobs(roles, days=7):
    """Return The Trade Desk jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("thetradedesk", roles, days)
