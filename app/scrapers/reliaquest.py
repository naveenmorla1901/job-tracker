import concurrent.futures
import json

import requests
from bs4 import BeautifulSoup

from app.scrapers.workday_utils import (
    format_workday_date,
    parse_workday_date,
    workday_effective_date,
    workday_job_is_recent,
)

BASE_URL = "https://reliaquest.wd5.myworkdayjobs.com"
BOARD = "ReliaQuest_Careers"


def get_reliaquest_jobs(roles, days=40):
    """Main function to retrieve ReliaQuest jobs structured by roles"""

    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        search_url = f"{BASE_URL}/wday/cxs/reliaquest/{BOARD}/jobs"

        payload = {
            "appliedFacets": {},
            "searchText": target_role,
            "limit": 20,
            "offset": 0
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": f"{BASE_URL}/{BOARD}"
        }

        try:
            response = requests.post(search_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            seen_ids = set()
            jobs_to_process = []

            for job in data.get('jobPostings', []):
                job_id = extract_reliaquest_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_reliaquest_job, job, days): job
                    for job in jobs_to_process
                }

                results = []
                for future in concurrent.futures.as_completed(future_to_job):
                    result = future.result()
                    if result:
                        results.append(result)

            return sorted(results, key=lambda x: x['date_posted'], reverse=True)

        except Exception as e:
            print(f"Error fetching {target_role} jobs: {str(e)}")
            return []

    # Structure results by role
    structured_results = {}
    for role in roles:
        structured_results[role] = fetch_role_jobs(role)

    return structured_results


def process_reliaquest_job(job, days):
    try:
        job_url = f"{BASE_URL}/en-US/{BOARD}{job.get('externalPath', '')}"
        metadata = get_reliaquest_details(job_url)

        if workday_job_is_recent(job, days, metadata.get('datePosted')):
            return format_reliaquest_data(job, metadata)

    except Exception as e:
        print(f"Error processing job: {str(e)}")
    return None


def get_reliaquest_details(job_url):
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        script = soup.find('script', {'type': 'application/ld+json'})
        if script:
            try:
                data = json.loads(script.string)
                return {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': clean_reliaquest_desc(data.get('description', ''))
                }
            except json.JSONDecodeError:
                pass

        return {
            'datePosted': (soup.find('meta', {'property': 'og:article:published_time'}) or {}).get('content'),
            'employmentType': (soup.find('meta', {'name': 'employmentType'}) or {}).get('content'),
            'description': (soup.find('meta', {'name': 'description'}) or {}).get('content')
        }

    except Exception as e:
        print(f"Error fetching details: {str(e)}")
        return {}


def format_reliaquest_data(job, metadata):
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_reliaquest_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"{BASE_URL}/en-US/{BOARD}{job.get('externalPath', '')}",
        "date_posted": workday_effective_date(job, metadata.get('datePosted')) or 'N/A',
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }


def extract_reliaquest_id(job):
    try:
        bullet = (job.get('bulletFields') or [None])[0]
        if bullet:
            return bullet
        return job['externalPath'].split('/')[-1].split('_')[-1]
    except Exception:
        return 'N/A'


def parse_reliaquest_date(date_str):
    return parse_workday_date(date_str)


def format_reliaquest_date(date_str):
    return format_workday_date(date_str) or date_str


def clean_reliaquest_desc(desc):
    return ' '.join(BeautifulSoup(desc, 'html.parser').get_text().split()[:150]) + '...'
