"""Prologis jobs from its Workday board."""
from app.scrapers.workday_utils import fetch_workday_board_jobs

API_URL = "https://prologis.wd5.myworkdayjobs.com/wday/cxs/prologis/Prologis_External_Careers/jobs"
BASE_URL = "https://prologis.wd5.myworkdayjobs.com/en-US/Prologis_External_Careers"


def get_prologis_jobs(roles, days=7):
    """Return Prologis jobs posted in the last `days` days, grouped by role."""
    return fetch_workday_board_jobs(API_URL, BASE_URL, roles, days)
