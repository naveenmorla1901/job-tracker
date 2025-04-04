"""
Utility functions for validating and processing job roles.
This module provides functions to ensure that only relevant roles are extracted from job listings.
"""
import re
import logging
from typing import List, Set, Dict, Any, Union

logger = logging.getLogger(__name__)

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
    "lead", "manager", "director", "head", "principal", "senior", "staff", "technical lead"
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
    
    # If the role contains numbers (like O9 Technical Architect), it's probably not a valid role
    if re.search(r'\d', normalized_role):
        # Unless it's specifically related to valid technology versions like Python 3, SQL Server 2019, etc.
        if not any(tech in normalized_role for tech in ["python", "java", "sql", "node", "react", "angular"]):
            # Check if it's explicitly requested
            if not any(normalize_role(input_role) in normalized_role for input_role in input_roles):
                return False
    
    # Check if the role contains any valid role keywords
    if any(keyword in normalized_role for keyword in VALID_ROLE_KEYWORDS):
        return True
    
    # Check if the role is similar to any of the input roles
    for input_role in input_roles:
        normalized_input = normalize_role(input_role)
        
        # Check for exact match
        if normalized_input == normalized_role:
            return True
        
        # Check if the normalized input role is contained in the normalized role
        if normalized_input in normalized_role:
            return True
        
        # Check for word overlap (at least one significant word in common)
        input_words = normalized_input.split()
        role_words = normalized_role.split()
        
        # Filter out common stop words
        stop_words = {"the", "a", "an", "and", "or", "in", "on", "at", "to", "for", "with", "by", "of"}
        input_words = [w for w in input_words if w not in stop_words]
        
        if any(word in role_words for word in input_words):
            return True
    
    return False

def filter_roles(job_data: Dict[str, Any], input_roles: List[str]) -> Dict[str, Any]:
    """
    Filter job data to only include valid roles.
    
    Args:
        job_data: Dictionary of job data with roles as keys
        input_roles: List of input roles used for the search
        
    Returns:
        Filtered job data with only valid roles
    """
    filtered_data = {}
    
    for role, jobs in job_data.items():
        normalized_role = normalize_role(role)
        
        if is_valid_role(normalized_role, input_roles):
            filtered_data[role] = jobs
        else:
            logger.info(f"Filtered out invalid role: {role}")
    
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
    # Check job title
    if "job_title" in job and job["job_title"]:
        if is_valid_role(job["job_title"], input_roles):
            return True
    
    # Check description (if available)
    if "description" in job and job["description"]:
        normalized_desc = normalize_role(job["description"])
        
        # Check if any input role is in the description
        for input_role in input_roles:
            normalized_input = normalize_role(input_role)
            if normalized_input in normalized_desc:
                return True
        
        # Check if any valid role keyword is in the description
        if any(keyword in normalized_desc for keyword in VALID_ROLE_KEYWORDS):
            return True
    
    # If we have explicit roles field
    if "roles" in job and job["roles"]:
        for role in job["roles"]:
            if is_valid_role(role, input_roles):
                return True
    
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
    return [job for job in jobs if validate_job_roles(job, input_roles)]

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
