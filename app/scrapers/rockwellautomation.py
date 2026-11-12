"""Rockwell Automation jobs from its Workday board."""
from app.scrapers.workday_utils import fetch_workday_board_jobs

API_URL = "https://rockwellautomation.wd1.myworkdayjobs.com/wday/cxs/rockwellautomation/external_rockwell_automation/jobs"
BASE_URL = "https://rockwellautomation.wd1.myworkdayjobs.com/en-US/external_rockwell_automation"


def get_rockwellautomation_jobs(roles, days=7):
    """Return Rockwell Automation jobs posted in the last `days` days, grouped by role."""
    return fetch_workday_board_jobs(API_URL, BASE_URL, roles, days)
