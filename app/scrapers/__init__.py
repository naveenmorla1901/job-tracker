# Scrapers package initialization
import importlib
import os
import inspect
import logging
import sys

# Get environment
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
is_test = ENVIRONMENT == "test"

logger = logging.getLogger("app.scrapers")

# Dictionary to store scraper functions
scrapers = {}

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
                        scrapers[module_name] = func
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
except ImportError:
    pass
