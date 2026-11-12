"""Point72 jobs from its greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_point72_jobs(roles, days=7):
    """Return Point72 jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("point72", roles, days)
