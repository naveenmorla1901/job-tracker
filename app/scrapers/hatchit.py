"""HatchIt jobs from its lever board."""
from app.scrapers.ats_boards import fetch_lever_jobs


def get_hatchit_jobs(roles, days=7):
    """Return HatchIt jobs posted in the last `days` days, grouped by role."""
    return fetch_lever_jobs("hatchit", roles, days)
