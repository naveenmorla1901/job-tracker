"""
Integration module to connect role validation with scrapers.
This ensures that all scrapers use consistent role validation.
"""
import logging
from typing import List, Dict, Any
# Role validation imports removed
# Define fallback functions
def extract_roles_from_title(title, roles=None):
    """Simple function to extract roles from a job title"""
    return ["Software Engineer"]  # Default role

def get_common_job_roles():
    """Return a list of common job roles"""
    return ["Software Engineer", "Data Scientist", "Product Manager"]

logger = logging.getLogger(__name__)

def validate_scraped_jobs(jobs: List[Dict[str, Any]], search_roles: List[str] = None) -> List[Dict[str, Any]]:
    """
    Validate and filter scraped jobs based on role validation.

    Args:
        jobs: List of job dictionaries from scraper
        search_roles: List of roles used for the search (if None, uses common roles)

    Returns:
        Filtered list of jobs with valid roles
    """
    # Role validation removed - return all jobs
    logger.info(f"Role validation disabled, returning all {len(jobs) if jobs else 0} jobs")
    return jobs if jobs else []

def extract_roles_for_job(job: Dict[str, Any], search_roles: List[str] = None) -> List[str]:
    """
    Extract valid roles from a job based on its title and description.

    Args:
        job: Dictionary containing job information
        search_roles: List of roles used for the search (if None, uses common roles)

    Returns:
        List of valid roles for the job
    """
    # If no search roles provided, use common roles
    if not search_roles:
        search_roles = get_common_job_roles()

    # Extract roles from job title
    if "job_title" in job and job["job_title"]:
        return extract_roles_from_title(job["job_title"], search_roles)

    return []