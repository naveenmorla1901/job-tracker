"""Oracle jobs from its Oracle HCM Candidate Experience site."""
from app.scrapers.ats_boards import fetch_oracle_hcm_jobs


def get_oraclecloud_jobs(roles, days=7):
    """Return Oracle jobs posted in the last `days` days, grouped by role."""
    return fetch_oracle_hcm_jobs("eeho.fa.us2.oraclecloud.com", "jobsearch", roles, days)
