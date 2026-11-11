"""Toyota Motor North America jobs.

Toyota's public careers site is a Phenom front end, but its postings still live
on Workday. The current tenant is toyota.wd503.myworkdayjobs.com/TMNA; the old
toyota.wd5.myworkdayjobs.com/TMNA_QR site in the original spreadsheet is dead.
"""
import concurrent.futures
import json

import requests
from bs4 import BeautifulSoup

from app.scrapers.ats_boards import _role_matcher, _search_phrase
from app.scrapers.workday_utils import (
    posted_age_days,
    workday_effective_date,
    workday_job_is_recent,
)

API_URL = "https://toyota.wd503.myworkdayjobs.com/wday/cxs/toyota/TMNA/jobs"
SITE_URL = "https://toyota.wd503.myworkdayjobs.com/en-US/TMNA"
REFERER = "https://toyota.wd503.myworkdayjobs.com/TMNA"
PAGE_SIZE = 20
# Workday ranks by relevance but also matches descriptions, so scan a couple of
# pages and keep only titles that actually contain the searched role's words.
# Title matches rank at the top; two pages leave room without multiplying the
# rate-limited Workday requests across all 22 role searches.
MAX_RESULTS = 40

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Referer": REFERER,
}


def get_toyota_jobs(roles, days=7):
    """Return Toyota Motor North America jobs posted in the last `days` days."""

    def fetch_role_jobs(target_role):
        search_text = _search_phrase(target_role) or target_role
        matches_title = _role_matcher(target_role)
        try:
            seen_ids = set()
            jobs_to_process = []
            offset = 0
            while offset < MAX_RESULTS:
                payload = {
                    "appliedFacets": {},
                    "searchText": search_text,
                    "limit": PAGE_SIZE,
                    "offset": offset,
                }
                response = requests.post(API_URL, json=payload, headers=HEADERS, timeout=30)
                response.raise_for_status()
                data = response.json()
                postings = data.get("jobPostings", [])
                if not postings:
                    break
                for job in postings:
                    job_id = extract_toyota_job_id(job)
                    if not job_id or job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)
                    if matches_title(job.get("title", "")):
                        jobs_to_process.append(job)
                offset += PAGE_SIZE
                if offset >= data.get("total", 0):
                    break

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = {
                    executor.submit(process_toyota_job, job, days): job
                    for job in jobs_to_process
                }
                results = []
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        results.append(result)

            return sorted(results, key=lambda item: item["date_posted"], reverse=True)

        except Exception as exc:
            print(f"Error fetching {target_role} jobs: {exc}")
            return []

    structured_results = {}
    for role in roles:
        structured_results[role] = fetch_role_jobs(role)
    return structured_results


def process_toyota_job(job, days):
    try:
        # Skip detail-page fetches for search results Workday already labels old.
        age = posted_age_days(job.get("postedOn"))
        if age is not None and age > days:
            return None

        job_url = f"{SITE_URL}{job.get('externalPath', '')}"
        metadata = get_toyota_job_details(job_url)
        if workday_job_is_recent(job, days, metadata.get("datePosted")):
            return format_toyota_job_data(job, metadata)
    except Exception as exc:
        print(f"Error processing job: {exc}")
    return None


def get_toyota_job_details(job_url):
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")

        for script in soup.find_all("script", {"type": "application/ld+json"}):
            try:
                data = json.loads(script.string or "{}")
            except json.JSONDecodeError:
                continue
            if isinstance(data, list):
                data = next((item for item in data if item.get("@type") == "JobPosting"), {})
            if data.get("@type") == "JobPosting":
                return {
                    "datePosted": data.get("datePosted"),
                    "employmentType": data.get("employmentType"),
                    "description": clean_toyota_description(data.get("description", "")),
                }

        return {
            "datePosted": (soup.find("meta", {"property": "og:article:published_time"}) or {}).get("content"),
            "employmentType": (soup.find("meta", {"name": "employmentType"}) or {}).get("content"),
            "description": (soup.find("meta", {"name": "description"}) or {}).get("content"),
        }
    except Exception as exc:
        print(f"Error fetching details: {exc}")
        return {}


def format_toyota_job_data(job, metadata):
    return {
        "job_title": job.get("title", "N/A"),
        "job_id": extract_toyota_job_id(job),
        "location": job.get("locationsText", "N/A"),
        "job_url": f"{SITE_URL}{job.get('externalPath', '')}",
        "date_posted": workday_effective_date(job, metadata.get("datePosted")) or "N/A",
        "employment_type": metadata.get("employmentType", "N/A"),
        "description": metadata.get("description", "N/A"),
    }


def extract_toyota_job_id(job):
    try:
        if job.get("bulletFields"):
            return job["bulletFields"][0]
        return job["externalPath"].split("_")[-1].split("/")[-1]
    except Exception:
        return "N/A"


def clean_toyota_description(description):
    if not description:
        return "N/A"
    cleaned = BeautifulSoup(description, "html.parser").get_text(separator=" ")
    return " ".join(cleaned.split()[:250]) + "..."
