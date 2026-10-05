"""X jobs. X Corp merged into xAI; its old Workday site (twitter.wd5) is gone and
hiring for both runs through xAI's Greenhouse board (job-boards.greenhouse.io/xai)."""
from app.scrapers.ats_boards import fetch_greenhouse_jobs


def get_x_jobs(roles, days=7):
    """Return X / xAI jobs posted in the last `days` days, grouped by role."""
    return fetch_greenhouse_jobs("xai", roles, days)
