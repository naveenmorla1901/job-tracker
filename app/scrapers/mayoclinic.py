"""Mayo Clinic jobs from its Oracle HCM Candidate Experience site."""
from app.scrapers.ats_boards import fetch_oracle_hcm_jobs


def get_mayoclinic_jobs(roles, days=7):
    """Return Mayo Clinic jobs posted in the last `days` days, grouped by role."""
    return fetch_oracle_hcm_jobs("fa-euwp-saasfaprod1.fa.ocs.oraclecloud.com", "CX_1", roles, days)
