"""Roblox jobs from its Greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_roblox_jobs(roles, days=7):
    """Return Roblox jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("roblox", roles, days)
