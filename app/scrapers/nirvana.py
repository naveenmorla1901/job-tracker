"""Nirvana Insurance jobs from its ashby board."""
from app.scrapers.ats_boards import fetch_ashby_jobs


def get_nirvana_jobs(roles, days=7):
    """Return Nirvana Insurance jobs posted in the last `days` days, grouped by role."""
    return fetch_ashby_jobs("nirvana", roles, days)
