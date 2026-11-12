"""Altair jobs from its Taleo v2 board."""
from app.scrapers.ats_boards import fetch_taleo_jobs

SEARCH_URL = (
    "https://phh.tbe.taleo.net/phh01/ats/careers/v2/searchResults"
    "?org=ALTAENGI&cws=39"
)


def get_altair_jobs(roles, days=7):
    """Return Altair jobs posted in the last `days` days, grouped by role."""
    return fetch_taleo_jobs(SEARCH_URL, roles, days)
