"""
Utility functions for validating and processing job roles.
This module provides functions to ensure that only relevant roles are extracted from job listings.
"""
import re
import logging
from typing import List, Dict, Any, Set
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)

# Global dictionary to track filtered roles
# Using defaultdict to automatically create entries
# Structure: {company_name: {role: count}}
_filtered_roles = defaultdict(lambda: defaultdict(int))
_filtered_roles_lock = threading.Lock()  # Thread safety for tracking

# List of valid role keywords that should be present in the extracted roles
VALID_ROLE_KEYWORDS = {
    # Data Science & Analytics
    "data scientist", "data science", "machine learning", "ml", "ai", "artificial intelligence",
    "data analyst", "analytics", "statistical", "statistician", "data mining",

    # Engineering & Development
    "software engineer", "developer", "engineer", "engineering", "development", "programmer",
    "frontend", "backend", "full stack", "fullstack", "web developer", "mobile developer",

    # Machine Learning & AI
    "machine learning engineer", "ml engineer", "ai engineer", "ai researcher",
    "neural network", "deep learning", "computer vision", "cv", "nlp", "natural language",
    "generative ai", "reinforcement learning", "data mining",

    # Technical Roles
    "data engineer", "devops", "sre", "site reliability", "cloud", "architect",
    "database", "sql", "python", "java", "javascript", "typescript", "react", "node",
    "security", "network", "systems", "infrastructure", "operations",

    # Management & Leadership
    "lead", "manager", "director", "head", "principal", "senior", "staff", "technical lead",

    # Additional roles that might be getting filtered out
    "analyst", "specialist", "consultant", "scientist", "researcher", "administrator",
    "architect", "designer", "product", "project", "program", "solution", "support",
    "tech", "technology", "it", "information technology", "application", "platform"
}

def normalize_role(role: str) -> str:
    """
    Normalize a role string by converting to lowercase and removing extra whitespace.

    Args:
        role: The role string to normalize

    Returns:
        Normalized role string
    """
    # Convert to lowercase
    role = role.lower()

    # Remove non-alphanumeric characters except spaces
    role = re.sub(r'[^\w\s]', ' ', role)

    # Replace multiple spaces with a single space
    role = re.sub(r'\s+', ' ', role)

    # Strip leading and trailing whitespace
    return role.strip()

def is_valid_role(role: str, input_roles: List[str]) -> bool:
    """
    Check if a role is valid by comparing it with input roles and valid role keywords.

    Args:
        role: The role to validate
        input_roles: List of input roles used for the search

    Returns:
        True if the role is valid, False otherwise
    """
    if not role:
        return False

    # Normalize the role
    normalized_role = normalize_role(role)

    # Log the role being validated for debugging
    logger.debug(f"Validating role: {role} (normalized: {normalized_role})")

    # If input_roles is empty, consider all roles valid
    if not input_roles:
        logger.debug(f"No input roles provided, considering role '{role}' valid")
        return True

    # Check if the role contains any valid role keywords
    if any(keyword in normalized_role for keyword in VALID_ROLE_KEYWORDS):
        logger.debug(f"Role '{role}' contains valid keyword")
        return True

    # If the role contains numbers (like O9 Technical Architect), be more lenient
    if re.search(r'\d', normalized_role):
        # If it contains any tech keyword, consider it valid
        tech_keywords = ["python", "java", "sql", "node", "react", "angular", "developer", "engineer", "architect"]
        if any(tech in normalized_role for tech in tech_keywords):
            logger.debug(f"Role '{role}' contains tech keyword with number")
            return True

        # Check if it's explicitly requested in input roles
        if any(normalize_role(input_role) in normalized_role for input_role in input_roles):
            logger.debug(f"Role '{role}' matches input role despite containing numbers")
            return True

    # Check if the role is similar to any of the input roles
    for input_role in input_roles:
        normalized_input = normalize_role(input_role)

        # Check for exact match
        if normalized_input == normalized_role:
            logger.debug(f"Role '{role}' exactly matches input role '{input_role}'")
            return True

        # Check if the normalized input role is contained in the normalized role
        if normalized_input in normalized_role:
            logger.debug(f"Role '{role}' contains input role '{input_role}'")
            return True

        # Check if the normalized role is contained in the input role
        if normalized_role in normalized_input:
            logger.debug(f"Input role '{input_role}' contains role '{role}'")
            return True

        # Check for word overlap (at least one significant word in common)
        input_words = normalized_input.split()
        role_words = normalized_role.split()

        # Filter out common stop words
        stop_words = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "with", "by", "of"}
        input_words = [w for w in input_words if w not in stop_words]

        if any(word in role_words for word in input_words):
            logger.debug(f"Role '{role}' shares words with input role '{input_role}'")
            return True

    logger.debug(f"Role '{role}' did not match any validation criteria")
    return False

def track_filtered_role(company: str, role: str, job_count: int = 1) -> None:
    """
    Track a role that was filtered out during validation.

    Args:
        company: The company name (scraper name)
        role: The role that was filtered out
        job_count: Number of jobs with this role
    """
    with _filtered_roles_lock:
        _filtered_roles[company][role] += job_count
        logger.debug(f"Tracked filtered role: {role} from {company} (count: {_filtered_roles[company][role]})")

def get_filtered_roles() -> Dict[str, Dict[str, int]]:
    """
    Get a dictionary of all filtered roles.

    Returns:
        Dictionary with company names as keys and dictionaries of {role: count} as values
    """
    with _filtered_roles_lock:
        # Create a copy to avoid threading issues
        return {company: dict(roles) for company, roles in _filtered_roles.items()}

def clear_filtered_roles() -> None:
    """
    Clear the filtered roles tracking data.
    """
    with _filtered_roles_lock:
        _filtered_roles.clear()
        logger.info("Cleared filtered roles tracking data")

def filter_roles(job_data: Dict[str, Any], input_roles: List[str], company: str = "unknown") -> Dict[str, Any]:
    """
    Filter job data to only include valid roles.

    Args:
        job_data: Dictionary of job data with roles as keys
        input_roles: List of input roles used for the search
        company: The company name (scraper name) for tracking filtered roles

    Returns:
        Filtered job data with only valid roles
    """
    # If no input roles provided, return all data
    if not input_roles:
        logger.info(f"No input roles provided, returning all {len(job_data)} roles")
        return job_data

    filtered_data = {}

    for role, jobs in job_data.items():
        normalized_role = normalize_role(role)

        if is_valid_role(normalized_role, input_roles):
            filtered_data[role] = jobs
            logger.debug(f"Keeping valid role: {role} with {len(jobs)} jobs")
        else:
            # Track the filtered role
            track_filtered_role(company, role, len(jobs))
            logger.info(f"Filtered out invalid role: {role} with {len(jobs)} jobs")

    # Log the filtering results
    if len(filtered_data) < len(job_data):
        logger.info(f"Filtered roles: {len(job_data)} -> {len(filtered_data)} (removed {len(job_data) - len(filtered_data)})")
    else:
        logger.info(f"All {len(job_data)} roles passed validation")

    return filtered_data

def extract_roles_from_title(job_title: str, input_roles: List[str]) -> List[str]:
    """
    Extract valid roles from a job title based on input roles and known valid roles.

    Args:
        job_title: The job title to extract roles from
        input_roles: List of input roles used for the search

    Returns:
        List of valid roles extracted from the job title
    """
    if not job_title:
        return []

    normalized_title = normalize_role(job_title)
    extracted_roles = []

    # Check for exact matches with valid role keywords
    for keyword in VALID_ROLE_KEYWORDS:
        if keyword in normalized_title:
            extracted_roles.append(keyword)

    # Check for similarity with input roles
    for input_role in input_roles:
        normalized_input = normalize_role(input_role)
        input_words = normalized_input.split()
        title_words = normalized_title.split()

        # Filter out common stop words
        stop_words = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "with", "by", "of"}
        input_words = [w for w in input_words if w not in stop_words]

        # Check if any significant input words are in the title
        if any(word in title_words for word in input_words):
            extracted_roles.append(input_role)

    # Remove duplicates while preserving order
    seen = set()
    return [role for role in extracted_roles if not (role in seen or seen.add(role))]

def validate_job_roles(job: Dict[str, Any], input_roles: List[str]) -> bool:
    """
    Validate if a job has relevant roles based on its title and description.

    Args:
        job: Dictionary containing job information
        input_roles: List of input roles used for the search

    Returns:
        True if the job has valid roles, False otherwise
    """
    job_id = job.get("job_id", "unknown")
    job_title = job.get("job_title", "")

    # If no input roles provided, consider all jobs valid
    if not input_roles:
        logger.debug(f"No input roles provided, considering job '{job_id}' ({job_title}) valid")
        return True

    # Check job title
    if "job_title" in job and job["job_title"]:
        if is_valid_role(job["job_title"], input_roles):
            logger.debug(f"Job '{job_id}' has valid title: {job_title}")
            return True

    # Check description (if available)
    if "description" in job and job["description"]:
        normalized_desc = normalize_role(job["description"])

        # Check if any input role is in the description
        for input_role in input_roles:
            normalized_input = normalize_role(input_role)
            if normalized_input in normalized_desc:
                logger.debug(f"Job '{job_id}' has input role '{input_role}' in description")
                return True

        # Check if any valid role keyword is in the description
        for keyword in VALID_ROLE_KEYWORDS:
            if keyword in normalized_desc:
                logger.debug(f"Job '{job_id}' has valid keyword '{keyword}' in description")
                return True

    # If we have explicit roles field
    if "roles" in job and job["roles"]:
        for role in job["roles"]:
            if is_valid_role(role, input_roles):
                logger.debug(f"Job '{job_id}' has valid explicit role: {role}")
                return True

    # Additional check: if job title contains any word from input roles
    if job_title:
        normalized_title = normalize_role(job_title)
        title_words = set(normalized_title.split())

        for input_role in input_roles:
            normalized_input = normalize_role(input_role)
            input_words = set(normalized_input.split())

            # Check for any word overlap
            common_words = title_words.intersection(input_words)
            if common_words and any(len(word) > 3 for word in common_words):  # Only consider significant words
                logger.debug(f"Job '{job_id}' title shares words with input role '{input_role}': {common_words}")
                return True

    logger.debug(f"Job '{job_id}' ({job_title}) did not match any validation criteria")
    return False

def filter_jobs_by_role(jobs: List[Dict[str, Any]], input_roles: List[str]) -> List[Dict[str, Any]]:
    """
    Filter a list of jobs to only include those with valid roles.

    Args:
        jobs: List of job dictionaries
        input_roles: List of input roles used for the search

    Returns:
        Filtered list of jobs with valid roles
    """
    if not input_roles:
        logger.info(f"No input roles provided, returning all {len(jobs)} jobs")
        return jobs

    filtered_jobs = [job for job in jobs if validate_job_roles(job, input_roles)]

    # Log the filtering results
    if len(filtered_jobs) < len(jobs):
        logger.info(f"Filtered jobs: {len(jobs)} -> {len(filtered_jobs)} (removed {len(jobs) - len(filtered_jobs)})")
    else:
        logger.info(f"All {len(jobs)} jobs passed role validation")

    return filtered_jobs

def get_common_job_roles() -> List[str]:
    """
    Get a list of common job roles related to data science, AI, and machine learning.

    Returns:
        List of common job roles
    """
    return [
        "Data Scientist",
        "Data Analyst",
        "Machine Learning Engineer",
        "AI Engineer",
        "Data Engineer",
        "Research Scientist",
        "Computer Vision Engineer",
        "NLP Engineer",
        "BI Developer",
        "BI Analyst",
        "ML Ops Engineer",
        "AI Researcher",
        "Statistician",
        "Data Architect",
        "Cloud Engineer",
        "DevOps Engineer",
        "Software Engineer",
        "Backend Engineer",
        "Full Stack Developer",
        "Python Developer",
        "Deep Learning Engineer",
        "AI Product Manager",
        "Data Science Manager",
        "ML Team Lead"
    ]
