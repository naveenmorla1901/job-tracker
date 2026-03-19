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

# Role validation has been removed

# Dictionary to store scraper functions
scrapers = {}

# Simple pass-through decorator (role filtering removed)
def apply_role_filtering(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Just call the original function without any filtering
        return func(*args, **kwargs)

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
