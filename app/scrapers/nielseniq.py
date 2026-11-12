"""NielsenIQ jobs from its smartrecruiters board."""
from app.scrapers.ats_boards import fetch_smartrecruiters_jobs


def get_nielseniq_jobs(roles, days=7):
    """Return NielsenIQ jobs posted in the last `days` days, grouped by role."""
    return fetch_smartrecruiters_jobs("NielsenIQ", roles, days)
