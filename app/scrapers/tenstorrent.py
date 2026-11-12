"""Tenstorrent jobs from its greenhouse board."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_tenstorrent_jobs(roles, days=7):
    """Return Tenstorrent jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("tenstorrent", roles, days)
