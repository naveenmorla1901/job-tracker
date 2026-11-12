"""Vertiv jobs from its Oracle HCM Candidate Experience site."""
from app.scrapers.ats_boards import fetch_oracle_hcm_jobs


def get_vertiv_jobs(roles, days=7):
    """Return Vertiv jobs posted in the last `days` days, grouped by role."""
    return fetch_oracle_hcm_jobs("egup.fa.us2.oraclecloud.com", "CX", roles, days)
