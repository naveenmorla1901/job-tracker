"""Twilio jobs from its Greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_twilio_jobs(roles, days=7):
    """Return Twilio jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("twilio", roles, days)
