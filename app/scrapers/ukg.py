"""UKG jobs from its Eightfold PCS board."""
from app.scrapers.ats_boards import fetch_eightfold_jobs


def get_ukg_jobs(roles, days=7):
    """Return UKG jobs posted in the last `days` days, grouped by role."""
    return fetch_eightfold_jobs("https://ukg.eightfold.ai", "ukg.com", roles, days)
