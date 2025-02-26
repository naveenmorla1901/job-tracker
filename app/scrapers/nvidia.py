import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_nvidia_jobs(roles, days=7):
    """
    For each role in the roles list, fetch NVIDIA jobs posted in the last `days` days.
    Returns a dictionary where keys are role names and values are lists of job dicts.
    """
    aggregated_jobs = {}
    for role in roles:
        aggregated_jobs[role] = fetch_nvidia_jobs(role, days)
    return aggregated_jobs

def fetch_nvidia_jobs(target_role, days=7):
    base_url = "https://nvidia.wd5.myworkdayjobs.com/wday/cxs/nvidia/NVIDIAExternalCareerSite/jobs"
    payload = {
        "appliedFacets": {
            "locationHierarchy1": ["2fcb99c455831013ea52fb338f2932d8"]
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
        "Referer": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite"
    }

    try:
        response = requests.post(base_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        seen_ids = set()
        jobs_to_process = []
        cutoff_date = datetime.now() - timedelta(days=days)

        for job in data.get('jobPostings', []):
            job_id = extract_nvidia_job_id(job)
            if job_id and job_id not in seen_ids:
                seen_ids.add(job_id)
                jobs_to_process.append(job)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_job = {
                executor.submit(process_nvidia_job, job, cutoff_date): job
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
        print(f"Error fetching NVIDIA jobs for role '{target_role}': {str(e)}")
        return []

def process_nvidia_job(job, cutoff_date):
    try:
        job_url = f"https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite{job.get('externalPath', '')}"
        metadata = get_nvidia_job_details(job_url)
        if not metadata.get('datePosted'):
            return None
        post_date = parse_nvidia_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_nvidia_job_data(job, metadata)
    except Exception as e:
        print(f"Error processing NVIDIA job: {str(e)}")
    return None

def get_nvidia_job_details(job_url):
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract details from JSON-LD if available
        script = soup.find('script', {'type': 'application/ld+json'})
        if script:
            try:
                data = json.loads(script.string)
                return {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': clean_nvidia_description(data.get('description', ''))
                }
            except json.JSONDecodeError:
                pass

        # Fallback to meta tags if JSON-LD is not available
        return {
            'datePosted': (soup.find('meta', {'property': 'og:article:published_time'}) or {}).get('content'),
            'employmentType': (soup.find('meta', {'name': 'employmentType'}) or {}).get('content'),
            'description': (soup.find('meta', {'name': 'description'}) or {}).get('content')
        }
    except Exception as e:
        print(f"Error fetching NVIDIA details from {job_url}: {str(e)}")
        return {}

def format_nvidia_job_data(job, metadata):
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_nvidia_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite{job.get('externalPath', '')}",
        "date_posted": format_nvidia_date(metadata['datePosted']),
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }

def extract_nvidia_job_id(job):
    try:
        return job['externalPath'].split('/')[-1].split('_')[-1]
    except Exception:
        return job.get('bulletFields', ['N/A'])[0]

def parse_nvidia_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    except Exception:
        try:
            return datetime.fromisoformat(date_str.replace('Z', ''))
        except Exception:
            return None

def format_nvidia_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
    except Exception:
        return date_str

def clean_nvidia_description(desc):
    if not desc:
        return 'N/A'
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    # Limit the description to the first 250 words as NVIDIA descriptions tend to be longer
    return ' '.join(cleaned.split()[:250]) + '...'

# Example usage:
# if __name__ == "__main__":
#     # Specify NVIDIA-specific roles
#     nvidia_roles = [
#         "Generative AI",
#         "Data Analyst"
#     ]

#     jobs_data = get_nvidia_jobs(roles=nvidia_roles, days=30)
#     # Print the aggregated results in JSON format:
#     print(json.dumps(jobs_data, indent=2, ensure_ascii=False))
