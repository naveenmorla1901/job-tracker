import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

# --- Configuration Section ---
# YOU MUST UPDATE THESE VALUES FOR FEDEX
FEDEX_COMPANY_NAME = "fedex"  # From the subdomain: fedex.wd1...
FEDEX_CAREER_SITE = "FXE-EU_External"  # From the URL path
FEDEX_API_URL = f"https://{FEDEX_COMPANY_NAME}.wd1.myworkdayjobs.com/wday/cxs/{FEDEX_COMPANY_NAME}/{FEDEX_CAREER_SITE}/jobs"
FEDEX_REFERER = f"https://{FEDEX_COMPANY_NAME}.wd1.myworkdayjobs.com/{FEDEX_CAREER_SITE}"
FEDEX_JOB_BASE_URL = f"https://{FEDEX_COMPANY_NAME}.wd1.myworkdayjobs.com/en-US/{FEDEX_CAREER_SITE}"

# Facets - You need to find these from the network request on the FedEx site
# These are PLACEHOLDERS and MUST be updated!
FACETS = {
    # "locationCountry": ["bc33aa3152ec42d4995f4791a106ed09"], # Example for US
    # "timeType": ["your_time_type_facet_id_here"]
}
# --- End of Configuration Section ---

def get_fedex_jobs(roles, days=7):
    """
    Main function to retrieve FedEx jobs structured by roles
    
    Args:
        roles (list): List of job roles to search for
        days (int): Number of days to look back for job postings
    
    Returns:
        dict: Structured results with roles as keys and job lists as values
    """
    
    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        payload = {
            "appliedFacets": FACETS,
            "searchText": target_role,
            "limit": 20,
            "offset": 0
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": FEDEX_REFERER
        }

        try:
            response = requests.post(FEDEX_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)

            for job in data.get('jobPostings', []):
                job_id = extract_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_fedex_job, job, cutoff_date): job
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
        print(f"Fetching {role} jobs...")  # Optional progress indicator
        structured_results[role] = fetch_role_jobs(role)
    
    return structured_results

def process_fedex_job(job, cutoff_date):
    """Process individual job posting"""
    try:
        job_url = f"{FEDEX_JOB_BASE_URL}{job.get('externalPath', '')}"
        metadata = get_fedex_job_details(job_url)

        if not metadata.get('datePosted'):
            return None

        post_date = parse_fedex_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_fedex_job_data(job, metadata)

    except Exception as e:
        print(f"Error processing job {job.get('title', 'N/A')}: {str(e)}")
    return None

def get_fedex_job_details(job_url):
    """Fetch detailed job information from job page"""
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
                    'description': clean_fedex_description(data.get('description', ''))
                }
            except json.JSONDecodeError:
                pass

        return {
            'datePosted': (soup.find('meta', {'property': 'og:article:published_time'}) or {}).get('content'),
            'employmentType': (soup.find('meta', {'name': 'employmentType'}) or {}).get('content'),
            'description': (soup.find('meta', {'name': 'description'}) or {}).get('content')
        }

    except Exception as e:
        print(f"Error fetching details from {job_url}: {str(e)}")
        return {}

def format_fedex_job_data(job, metadata):
    """Format job data into standardized structure"""
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"{FEDEX_JOB_BASE_URL}{job.get('externalPath', '')}",
        "date_posted": format_fedex_date(metadata['datePosted']),
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }

def extract_job_id(job):
    """Extract job ID from job data"""
    try:
        return job['externalPath'].split('_')[-1].split('/')[-1]
    except:
        return job.get('bulletFields', ['N/A'])[0]

def parse_fedex_date(date_str):
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    except:
        try:
            return datetime.fromisoformat(date_str.replace('Z', ''))
        except:
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except:
                return None

def format_fedex_date(date_str):
    """Format date string to YYYY-MM-DD format"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
    except:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y-%m-%d")
        except:
            return date_str

def clean_fedex_description(desc):
    """Clean and truncate job description"""
    if not desc:
        return 'N/A'
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    return ' '.join(cleaned.split()[:200]) + '...'

def print_fedex_summary(structured_results, days):
    """Print a summary of results by role"""
    print(f"\n{'='*80}")
    print(f"FEDEX JOB SEARCH SUMMARY (LAST {days} DAYS)")
    print(f"{'='*80}")
    
    total_jobs = 0
    for role, jobs in structured_results.items():
        count = len(jobs)
        total_jobs += count
        print(f"\n{role}: {count} job(s) found")
        if count > 0:
            print(f"  Latest: {jobs[0]['job_title']} ({jobs[0]['date_posted']})")
    
    print(f"\n{'='*80}")
    print(f"TOTAL JOBS FOUND: {total_jobs}")
    print(f"{'='*80}")
