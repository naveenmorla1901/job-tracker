"""Perficient jobs from its Oracle HCM Candidate Experience site."""
from app.scrapers.ats_boards import fetch_oracle_hcm_jobs


def get_perficient_jobs(roles, days=7):
    """Return Perficient jobs posted in the last `days` days, grouped by role."""
    return fetch_oracle_hcm_jobs("fa-etqd-saasfaprod1.fa.ocs.oraclecloud.com", "CX_1", roles, days)
