"""Box jobs from its greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_boxinc_jobs(roles, days=7):
    """Return Box jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("boxinc", roles, days)
