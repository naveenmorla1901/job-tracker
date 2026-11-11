import requests
from bs4 import BeautifulSoup
import json
import concurrent.futures

from app.scrapers.workday_utils import (
    workday_effective_date,
    workday_job_is_recent,
)

_UNAVAILABLE_STATUSES = {422, 500, 502, 503, 504, 520}


def get_nxp_jobs(roles, days=7):
    """Main function to retrieve NXP Semiconductors jobs structured by roles"""
    outage_status = {"code": None}

    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://nxp.wd3.myworkdayjobs.com/wday/cxs/nxp/careers/jobs"

        payload = {
            "appliedFacets": {
                "Location_Country": ["bc33aa3152ec42d4995f4791a106ed09"]
            },
            "searchText": target_role,
            "limit": 20,
            "offset": 0
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://nxp.wd3.myworkdayjobs.com/careers"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers, timeout=30)
            if response.status_code in _UNAVAILABLE_STATUSES:
                outage_status["code"] = response.status_code
                return []
            response.raise_for_status()
            data = response.json()

            seen_ids = set()
            jobs_to_process = []

            for job in data.get('jobPostings', []):
                job_id = extract_nxp_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_nxp_job, job, days): job
                    for job in jobs_to_process
                }

                results = []
                for future in concurrent.futures.as_completed(future_to_job):
                    result = future.result()
                    if result:
                        results.append(result)

            return sorted(results, key=lambda x: x['date_posted'], reverse=True)

        except requests.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status in _UNAVAILABLE_STATUSES:
                outage_status["code"] = status
                return []
            print(f"Error fetching {target_role} jobs: {str(e)}")
            return []
        except Exception as e:
            print(f"Error fetching {target_role} jobs: {str(e)}")
            return []

    # Structure results by role
    structured_results = {}
    for role in roles:
        structured_results[role] = fetch_role_jobs(role)

    if outage_status["code"] and not any(structured_results.values()):
        print(
            "SCRAPER_UNAVAILABLE: NXP Workday returned HTTP "
            f"{outage_status['code']} (maintenance page); will retry next cycle."
        )

    return structured_results


def process_nxp_job(job, days):
    try:
        job_url = f"https://nxp.wd3.myworkdayjobs.com/en-US/careers{job.get('externalPath', '')}"
        metadata = get_nxp_job_details(job_url)

        if workday_job_is_recent(job, days, metadata.get('datePosted')):
            return format_nxp_job_data(job, metadata)

    except Exception as e:
        print(f"Error processing job: {str(e)}")
    return None

def get_nxp_job_details(job_url):
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        response.encoding = 'utf-8'  # Workday serves UTF-8 without a charset header
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract from JSON-LD
        script = soup.find('script', {'type': 'application/ld+json'})
        if script:
            try:
                data = json.loads(script.string)
                return {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': clean_nxp_description(data.get('description', ''))
                }
            except json.JSONDecodeError:
                pass

        # Fallback to meta tags
        return {
            'datePosted': (soup.find('meta', {'property': 'og:article:published_time'}) or {}).get('content'),
            'employmentType': (soup.find('meta', {'name': 'employmentType'}) or {}).get('content'),
            'description': (soup.find('meta', {'name': 'description'}) or {}).get('content')
        }

    except Exception as e:
        print(f"Error fetching details: {str(e)}")
        return {}

def format_nxp_job_data(job, metadata):
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_nxp_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"https://nxp.wd3.myworkdayjobs.com/en-US/careers{job.get('externalPath', '')}",
        "date_posted": workday_effective_date(job, metadata.get('datePosted')) or 'N/A',
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }

def extract_nxp_job_id(job):
    try:
        path = job.get('externalPath', '')
        if '_' in path:
            return path.split('_')[-1].split('/')[0]
        return path.split('/')[-1]
    except:
        return job.get('bulletFields', ['N/A'])[0]

def clean_nxp_description(desc):
    if not desc:
        return 'N/A'
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    return ' '.join(cleaned.split()[:250]) + '...'

# Example usage:
# if __name__ == "__main__":
#     jobs_data = get_nxp_jobs(roles=["Data Scientist", "Machine Learning Engineer"], days=7)
#     print(json.dumps(jobs_data, indent=2, ensure_ascii=False))
