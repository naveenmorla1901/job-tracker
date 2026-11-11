"""Boston Scientific jobs.

Boston Scientific's old Workday board is gone; its current careers site is SAP
SuccessFactors Career Site Builder, whose public search page lists the jobs.
"""
from app.scrapers.ats_boards import fetch_successfactors_jobs

SEARCH_URL = "https://jobs.bostonscientific.com/search/"


def get_bostonscientific_jobs(roles, days=7):
    """Return Boston Scientific jobs posted in the last `days` days, grouped by role."""
    return fetch_successfactors_jobs(SEARCH_URL, roles, days)
