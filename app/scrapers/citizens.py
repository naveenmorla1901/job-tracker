"""Citizens jobs from its Oracle HCM Candidate Experience site."""
from app.scrapers.ats_boards import fetch_oracle_hcm_jobs


def get_citizens_jobs(roles, days=7):
    """Return Citizens jobs posted in the last `days` days, grouped by role."""
    return fetch_oracle_hcm_jobs("hcgn.fa.us2.oraclecloud.com", "CX_1", roles, days)
