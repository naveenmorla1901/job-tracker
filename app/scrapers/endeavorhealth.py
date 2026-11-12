"""Endeavor Health jobs from its Workday board."""
from app.scrapers.workday_utils import fetch_workday_board_jobs

API_URL = "https://nshs.wd1.myworkdayjobs.com/wday/cxs/nshs/ns-eeh/jobs"
BASE_URL = "https://nshs.wd1.myworkdayjobs.com/ns-eeh"


def get_endeavorhealth_jobs(roles, days=7):
    """Return Endeavor Health jobs posted in the last `days` days, grouped by role."""
    return fetch_workday_board_jobs(API_URL, BASE_URL, roles, days)
