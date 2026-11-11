"""Date-window filtering shared by the scheduler.

Most scrapers compare a date-only ``datePosted`` against ``datetime.now() -
days``. A job posted exactly ``days`` ago parses to midnight, which is earlier
than the current clock time, so the scraper silently drops it. The scheduler
therefore asks scrapers for one extra day and trims the result by calendar date.
"""
from datetime import date, datetime, timedelta, timezone


def parse_posted_date(value):
    """Parse a scraper's ``date_posted`` value into a date, or None."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if not text or text.upper() == "N/A":
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def filter_jobs_to_window(jobs_data, days_back, now=None):
    """Keep jobs posted on or after the first day of the ``days_back`` window.

    Jobs without a parseable date are kept: a missing date should not hide a
    posting, and the scraper already decided it was recent enough to return.
    """
    today = (now or datetime.now(timezone.utc)).date()
    cutoff = today - timedelta(days=days_back)
    filtered = {}
    for role, jobs in (jobs_data or {}).items():
        kept = []
        for job in jobs or []:
            posted = parse_posted_date(job.get("date_posted"))
            if posted is None or posted >= cutoff:
                kept.append(job)
        filtered[role] = kept
    return filtered
