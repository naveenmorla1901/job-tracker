"""Aicadium jobs from its BambooHR board."""
from app.scrapers.ats_boards import fetch_bamboohr_jobs


def get_aicadium_jobs(roles, days=7):
    """Return Aicadium jobs posted in the last `days` days, grouped by role."""
    return fetch_bamboohr_jobs("aicadium", roles, days)
