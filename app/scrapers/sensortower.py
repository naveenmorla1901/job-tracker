"""Sensor Tower jobs from its Ashby board."""
from app.scrapers.ats_boards import fetch_ashby_jobs


def get_sensortower_jobs(roles, days=7):
    """Return Sensor Tower jobs posted in the last `days` days, grouped by role."""
    return fetch_ashby_jobs("sensor-tower", roles, days)
