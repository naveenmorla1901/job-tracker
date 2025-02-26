import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_gartner_jobs(roles, days=7):
    """
    For each role in the roles list, fetch jobs posted in the last `days` days.
    Returns a dictionary where keys are role names and values are lists of job dictionaries.
    """
    aggregated_jobs = {}
    for role in roles:
        aggregated_jobs[role] = fetch_gartner_jobs(role, days)
    return aggregated_jobs

def fetch_gartner_jobs(target_role, days=7):
    base_url = "https://gartner.wd5.myworkdayjobs.com/wday/cxs/gartner/EXT/jobs"

    payload = {
        "appliedFacets": {
            "locationCountry": ["bc33aa3152ec42d4995f4791a106ed09"]
        },
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
        "Referer": "https://gartner.wd5.myworkdayjobs.com/EXT"
    }

    try:
        response = requests.post(base_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        seen_ids = set()
        jobs_to_process = []
        cutoff_date = datetime.now() - timedelta(days=days)

        for job in data.get('jobPostings', []):
            job_id = extract_gartner_id(job)
            if job_id and job_id not in seen_ids:
                seen_ids.add(job_id)
                jobs_to_process.append(job)

        # Process jobs concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_job = {
                executor.submit(process_gartner_job, job, cutoff_date): job
                for job in jobs_to_process
            }

            results = []
            for future in concurrent.futures.as_completed(future_to_job):
                result = future.result()
                if result:
                    results.append(result)

        # Sort the results by date_posted in descending order
        sorted_results = sorted(results, key=lambda x: x['date_posted'], reverse=True)
        return sorted_results

    except Exception as e:
        print(f"Error fetching Gartner jobs for role '{target_role}': {str(e)}")
        return []

def process_gartner_job(job, cutoff_date):
    try:
        job_url = f"https://gartner.wd5.myworkdayjobs.com/en-US/EXT{job.get('externalPath', '')}"
        metadata = get_gartner_details(job_url)

        if not metadata.get('datePosted'):
            return None

        post_date = parse_gartner_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_gartner_data(job, metadata)

    except Exception as e:
        print(f"Error processing Gartner job: {str(e)}")
    return None

def get_gartner_details(job_url):
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract from JSON-LD if available
        script = soup.find('script', {'type': 'application/ld+json'})
        if script:
            try:
                data = json.loads(script.string)
                return {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': clean_gartner_description(data.get('description', ''))
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
        print(f"Error fetching Gartner details from {job_url}: {str(e)}")
        return {}

def format_gartner_data(job, metadata):
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_gartner_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"https://gartner.wd5.myworkdayjobs.com/en-US/EXT{job.get('externalPath', '')}",
        "date_posted": format_gartner_date(metadata['datePosted']),
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }

def extract_gartner_id(job):
    try:
        path_parts = job['externalPath'].split('_')
        return f"{path_parts[-2]}_{path_parts[-1]}"  # Handle JR numbers with location codes
    except Exception:
        return job.get('bulletFields', ['N/A'])[0]

def parse_gartner_date(date_str):
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except Exception:
            continue
    return None

def format_gartner_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
    except Exception:
        return date_str

def clean_gartner_description(desc):
    if not desc:
        return 'N/A'
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    return ' '.join(cleaned.split()[:250]) + '...'

# Example usage:
# if __name__ == "__main__":
#     # For example, checking for these roles:
#     roles_to_check = ["Data Analyst", "Data Scientist"]
#     jobs_data = get_gartner_jobs(roles=roles_to_check, days=7)
#     # Print the aggregated results in JSON format:
#     print(json.dumps(jobs_data, indent=2, ensure_ascii=False))
