"""Pinterest jobs from its Greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_pinterest_jobs(roles, days=7):
    """Return Pinterest jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("pinterest", roles, days)
