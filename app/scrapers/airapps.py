"""Air Apps jobs from its ashby board."""
from app.scrapers.ats_boards import fetch_ashby_jobs


def get_airapps_jobs(roles, days=7):
    """Return Air Apps jobs posted in the last `days` days, grouped by role."""
    return fetch_ashby_jobs("airapps", roles, days)
