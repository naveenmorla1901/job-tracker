"""Spotify jobs from its Lever board."""
from app.scrapers.ats_boards import fetch_lever_jobs


def get_spotify_jobs(roles, days=7):
    """Return Spotify jobs posted in the last `days` days, grouped by role."""
    return fetch_lever_jobs("spotify", roles, days)
