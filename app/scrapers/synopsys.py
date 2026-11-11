"""Synopsys jobs.

Synopsys' old Workday board is gone; its current careers site runs on
TalentBrew (Radancy), whose search-results AJAX endpoint returns the same job
cards as the public page.
"""
from app.scrapers.ats_boards import fetch_talentbrew_jobs

BASE_URL = "https://careers.synopsys.com"


def get_synopsys_jobs(roles, days=7):
    """Return Synopsys jobs posted in the last `days` days, grouped by role."""
    return fetch_talentbrew_jobs(BASE_URL, roles, days)
