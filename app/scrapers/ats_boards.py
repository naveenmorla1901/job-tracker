"""
Shared fetchers for public job-board APIs that return a company's whole board
in one request (Ashby, Greenhouse). Unlike Workday there is no search endpoint,
so each searched role is matched against job titles here.

Not a scraper itself: there is no get_ats_boards_jobs, so the scheduler skips it.
"""
import re
from datetime import datetime, timedelta, timezone

import requests
from bs4 import BeautifulSoup
from dateutil.parser import isoparse

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}

# Skill words the scheduler appends to role searches ("Data Scientist python SQL");
# they are not part of a job title.
_NON_TITLE_WORDS = {"python", "sql", "visualization"}


def _role_matcher(role):
    """Return a predicate: every title-relevant word of the role appears in the title."""
    words = [w for w in re.findall(r"[a-z0-9/]+", role.lower()) if w not in _NON_TITLE_WORDS]
    # "science" should also match "scientist"
    patterns = [re.compile(r"\bscien" if w == "science" else rf"\b{re.escape(w)}\b") for w in words]
    return lambda title: bool(patterns) and all(p.search(title.lower()) for p in patterns)


def _parse_iso(value):
    # isoparse, not datetime.fromisoformat: on Python 3.8 (the server) the latter
    # rejects "Z" and fractional seconds that aren't 3 or 6 digits
    try:
        parsed = isoparse(value)
    except (TypeError, ValueError):
        return None
    return parsed.astimezone(timezone.utc) if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _clean(html_or_text, words=250):
    text = BeautifulSoup(html_or_text or "", "html.parser").get_text(separator=" ")
    tokens = text.split()
    return " ".join(tokens[:words]) + ("..." if len(tokens) > words else "") if tokens else "N/A"


def _by_role(jobs, roles, days):
    """Group normalised jobs by matching role, keeping those posted within `days`."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    recent = [j for j in jobs if j["_posted"] and j["_posted"] >= cutoff]
    results = {}
    for role in roles:
        matches = _role_matcher(role)
        results[role] = [
            {k: v for k, v in j.items() if k != "_posted"}
            for j in recent if matches(j["job_title"])
        ]
    return results


def fetch_ashby_jobs(board, roles, days=7):
    """Jobs from https://jobs.ashbyhq.com/<board> grouped by role."""
    response = requests.get(
        f"https://api.ashbyhq.com/posting-api/job-board/{board}", headers=HEADERS, timeout=30
    )
    response.raise_for_status()
    jobs = []
    for job in response.json().get("jobs", []):
        if not job.get("isListed", True):
            continue
        posted = _parse_iso(job.get("publishedAt"))
        jobs.append({
            "job_title": job.get("title", "N/A"),
            "job_id": job.get("id"),
            "location": job.get("location", "N/A"),
            "job_url": job.get("jobUrl"),
            "date_posted": posted.strftime("%Y-%m-%d") if posted else None,
            "employment_type": job.get("employmentType", "N/A"),
            "description": _clean(job.get("descriptionPlain")),
            "_posted": posted,
        })
    return _by_role(jobs, roles, days)


def fetch_greenhouse_jobs(board, roles, days=7):
    """Jobs from https://job-boards.greenhouse.io/<board> grouped by role."""
    response = requests.get(
        f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs",
        params={"content": "true"}, headers=HEADERS, timeout=30,
    )
    response.raise_for_status()
    jobs = []
    for job in response.json().get("jobs", []):
        posted = _parse_iso(job.get("first_published") or job.get("updated_at"))
        jobs.append({
            "job_title": job.get("title", "N/A"),
            "job_id": str(job.get("id")),
            "location": (job.get("location") or {}).get("name", "N/A"),
            "job_url": job.get("absolute_url"),
            "date_posted": posted.strftime("%Y-%m-%d") if posted else None,
            "employment_type": "N/A",
            "description": _clean(BeautifulSoup(job.get("content") or "", "html.parser").get_text()),
            "_posted": posted,
        })
    return _by_role(jobs, roles, days)
