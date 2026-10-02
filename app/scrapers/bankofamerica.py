import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_bankofamerica_jobs(roles, days=7):
    """Main function to retrieve Bank of America jobs structured by roles"""

    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://ghr.wd1.myworkdayjobs.com/wday/cxs/ghr/Lateral-US/jobs"

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
            "Referer": "https://ghr.wd1.myworkdayjobs.com/Lateral-US"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()

            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)

            for job in data.get('jobPostings', []):
                job_id = extract_bankofamerica_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_bankofamerica_job, job, cutoff_date): job
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

def process_bankofamerica_job(job, cutoff_date):
    try:
        job_url = f"https://ghr.wd1.myworkdayjobs.com/en-US/Lateral-US{job.get('externalPath', '')}"
        metadata = get_bankofamerica_job_details(job_url)

        if not metadata.get('datePosted'):
            return None

        post_date = parse_bankofamerica_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_bankofamerica_job_data(job, metadata)

    except Exception as e:
        print(f"Error processing job: {str(e)}")
    return None

def get_bankofamerica_job_details(job_url):
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
                    'description': clean_bankofamerica_description(data.get('description', ''))
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

def format_bankofamerica_job_data(job, metadata):
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_bankofamerica_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"https://ghr.wd1.myworkdayjobs.com/en-US/Lateral-US{job.get('externalPath', '')}",
        "date_posted": format_bankofamerica_date(metadata['datePosted']),
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }

def extract_bankofamerica_job_id(job):
    try:
        path = job.get('externalPath', '')
        if '_' in path:
            return path.split('_')[-1].split('/')[0]
        return path.split('/')[-1]
    except:
        return job.get('bulletFields', ['N/A'])[0]

def parse_bankofamerica_date(date_str):
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            # Drop tzinfo so the result compares cleanly with the naive cutoff date
            return datetime.strptime(date_str, fmt).replace(tzinfo=None)
        except:
            continue
    return None

def format_bankofamerica_date(date_str):
    parsed = parse_bankofamerica_date(date_str)
    return parsed.strftime("%Y-%m-%d") if parsed else date_str

def clean_bankofamerica_description(desc):
    if not desc:
        return 'N/A'
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    return ' '.join(cleaned.split()[:250]) + '...'

# Example usage:
# if __name__ == "__main__":
#     jobs_data = get_bankofamerica_jobs(roles=["Data Scientist", "Machine Learning Engineer"], days=7)
#     print(json.dumps(jobs_data, indent=2, ensure_ascii=False))
