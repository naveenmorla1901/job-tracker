"""JPMorgan Chase jobs from its Oracle HCM Candidate Experience site."""
from app.scrapers.ats_boards import fetch_oracle_hcm_jobs


def get_chase_jobs(roles, days=7):
    """Return JPMorgan Chase jobs posted in the last `days` days, grouped by role."""
    return fetch_oracle_hcm_jobs("jpmc.fa.oraclecloud.com", "CX_1001", roles, days)
