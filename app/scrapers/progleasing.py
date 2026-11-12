"""Prog Leasing jobs from its Workday board."""
from app.scrapers.workday_utils import fetch_workday_board_jobs

API_URL = "https://progleasing.wd5.myworkdayjobs.com/wday/cxs/progleasing/ProgLeasingCareers/jobs"
BASE_URL = "https://progleasing.wd5.myworkdayjobs.com/en-US/ProgLeasingCareers"


def get_progleasing_jobs(roles, days=7):
    """Return Prog Leasing jobs posted in the last `days` days, grouped by role."""
    return fetch_workday_board_jobs(API_URL, BASE_URL, roles, days)
