import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_radian_jobs(roles, days=7):
    """
    For each role in the roles list, fetch jobs posted in the last `days` days.
    Returns a dictionary where keys are role names and values are lists of job dicts.
    """
    aggregated_jobs = {}
    for role in roles:
        # Fetch the jobs for each role and store them under the role key.
        aggregated_jobs[role] = fetch_compass_jobs(role, days)
    return aggregated_jobs

def fetch_compass_jobs(target_role, days=7):
    base_url = "https://compass.wd5.myworkdayjobs.com/wday/cxs/compass/Radian_External_Career_Site/jobs"
    payload = {
        "searchText": target_role,
        "limit": 20,
        "offset": 0,
        "appliedFacets": {}
    }
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/91.0.4472.124 Safari/537.36"),
        "Referer": "https://compass.wd5.myworkdayjobs.com/Radian_External_Career_Site"
    }

    try:
        response = requests.post(base_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        seen_ids = set()
        jobs_to_process = []
        cutoff_date = datetime.now() - timedelta(days=days)

        for job in data.get('jobPostings', []):
            job_id = extract_compass_job_id(job)
            if job_id and job_id not in seen_ids:
                seen_ids.add(job_id)
                jobs_to_process.append(job)

        # Process jobs concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_job = {
                executor.submit(process_compass_job, job, cutoff_date): job
                for job in jobs_to_process
            }
            results = []
            for future in concurrent.futures.as_completed(future_to_job):
                result = future.result()
                if result:
                    results.append(result)

        # Sort results by date_posted in descending order and return
        sorted_results = sorted(results, key=lambda x: x['date_posted'], reverse=True)
        return sorted_results

    except Exception as e:
        print(f"Error fetching jobs for role '{target_role}': {str(e)}")
        return []

def process_compass_job(job, cutoff_date):
    try:
        job_url = f"https://compass.wd5.myworkdayjobs.com/Radian_External_Career_Site{job.get('externalPath', '')}"
        metadata = get_compass_job_details(job_url)
        if not metadata.get('datePosted'):
            return None
        post_date = parse_compass_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_compass_job_data(job, metadata)
    except Exception as e:
        print(f"Error processing job: {str(e)}")
    return None

def get_compass_job_details(job_url):
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
                    'description': clean_compass_description(data.get('description', ''))
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
        print(f"Error fetching details from {job_url}: {str(e)}")
        return {}

def format_compass_job_data(job, metadata):
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_compass_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"https://compass.wd5.myworkdayjobs.com/Radian_External_Career_Site{job.get('externalPath', '')}",
        "date_posted": format_compass_date(metadata['datePosted']),
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }

def extract_compass_job_id(job):
    try:
        return job['externalPath'].split('_')[-1].split('/')[-1]
    except Exception:
        return job.get('bulletFields', ['N/A'])[0]

def parse_compass_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    except Exception:
        try:
            # Handle dates in ISO format that might not include microseconds
            return datetime.fromisoformat(date_str.replace('Z', ''))
        except Exception:
            return None

def format_compass_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
    except Exception:
        return date_str

def clean_compass_description(desc):
    if not desc:
        return 'N/A'
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    # Limit the description to the first 200 words (as an example)
    return ' '.join(cleaned.split()[:200]) + '...'

# Example usage:
# if __name__ == "__main__":
#     # For instance, if you want to check for these roles:
#     roles_to_check = ["Software Engineer", "Data Scientist"]
#     jobs_data = get_salesforce_jobs(roles=roles_to_check, days=7)
#     # Print the aggregated results in JSON format:
#     print(json.dumps(jobs_data, indent=2, ensure_ascii=False))
