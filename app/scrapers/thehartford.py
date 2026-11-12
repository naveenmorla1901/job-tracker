"""The Hartford jobs from its Workday board."""
from app.scrapers.workday_utils import fetch_workday_board_jobs

API_URL = "https://thehartford.wd5.myworkdayjobs.com/wday/cxs/thehartford/Careers_External/jobs"
BASE_URL = "https://thehartford.wd5.myworkdayjobs.com/en-US/Careers_External"


def get_thehartford_jobs(roles, days=7):
    """Return The Hartford jobs posted in the last `days` days, grouped by role."""
    return fetch_workday_board_jobs(API_URL, BASE_URL, roles, days)
