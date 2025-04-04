# Scrapers package initialization
import importlib
import os
import inspect
import logging
import sys
from functools import wraps

# Get environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
is_test = ENVIRONMENT == "test"

logger = logging.getLogger("app.scrapers")

# Import role validation utilities
try:
    from app.scrapers.role_utils import filter_jobs_by_role, filter_roles
except ImportError as e:
    logger.error(f"Error importing role utilities: {e}")
    # Define dummy functions to prevent errors
    def filter_jobs_by_role(jobs, input_roles):
        return jobs
    
    def filter_roles(job_data, input_roles):
        return job_data

# Dictionary to store scraper functions
scrapers = {}

# Create a decorator to apply role filtering to all scrapers
def apply_role_filtering(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        input_roles = kwargs.get('roles', [])
        if not input_roles and args:
            input_roles = args[0]  # Assume first positional argument is roles
        
        # Call the original function
        job_data = func(*args, **kwargs)
        
        # Filter the results to only include relevant roles
        if job_data and input_roles:
            try:
                # Apply role filtering
                filtered_data = filter_roles(job_data, input_roles)
                
                # For each role, filter the jobs to only include relevant ones
                for role, jobs in filtered_data.items():
                    filtered_data[role] = filter_jobs_by_role(jobs, input_roles)
                
                logger.info(f"Applied role filtering to scraper results: {len(job_data)} -> {len(filtered_data)} roles")
                return filtered_data
            except Exception as e:
                logger.error(f"Error applying role filtering: {e}")
        
        # If filtering failed or no input roles, return original data
        return job_data
    
    return wrapper

# Only load scrapers in non-test environment or when explicitly requested
if not is_test or 'pytest' not in sys.modules:
    # Get all Python files in the scrapers directory
    scraper_dir = os.path.dirname(__file__)
    for filename in os.listdir(scraper_dir):
        if filename.endswith(".py") and filename != "__init__.py" and filename != "base.py":
            module_name = filename[:-3]  # Remove '.py' extension
            
            try:
                # Import the module
                module = importlib.import_module(f"app.scrapers.{module_name}")
                
                # Look for get_*_jobs functions
                for name, func in inspect.getmembers(module, inspect.isfunction):
                    if name == f"get_{module_name}_jobs":
                        # Apply role filtering to the scraper function
                        decorated_func = apply_role_filtering(func)
                        scrapers[module_name] = decorated_func
                        logger.info(f"Found scraper: {module_name}")
                        
            except ImportError as e:
                logger.error(f"Error importing scraper {module_name}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error with scraper {module_name}: {e}")

# Function to get all available scrapers
def get_all_scrapers():
    """Returns a dictionary of all available scrapers with their names as keys"""
    return scrapers

# Export specific scrapers for backward compatibility
try:
    from app.scrapers.salesforce import get_salesforce_jobs
    # Apply role filtering to the export as well
    get_salesforce_jobs = apply_role_filtering(get_salesforce_jobs)
except ImportError:
    pass
