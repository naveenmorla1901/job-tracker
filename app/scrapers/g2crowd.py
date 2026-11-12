"""G2 jobs from its Ashby board."""
from app.scrapers.ats_boards import fetch_ashby_jobs


def get_g2crowd_jobs(roles, days=7):
    """Return G2 jobs posted in the last `days` days, grouped by role."""
    return fetch_ashby_jobs("g2", roles, days)
