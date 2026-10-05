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


# --- Workday request budget -------------------------------------------------
# Workday serves every tenant from shared hosts (wd1, wd5, ...) and rate-limits by
# client IP across all of them, so a parallel cycle must budget Workday traffic as
# a whole. Inside a scheduled scraper run (begin_scraper_run) the adapter below:
#   * fetches each Workday job page once: the same job comes back for many of the
#     22 role searches and every scraper re-downloads it just to read datePosted;
#   * skips pages the search results already show as older than the run's window
#     ("Posted 30+ Days Ago"), answering with a stand-in page whose JSON-LD
#     datePosted carries that age, so the scraper drops the job exactly as it would
#     with the real page (all Workday scrapers read datePosted from JSON-LD);
#   * holds one of a few cross-process slots per Workday request (set_workday_slots).
_WORKDAY_HOSTS = ("myworkdayjobs.com", "myworkdaysite.com")
_POSTED_RE = None
_run_state = {"active": False, "days": None, "pages": {}, "posted": {}}
_workday_slots = None


def set_workday_slots(semaphore):
    """Pool initializer: share one semaphore that caps concurrent Workday requests."""
    global _workday_slots
    _workday_slots = semaphore


def begin_scraper_run(days_back):
    """Start a scraper run: fresh page cache, and skip pages older than days_back."""
    _run_state.update(active=True, days=days_back, pages={}, posted={})


def end_scraper_run():
    _run_state.update(active=False, days=None, pages={}, posted={})


def _posted_age_days(posted_on):
    """'Posted Today' -> 0, 'Posted Yesterday' -> 1, 'Posted 5 Days Ago' -> 5, '30+' -> 31."""
    global _POSTED_RE
    import re
    if _POSTED_RE is None:
        _POSTED_RE = re.compile(r"(\d+)\+?\s+days?\s+ago", re.I)
    text = (posted_on or "").lower()
    if "today" in text:
        return 0
    if "yesterday" in text:
        return 1
    match = _POSTED_RE.search(text)
    if not match:
        return None
    return int(match.group(1)) + (1 if "+" in text else 0)


def _job_key(url):
    """(host, '/job/...') for a Workday job page or search result path."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    path = parsed.path
    index = path.find("/job/")
    return (parsed.hostname, path[index:]) if index >= 0 else None


def _install_http_retries():
    """Retry transient failures for every HTTPS request the scrapers make.

    Career sites (Workday especially) intermittently answer 429/500/502/503/504
    or time out on single job pages. Each scraper calls requests.get/post, which
    builds a fresh Session per call, so mounting the adapter in Session.__init__
    covers all of them without editing each module. Only https:// is mounted: the
    dashboard's http://localhost API calls are untouched.
    """
    import copy
    import json
    from datetime import datetime, timedelta

    import requests
    from requests.adapters import HTTPAdapter
    from urllib.parse import urlparse
    from urllib3.util.retry import Retry

    if getattr(requests.Session, "_scraper_retries_installed", False):
        return

    retry = Retry(
        total=4,
        connect=2,
        read=2,
        status=4,
        backoff_factor=2,  # waits 0s, 4s, 8s, 16s between attempts
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=None,  # Workday job searches are read-only POSTs
        respect_retry_after_header=True,
        raise_on_status=False,  # hand the final response back; raise_for_status still reports it
    )

    def stand_in_page(request, age_days):
        posted = (datetime.utcnow() - timedelta(days=age_days)).strftime("%Y-%m-%d")
        body = (
            '<html><head><script type="application/ld+json">'
            + json.dumps({"@type": "JobPosting", "datePosted": posted, "description": ""})
            + f'</script><meta property="og:article:published_time" content="{posted}"></head></html>'
        )
        response = requests.Response()
        response.status_code = 200
        response._content = body.encode("utf-8")
        response.headers["Content-Type"] = "text/html; charset=utf-8"
        response.encoding = "utf-8"
        response.url = request.url
        response.request = request
        return response

    class ScraperAdapter(HTTPAdapter):
        def send(self, request, **kwargs):
            host = urlparse(request.url).hostname or ""
            workday = host.endswith(_WORKDAY_HOSTS)
            in_run = _run_state["active"]
            is_page = workday and request.method == "GET" and "/job/" in request.url

            if is_page and in_run:
                cached = _run_state["pages"].get(request.url)
                if cached is not None:
                    response = copy.copy(cached)
                    response.request = request
                    return response
                age = _run_state["posted"].get(_job_key(request.url))
                if age is not None and _run_state["days"] is not None and age > _run_state["days"] + 1:
                    return stand_in_page(request, age)

            slots = _workday_slots if workday else None
            if slots is not None:
                slots.acquire()
            try:
                response = super().send(request, **kwargs)
            finally:
                if slots is not None:
                    slots.release()

            if workday and in_run and response.status_code == 200:
                if is_page:
                    response.content  # read the body now so the cached copy keeps it
                    _run_state["pages"][request.url] = response
                elif request.method == "POST" and "/wday/cxs/" in request.url:
                    try:
                        for posting in response.json().get("jobPostings", []):
                            key = _job_key(f"https://{host}{posting.get('externalPath', '')}")
                            age = _posted_age_days(posting.get("postedOn"))
                            if key and age is not None:
                                _run_state["posted"][key] = age
                    except ValueError:
                        pass
            return response

    original_init = requests.Session.__init__

    def init_with_retries(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.mount("https://", ScraperAdapter(max_retries=retry))

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
