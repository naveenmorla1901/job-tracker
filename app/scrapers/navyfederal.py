"""Navy Federal Credit Union jobs from its Oracle HCM Candidate Experience site."""
from app.scrapers.ats_boards import fetch_oracle_hcm_jobs


def get_navyfederal_jobs(roles, days=7):
    """Return Navy Federal Credit Union jobs posted in the last `days` days, grouped by role."""
    return fetch_oracle_hcm_jobs("fa-etbx-saasfaprod1.fa.ocs.oraclecloud.com", "CX_1001", roles, days)
