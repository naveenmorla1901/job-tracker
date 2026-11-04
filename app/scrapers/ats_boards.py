"""
Shared fetchers for public job-board APIs that return a company's whole board
in one request (Ashby, Greenhouse). Unlike Workday there is no search endpoint,
so each searched role is matched against job titles here.

Not a scraper itself: there is no get_ats_boards_jobs, so the scheduler skips it.
"""
import re
from concurrent.futures import ThreadPoolExecutor
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


def _rippling_detail(board, posting):
    response = requests.get(
        f"https://ats.rippling.com/api/v1/board/{board}/jobs/{posting['uuid']}",
        headers=HEADERS, timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_rippling_jobs(board, roles, days=7):
    """Jobs from https://ats.rippling.com/<board>/jobs grouped by role."""
    response = requests.get(
        f"https://ats.rippling.com/api/v1/board/{board}/jobs",
        headers=HEADERS, timeout=30,
    )
    response.raise_for_status()
    postings = []
    seen = set()
    for posting in response.json():
        uuid = posting.get("uuid")
        if uuid and uuid not in seen:
            seen.add(uuid)
            postings.append(posting)

    details = []
    failures = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(_rippling_detail, board, p) for p in postings]
        for future in futures:
            try:
                details.append(future.result())
            except Exception as exc:
                # A single missing detail page should not hide the rest of the board.
                failures.append(exc)

    if postings and not details:
        reason = failures[0] if failures else "no postings"
        raise RuntimeError(f"Rippling board {board}: no job details could be fetched: {reason}")
    if failures:
        print(f"Error fetching {len(failures)} Rippling job detail(s) for {board}: {failures[0]}")

    jobs = []
    for detail in details:
        posted = _parse_iso(detail.get("createdOn"))
        description = detail.get("description") or {}
        locations = [loc for loc in (detail.get("workLocations") or []) if loc]
        jobs.append({
            "job_title": detail.get("name", "N/A"),
            "job_id": detail.get("uuid"),
            "location": ", ".join(locations) if locations else "N/A",
            "job_url": detail.get("url"),
            "date_posted": posted.strftime("%Y-%m-%d") if posted else None,
            "employment_type": (detail.get("employmentType") or {}).get("id") or "N/A",
            "description": _clean(" ".join(
                part for part in (description.get("company"), description.get("role")) if part
            )),
            "_posted": posted,
        })
    return _by_role(jobs, roles, days)


_GEM_URL = "https://jobs.gem.com/api/public/graphql"
_GEM_HEADERS = {
    **HEADERS,
    "Content-Type": "application/json",
    "Origin": "https://jobs.gem.com",
}
_GEM_LIST_QUERY = """
query JobBoardList($boardId: String!) {
  oatsExternalJobPostings(boardId: $boardId) {
    jobPostings {
      extId
      title
      locations { name }
      job { employmentType }
    }
  }
}
"""
_GEM_DETAIL_QUERY = """
query ExternalJobPosting($boardId: String!, $extId: String!) {
  oatsExternalJobPosting(boardId: $boardId, extId: $extId) {
    extId
    title
    firstPublishedTsSec
    startDateTs
    locations { name }
    job { employmentType requisitionId }
    descriptionHtml
  }
}
"""


def _gem_query(query, variables):
    response = requests.post(
        _GEM_URL,
        json={"query": query, "variables": variables},
        headers=_GEM_HEADERS, timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message", "Gem GraphQL error"))
    return payload.get("data") or {}


def _gem_detail(board, posting):
    data = _gem_query(_GEM_DETAIL_QUERY, {"boardId": board, "extId": posting["extId"]})
    return data.get("oatsExternalJobPosting") or {}


def _gem_posted(detail):
    timestamp = detail.get("firstPublishedTsSec") or detail.get("startDateTs")
    if isinstance(timestamp, (int, float)):
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)
    return _parse_iso(timestamp)


def fetch_gem_jobs(board, roles, days=7):
    """Jobs from https://jobs.gem.com/<board> grouped by role."""
    data = _gem_query(_GEM_LIST_QUERY, {"boardId": board})
    postings = (data.get("oatsExternalJobPostings") or {}).get("jobPostings") or []
    postings = [p for p in postings if p.get("extId")]

    details = []
    failures = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(_gem_detail, board, p) for p in postings]
        for future in futures:
            try:
                details.append(future.result())
            except Exception as exc:
                failures.append(exc)

    if postings and not details:
        reason = failures[0] if failures else "no postings"
        raise RuntimeError(f"Gem board {board}: no job details could be fetched: {reason}")
    if failures:
        print(f"Error fetching {len(failures)} Gem job detail(s) for {board}: {failures[0]}")

    jobs = []
    for detail in details:
        posted = _gem_posted(detail)
        locations = [loc.get("name") for loc in (detail.get("locations") or []) if loc.get("name")]
        jobs.append({
            "job_title": detail.get("title", "N/A"),
            "job_id": detail.get("extId"),
            "location": ", ".join(locations) if locations else "N/A",
            "job_url": f"https://jobs.gem.com/{board}/{detail.get('extId', '')}",
            "date_posted": posted.strftime("%Y-%m-%d") if posted else None,
            "employment_type": (detail.get("job") or {}).get("employmentType") or "N/A",
            "description": _clean(detail.get("descriptionHtml")),
            "_posted": posted,
        })
    return _by_role(jobs, roles, days)
