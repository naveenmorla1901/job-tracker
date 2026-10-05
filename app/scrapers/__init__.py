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


def _install_http_retries():
    """Retry transient failures for every HTTPS request the scrapers make.

    Career sites (Workday especially) intermittently answer 429/500/502/503/504
    or time out on single job pages. Each scraper calls requests.get/post, which
    builds a fresh Session per call, so mounting a retrying adapter in
    Session.__init__ covers all of them without editing each module. Only
    https:// is mounted: the dashboard's http://localhost API calls are untouched.
    """
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    if getattr(requests.Session, "_scraper_retries_installed", False):
        return

    retry = Retry(
        total=3,
        connect=2,
        read=2,
        status=3,
        backoff_factor=1.5,  # waits 0s, 3s, 6s between attempts
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=None,  # Workday job searches are read-only POSTs
        respect_retry_after_header=True,
        raise_on_status=False,  # hand the final response back; raise_for_status still reports it
    )
    original_init = requests.Session.__init__

    def init_with_retries(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.mount("https://", HTTPAdapter(max_retries=retry))

    requests.Session.__init__ = init_with_retries
    requests.Session._scraper_retries_installed = True


_install_http_retries()

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
