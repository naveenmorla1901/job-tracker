import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_assurant_jobs(roles, days=7):
    """
    Fetches jobs for each role in the provided roles list posted in the last `days` days.
    Returns a dictionary where keys are role names and values are lists of job dicts.
    """
    aggregated_jobs = {}
    for role in roles:
        aggregated_jobs[role] = fetch_assurant_jobs(role, days)
    return aggregated_jobs

def fetch_assurant_jobs(target_role, days=7):
    base_url = "https://assurant.wd1.myworkdayjobs.com/wday/cxs/assurant/Assurant_Careers/jobs"
    payload = {
        "appliedFacets": {},
        "searchText": target_role,
        "limit": 20,
        "offset": 0
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36"),
        "Referer": "https://assurant.wd1.myworkdayjobs.com/Assurant_Careers"
    }

    try:
        response = requests.post(base_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        seen_ids = set()
        jobs_to_process = []
        cutoff_date = datetime.now() - timedelta(days=days)

        for job in data.get('jobPostings', []):
            job_id = extract_assurant_job_id(job)
            if job_id and job_id not in seen_ids:
                seen_ids.add(job_id)
                jobs_to_process.append(job)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_job = {
                executor.submit(process_assurant_job, job, cutoff_date): job
                for job in jobs_to_process
            }
            results = []
            for future in concurrent.futures.as_completed(future_to_job):
                result = future.result()
                if result:
                    results.append(result)

        sorted_results = sorted(results, key=lambda x: x['date_posted'], reverse=True)
        return sorted_results

    except Exception as e:
        print(f"Error fetching Assurant jobs for role '{target_role}': {str(e)}")
        return []

def process_assurant_job(job, cutoff_date):
    try:
        job_url = f"https://assurant.wd1.myworkdayjobs.com/en-US/Assurant_Careers{job.get('externalPath', '')}"
        metadata = get_assurant_job_details(job_url)

        if not metadata.get('datePosted'):
            return None

        post_date = parse_assurant_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_assurant_job_data(job, metadata)

    except Exception as e:
        print(f"Error processing Assurant job: {str(e)}")
    return None

def get_assurant_job_details(job_url):
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Try extracting JSON-LD data
        script = soup.find('script', {'type': 'application/ld+json'})
        if script:
            try:
                data = json.loads(script.string)
                return {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': clean_assurant_description(data.get('description', ''))
                }
            except json.JSONDecodeError:
                pass

        # Fallback to meta tags if JSON-LD is unavailable
        return {
            'datePosted': (soup.find('meta', {'property': 'og:article:published_time'}) or {}).get('content'),
            'employmentType': (soup.find('meta', {'name': 'employmentType'}) or {}).get('content'),
            'description': (soup.find('meta', {'name': 'description'}) or {}).get('content')
        }

    except Exception as e:
        print(f"Error fetching Assurant details from {job_url}: {str(e)}")
        return {}

def format_assurant_job_data(job, metadata):
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_assurant_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"https://assurant.wd1.myworkdayjobs.com/en-US/Assurant_Careers{job.get('externalPath', '')}",
        "date_posted": format_assurant_date(metadata['datePosted']),
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }

def extract_assurant_job_id(job):
    try:
        path_parts = job['externalPath'].split('/')
        return next(part for part in reversed(path_parts) if part.startswith('R'))
    except Exception:
        return job.get('bulletFields', ['N/A'])[0]

def parse_assurant_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    except Exception:
        try:
            return datetime.fromisoformat(date_str.replace('Z', ''))
        except Exception:
            return None

def format_assurant_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
    except Exception:
        return date_str

def clean_assurant_description(desc):
    if not desc:
        return 'N/A'
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    return ' '.join(cleaned.split()[:200]) + '...'

# Example usage:
# if __name__ == "__main__":
#     assurant_roles = [
#         "Data Analyst",
#         "Actuarial Analyst"
#     ]
#     jobs_data = get_assurant_jobs(roles=assurant_roles, days=7)
#     print(json.dumps(jobs_data, indent=2, ensure_ascii=False))
