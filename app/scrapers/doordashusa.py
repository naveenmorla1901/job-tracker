"""DoorDash jobs from its greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_doordashusa_jobs(roles, days=7):
    """Return DoorDash jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("doordashusa", roles, days)
