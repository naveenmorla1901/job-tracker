"""
Integration module to connect role validation with scrapers.
This ensures that all scrapers use consistent role validation.
"""
import logging
from typing import List, Dict, Any
from app.scrapers.role_utils import (
    filter_jobs_by_role,
    extract_roles_from_title,
    get_common_job_roles
)

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
    # If no jobs to validate, return empty list
    if not jobs:
        logger.warning("No jobs to validate")
        return []

    # If no search roles provided, use common roles
    if not search_roles:
        search_roles = get_common_job_roles()
        logger.info(f"No search roles provided, using {len(search_roles)} common roles")

    # Log the validation process
    logger.info(f"Validating {len(jobs)} scraped jobs against {len(search_roles)} roles")

    # Filter jobs by role
    valid_jobs = filter_jobs_by_role(jobs, search_roles)

    # Log the results
    if len(valid_jobs) < len(jobs):
        logger.info(f"Validation complete: {len(valid_jobs)} valid jobs out of {len(jobs)} total (removed {len(jobs) - len(valid_jobs)})")
    else:
        logger.info(f"Validation complete: All {len(jobs)} jobs passed validation")

    return valid_jobs

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