"""Lower jobs. Lower moved from Workday to Gem (https://jobs.gem.com/lower-llc)."""
from app.scrapers.ats_boards import fetch_gem_jobs


def get_lower_jobs(roles, days=7):
    """Return Lower jobs posted in the last `days` days, grouped by role."""
    return fetch_gem_jobs("lower-llc", roles, days)
