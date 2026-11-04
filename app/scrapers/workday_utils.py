"""Shared helpers for Workday-backed scrapers.

Workday search results carry a relative ``postedOn`` label ("Posted Today",
"Posted 4 Days Ago", "Posted 30+ Days Ago") while the job page's JSON-LD
``datePosted`` is often the original requisition date, which can be much older.
Filtering only on the detail date silently drops jobs that Workday has just
re-posted, so the scrapers use the search result's age first and fall back to
the detail date when ``postedOn`` is missing.
"""
import re
from datetime import datetime, timedelta, timezone

from dateutil.parser import isoparse

_POSTED_RE = re.compile(r"(\d+)\+?\s+days?\s+ago", re.I)


def _utcnow():
    """Naive UTC now, matching parse_workday_date's output."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_workday_date(value):
    """Parse a Workday/JSON-LD date into a naive UTC datetime.

    Accepts date-only values ("2026-11-03"), ISO timestamps with or without a
    timezone, and ``Z`` suffixes. Returns ``None`` when the value is missing or
    not a date.
    """
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = isoparse(str(value))
        except (TypeError, ValueError):
            return None
    if parsed.tzinfo:
        parsed = parsed.astimezone(timezone.utc).replace(tzinfo=None)
    return parsed


def posted_age_days(posted_on):
    """Return the age in days from a Workday ``postedOn`` label, or None."""
    text = (posted_on or "").lower()
    if "today" in text:
        return 0
    if "yesterday" in text:
        return 1
    match = _POSTED_RE.search(text)
    if not match:
        return None
    # "30+ Days Ago" is a floor, so treat it as just over 30 days.
    return int(match.group(1)) + (1 if "+" in text else 0)


def workday_job_is_recent(job, days, detail_date=None):
    """Whether a Workday search result is inside the ``days`` window."""
    age = posted_age_days(job.get("postedOn"))
    if age is not None:
        return age <= days
    parsed = parse_workday_date(detail_date)
    if parsed is None:
        return False
    return parsed >= _utcnow() - timedelta(days=days)


def workday_posted_date(job):
    """Approximate posting date from ``postedOn`` when the detail date is missing."""
    age = posted_age_days(job.get("postedOn"))
    if age is None:
        return None
    return (_utcnow() - timedelta(days=age)).strftime("%Y-%m-%d")


def workday_effective_date(job, detail_date=None):
    """Most recent usable posting date for a Workday search result.

    Workday's detail ``datePosted`` can be the original requisition date while
    ``postedOn`` reflects a re-post. Using the later of the two keeps the stored
    date aligned with the recency filter and the dashboard's date-based views.
    """
    detail = parse_workday_date(detail_date)
    age = posted_age_days(job.get("postedOn"))
    posted = _utcnow() - timedelta(days=age) if age is not None else None
    if detail and posted:
        return max(detail, posted).strftime("%Y-%m-%d")
    if detail:
        return detail.strftime("%Y-%m-%d")
    return posted.strftime("%Y-%m-%d") if posted else None


def format_workday_date(value):
    """Format a Workday date as YYYY-MM-DD, or return None if unparseable."""
    parsed = parse_workday_date(value)
    return parsed.strftime("%Y-%m-%d") if parsed else None
