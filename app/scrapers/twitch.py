"""Twitch jobs from its Greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_twitch_jobs(roles, days=7):
    """Return Twitch jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("twitch", roles, days)
