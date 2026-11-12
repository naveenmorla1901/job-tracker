"""Anthropic jobs from its greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_anthropic_jobs(roles, days=7):
    """Return Anthropic jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("anthropic", roles, days)
