"""Shared helpers for Workday-backed scrapers.

Workday search results carry a relative ``postedOn`` label ("Posted Today",
"Posted 4 Days Ago", "Posted 30+ Days Ago") while the job page's JSON-LD
``datePosted`` is often the original requisition date, which can be much older.
Filtering only on the detail date silently drops jobs that Workday has just
re-posted, so the scrapers use the search result's age first and fall back to
the detail date when ``postedOn`` is missing.
"""
import json
import re
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup
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


_WORKDAY_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}


def _workday_job_id(posting):
    path = posting.get("externalPath") or ""
    if "_" in path:
        return path.rsplit("_", 1)[-1].split("/")[0]
    tail = path.rstrip("/").split("/")[-1]
    if tail:
        return tail
    fields = posting.get("bulletFields") or []
    return fields[0] if fields else None


def _workday_detail(job_url):
    try:
        response = requests.get(job_url, timeout=30)
        response.raise_for_status()
    except Exception as exc:
        print(f"Error fetching Workday detail {job_url}: {exc}")
        return {}
    soup = BeautifulSoup(response.text, "html.parser")
    script = soup.find("script", {"type": "application/ld+json"})
    if script:
        try:
            data = json.loads(script.string or "{}")
            return {
                "datePosted": data.get("datePosted"),
                "employmentType": data.get("employmentType"),
                "description": " ".join(
                    BeautifulSoup(
                        data.get("description") or "", "html.parser"
                    ).get_text(separator=" ").split()[:250]
                ),
            }
        except (TypeError, ValueError):
            pass
    return {}


def fetch_workday_board_jobs(api_url, base_url, roles, days=7, page_limit=20):
    """Jobs from a Workday CXS board, grouped by role.

    Workday's search result carries a relative ``postedOn`` label. Postings
    already older than the window are dropped before their detail page is
    fetched; postings without a label fall back to the detail date.
    """
    role_jobs = {}
    details = {}
    for role in roles:
        try:
            response = requests.post(
                api_url,
                json={
                    "appliedFacets": {},
                    "searchText": role,
                    "limit": page_limit,
                    "offset": 0,
                },
                headers={**_WORKDAY_HEADERS, "Referer": base_url},
                timeout=30,
            )
            response.raise_for_status()
            postings = response.json().get("jobPostings", [])
        except Exception as exc:
            print(f"Error fetching {role} jobs: {exc}")
            role_jobs[role] = []
            continue

        jobs = []
        for posting in postings:
            job_id = _workday_job_id(posting)
            if not job_id:
                continue
            age = posted_age_days(posting.get("postedOn"))
            if age is not None and age > days:
                continue
            job_url = base_url + (posting.get("externalPath") or "")
            if job_id not in details:
                details[job_id] = _workday_detail(job_url)
            detail = details[job_id]
            if age is None and not workday_job_is_recent(
                posting, days, detail.get("datePosted")
            ):
                continue
            jobs.append({
                "job_title": posting.get("title", "N/A"),
                "job_id": job_id,
                "location": posting.get("locationsText", "N/A"),
                "job_url": job_url,
                "date_posted": workday_effective_date(
                    posting, detail.get("datePosted")
                ) or "N/A",
                "employment_type": detail.get("employmentType") or "N/A",
                "description": detail.get("description") or "N/A",
            })
        role_jobs[role] = jobs
    return role_jobs
