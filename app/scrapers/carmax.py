import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_carmax_jobs(roles, days=7):
    """
    Main function to retrieve CarMax jobs structured by roles
    
    Args:
        roles (list): List of job roles to search for
        days (int): Number of days to look back for recent jobs
    
    Returns:
        dict: Structured results with roles as keys and job lists as values
    """
    
    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://carmax.wd1.myworkdayjobs.com/wday/cxs/carmax/External/jobs"
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
            "Referer": "https://carmax.wd1.myworkdayjobs.com/External"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)

            for job in data.get('jobPostings', []):
                job_id = extract_carmax_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            # Process jobs in parallel for speed
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_carmax_job, job, cutoff_date): job
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

def process_carmax_job(job, cutoff_date):
    """Process a single job to get its details and check posting date."""
    try:
        job_url = f"https://carmax.wd1.myworkdayjobs.com/en-US/External{job.get('externalPath', '')}"
        metadata = get_carmax_job_details(job_url)

        if not metadata.get('datePosted'):
            return None

        post_date = parse_carmax_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_carmax_job_data(job, metadata)

    except Exception as e:
        print(f"Error processing job: {str(e)}")
    return None

def get_carmax_job_details(job_url):
    """Fetch detailed job information from its individual page."""
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Try to extract from JSON-LD structured data first
        script = soup.find('script', {'type': 'application/ld+json'})
        if script:
            try:
                data = json.loads(script.string)
                return {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': clean_carmax_description(data.get('description', ''))
                }
            except json.JSONDecodeError:
                pass

        # Fallback to common meta tags
        return {
            'datePosted': (soup.find('meta', {'property': 'og:article:published_time'}) or {}).get('content'),
            'employmentType': (soup.find('meta', {'name': 'employmentType'}) or {}).get('content'),
            'description': (soup.find('meta', {'name': 'description'}) or {}).get('content')
        }

    except Exception as e:
        # Return empty dict if details can't be fetched
        return {}

def format_carmax_job_data(job, metadata):
    """Structure the job data into the desired output format."""
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_carmax_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"https://carmax.wd1.myworkdayjobs.com/en-US/External{job.get('externalPath', '')}",
        "date_posted": format_carmax_date(metadata.get('datePosted')),
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }

def extract_carmax_job_id(job):
    """Extract job ID reliably from different possible fields."""
    # Try externalPath first (often contains the ID)
    if job.get('externalPath'):
        # Get the last part after the last slash or underscore
        path_parts = job['externalPath'].split('_')
        return path_parts[-1].split('/')[-1]
    # Fallback to bulletFields
    return job.get('bulletFields', ['N/A'])[0]

def parse_carmax_date(date_str):
    """Convert date string to datetime object for comparison."""
    if not date_str:
        return None
    try:
        # Try common ISO formats
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        except ValueError:
            return None

def format_carmax_date(date_str):
    """Format date to YYYY-MM-DD for output."""
    if not date_str:
        return 'N/A'
    try:
        dt = parse_carmax_date(date_str)
        return dt.strftime("%Y-%m-%d") if dt else date_str[:10]
    except:
        return date_str

def clean_carmax_description(desc):
    """Clean HTML from description and truncate."""
    if not desc:
        return 'N/A'
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    words = cleaned.split()
    if len(words) > 200:
        return ' '.join(words[:200]) + '...'
    return cleaned
