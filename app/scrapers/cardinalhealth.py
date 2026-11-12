"""Cardinal Health jobs from its Workday board."""
from app.scrapers.workday_utils import fetch_workday_board_jobs

API_URL = "https://cardinalhealth.wd1.myworkdayjobs.com/wday/cxs/cardinalhealth/EXT/jobs"
BASE_URL = "https://cardinalhealth.wd1.myworkdayjobs.com/en-US/EXT"


def get_cardinalhealth_jobs(roles, days=7):
    """Return Cardinal Health jobs posted in the last `days` days, grouped by role."""
    return fetch_workday_board_jobs(API_URL, BASE_URL, roles, days)
