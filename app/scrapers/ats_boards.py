"""
Shared fetchers for public job boards (Ashby, Greenhouse, Gem, Rippling,
SuccessFactors, TalentBrew). Each fetcher returns the project's common job
schema grouped by role.

Not a scraper itself: there is no get_ats_boards_jobs, so the scheduler skips it.
"""
import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from urllib.parse import quote, urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from dateutil.parser import isoparse

HEADERS = {
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}

HTML_HEADERS = {
    **HEADERS,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# Skill words the scheduler appends to role searches ("Data Scientist python SQL");
# they are not part of a job title. Only trailing ones are suffixes: "SQL
# Developer" keeps its SQL because the scheduler never appends there.
_NON_TITLE_WORDS = {"python", "sql", "visualization"}


def _search_phrase(role):
    """Drop trailing scheduler skill suffixes ("python SQL") from a role."""
    words = role.split()
    while len(words) > 1 and words[-1].lower() in _NON_TITLE_WORDS:
        words.pop()
    return " ".join(words)


def _role_matcher(role):
    """Return a predicate: every title-relevant word of the role appears in the title."""
    words = re.findall(r"[a-z0-9/]+", _search_phrase(role).lower())
    patterns = []
    for word in words:
        # "science" should also match "scientist"; "engineer" also "engineering"
        if word == "science":
            patterns.append(re.compile(r"\bscien"))
        elif word == "engineer":
            patterns.append(re.compile(r"\bengineer"))
        else:
            patterns.append(re.compile(rf"\b{re.escape(word)}\b"))
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


# --- SuccessFactors Career Site Builder -------------------------------------
# Boston Scientific left Workday for SAP SuccessFactors. Its public search page
# matches a quoted phrase against titles and descriptions; the job page carries
# the posting date in <meta itemprop="datePosted">. The RSS feed only returns
# the 20 newest matches and ignores the phrase, so it cannot drive date filtering.

_SF_PAGE_SIZE = 25
_SF_MAX_PAGES = 8
_SF_JOB_ID_RE = re.compile(r"/(\d+)/?$")


def _successfactors_date(value):
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _successfactors_search(search_url, role):
    """Return candidate job cards for one quoted-phrase search."""
    phrase = _search_phrase(role)
    if not phrase:
        return []
    candidates = []
    for page in range(_SF_MAX_PAGES):
        try:
            response = requests.get(
                search_url,
                params={"q": f'"{phrase}"', "startrow": page * _SF_PAGE_SIZE},
                headers=HTML_HEADERS,
                timeout=30,
            )
            response.raise_for_status()
        except Exception as exc:
            print(f"Error fetching {role} jobs: {exc}")
            break
        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table#searchresults tbody tr.data-row")
        for row in rows:
            link = row.select_one("a.jobTitle-link")
            if not link:
                continue
            href = link.get("href") or ""
            match = _SF_JOB_ID_RE.search(urlparse(href).path)
            if not match:
                continue
            location_el = row.select_one("td.colLocation span.jobLocation")
            candidates.append({
                "job_title": link.get_text(" ", strip=True),
                "job_id": match.group(1),
                "location": location_el.get_text(" ", strip=True) if location_el else "N/A",
                "job_url": urljoin(search_url, href),
            })
        if len(rows) < _SF_PAGE_SIZE:
            break
    return candidates


def _successfactors_detail(job_url):
    response = requests.get(job_url, headers=HTML_HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    date_meta = soup.find("meta", {"itemprop": "datePosted"})
    description_el = soup.select_one("div.jobDisplay div.content")
    return {
        "posted": _successfactors_date(date_meta.get("content") if date_meta else None),
        "description": _clean(description_el.get_text(" ", strip=True)) if description_el else "N/A",
    }


def fetch_successfactors_jobs(search_url, roles, days=7):
    """Jobs from a SuccessFactors Career Site Builder site, grouped by role."""
    candidates = {}
    for role in roles:
        for job in _successfactors_search(search_url, role):
            candidates.setdefault(job["job_id"], job)

    matchers = [_role_matcher(role) for role in roles]
    matched = [
        job for job in candidates.values()
        if any(matcher(job["job_title"]) for matcher in matchers)
    ]

    jobs = []
    failures = []
    if matched:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(_successfactors_detail, job["job_url"]): job
                for job in matched
            }
            for future in as_completed(futures):
                job = futures[future]
                try:
                    detail = future.result()
                except Exception as exc:
                    failures.append(exc)
                    continue
                jobs.append({
                    **job,
                    "date_posted": detail["posted"].strftime("%Y-%m-%d") if detail["posted"] else None,
                    "employment_type": "N/A",
                    "description": detail["description"],
                    "_posted": detail["posted"],
                })
    if failures:
        print(f"Error fetching {len(failures)} job detail(s): {failures[0]}")
    return _by_role(jobs, roles, days)


# --- TalentBrew / Radancy ----------------------------------------------------
# Synopsys' career site runs on TalentBrew. Its search results module exposes
# the same HTML the page renders through an AJAX endpoint, which can return 100
# rows at once instead of the 15 the page shows.

_TB_DATE_RE = re.compile(r"(\d{1,2}/\d{1,2}/\d{4})")
_TB_PAGE_SIZE = 100
_TB_MAX_PAGES = 2


def _talentbrew_detail(job_url):
    response = requests.get(job_url, headers=HTML_HEADERS, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "{}")
        except (TypeError, ValueError):
            continue
        if isinstance(data, list):
            data = next((item for item in data if item.get("@type") == "JobPosting"), {})
        if data.get("@type") == "JobPosting":
            return {
                "datePosted": data.get("datePosted"),
                "employmentType": data.get("employmentType"),
                "description": _clean(data.get("description")),
            }
    return {}


def _talentbrew_page(base_url, role, page):
    keyword = _search_phrase(role) or role
    response = requests.get(
        f"{base_url}/search-jobs/results",
        params={
            "ActiveFacetID": "0",
            "CurrentPage": str(page),
            "RecordsPerPage": str(_TB_PAGE_SIZE),
            "SearchResultsModuleName": "Search Results",
            "SearchFiltersModuleName": "Search Filters",
            "SortCriteria": "0",
            "SortDirection": "1",
            "SearchType": "1",
            "SearchResultType": "0",
            "Keywords": keyword,
        },
        headers={
            **HEADERS,
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"{base_url}/search-jobs?k={quote(keyword)}",
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return BeautifulSoup(payload.get("results") or "", "html.parser")


def fetch_talentbrew_jobs(base_url, roles, days=7):
    """Jobs from a TalentBrew site's search results, grouped by role."""
    jobs = []
    seen = set()
    for role in roles:
        for page in range(1, _TB_MAX_PAGES + 1):
            try:
                soup = _talentbrew_page(base_url, role, page)
            except Exception as exc:
                print(f"Error fetching {role} jobs: {exc}")
                break
            items = soup.select("li.search-results-list__list-item")
            if not items:
                break
            for item in items:
                link = item.select_one("a.sr-job-link")
                if not link:
                    continue
                href = link.get("href") or ""
                job_id = link.get("data-job-id") or ""
                if not href or not job_id or job_id in seen:
                    continue
                title_el = link.select_one("h2")
                title = title_el.get_text(" ", strip=True) if title_el else ""
                if not title:
                    continue
                seen.add(job_id)
                location_el = item.select_one("span.job-location")
                location = location_el.get_text(" ", strip=True) if location_el else "N/A"
                date_el = item.select_one("span.job-date-posted")
                date_text = date_el.get_text(" ", strip=True) if date_el else ""
                date_match = _TB_DATE_RE.search(date_text)
                posted = None
                if date_match:
                    try:
                        posted = datetime.strptime(date_match.group(1), "%m/%d/%Y").replace(
                            tzinfo=timezone.utc
                        )
                    except ValueError:
                        posted = None
                jobs.append({
                    "job_title": title,
                    "job_id": job_id,
                    "location": location,
                    "job_url": urljoin(base_url, href),
                    "date_posted": posted.strftime("%Y-%m-%d") if posted else None,
                    "employment_type": "N/A",
                    "description": "N/A",
                    "_posted": posted,
                })
            if len(items) < _TB_PAGE_SIZE:
                break

    # Fetch descriptions only for recent jobs that actually match a role.
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    matchers = [_role_matcher(role) for role in roles]
    detail_jobs = [
        job for job in jobs
        if job["_posted"] and job["_posted"] >= cutoff
        and any(matcher(job["job_title"]) for matcher in matchers)
    ]
    if detail_jobs:
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(_talentbrew_detail, job["job_url"]): job
                for job in detail_jobs
            }
            for future in as_completed(futures):
                job = futures[future]
                try:
                    detail = future.result()
                except Exception:
                    detail = {}
                if detail:
                    job["description"] = detail.get("description") or "N/A"
                    job["employment_type"] = detail.get("employmentType") or "N/A"
    return _by_role(jobs, roles, days)
