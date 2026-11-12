"""Notion jobs from its Ashby board."""
from app.scrapers.ats_boards import fetch_ashby_jobs


def get_notion_jobs(roles, days=7):
    """Return Notion jobs posted in the last `days` days, grouped by role."""
    return fetch_ashby_jobs("notion", roles, days)
