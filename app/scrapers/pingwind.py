"""PingWind jobs from its lever board."""
from app.scrapers.ats_boards import fetch_lever_jobs


def get_pingwind_jobs(roles, days=7):
    """Return PingWind jobs posted in the last `days` days, grouped by role."""
    return fetch_lever_jobs("pingwind", roles, days)
