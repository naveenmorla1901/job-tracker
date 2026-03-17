import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_carrier_jobs(roles, days=7):
    """Main function to retrieve Carrier jobs structured by roles"""
    
    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://carrier.wd5.myworkdayjobs.com/wday/cxs/carrier/jobs/jobs"
        
        payload = {
            "appliedFacets": {
                "location_Country": ["bc33aa3152ec42d4995f4791a106ed09"]
            },
            "searchText": target_role,
            "limit": 20,
            "offset": 0
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://carrier.wd5.myworkdayjobs.com/jobs"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
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
                    executor.submit(process_carrier_job, job, cutoff_date): job 
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


def process_carrier_job(job, cutoff_date):
    """Process individual job to extract details"""
    try:
        job_url = f"https://carrier.wd5.myworkdayjobs.com/en-US/jobs{job.get('externalPath', '')}"
        metadata = get_carrier_job_details(job_url)
        
        if not metadata.get('datePosted'):
            return None
            
        post_date = parse_carrier_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_carrier_job_data(job, metadata)
            
    except Exception as e:
        print(f"Error processing job: {str(e)}")
    return None


def get_carrier_job_details(job_url):
    """Extract job details from job posting page"""
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract from JSON-LD
        script = soup.find('script', {'type': 'application/ld+json'})
        if script:
            try:
                data = json.loads(script.string)
                return {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': clean_carrier_description(data.get('description', ''))
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
        print(f"Error fetching details from {job_url}: {str(e)}")
        return {}


def format_carrier_job_data(job, metadata):
    """Format job data for output"""
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"https://carrier.wd5.myworkdayjobs.com/en-US/jobs{job.get('externalPath', '')}",
        "date_posted": format_carrier_date(metadata['datePosted']),
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }


def extract_job_id(job):
    """Extract job ID from job data"""
    try:
        return job['externalPath'].split('_')[-1].split('/')[-1]
    except:
        return job.get('bulletFields', ['N/A'])[0]


def parse_carrier_date(date_str):
    """Parse date string to datetime object"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    except:
        try:
            return datetime.fromisoformat(date_str.replace('Z', ''))
        except:
            return None


def format_carrier_date(date_str):
    """Format date to YYYY-MM-DD"""
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
    except:
        return date_str


def clean_carrier_description(desc):
    """Clean HTML from description and truncate"""
    if not desc:
        return 'N/A'
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    return ' '.join(cleaned.split()[:200]) + '...'


def print_carrier_results(jobs_data):
    """Pretty print the structured results"""
    for role, jobs in jobs_data.items():
        if jobs:
            print(f"\n{len(jobs)} RECENT {role.upper()} JOBS AT CARRIER")
            print("=" * 70)
            print(json.dumps(jobs, indent=2, ensure_ascii=False))
        else:
            print(f"\nNo {role} jobs found at Carrier")
        print("\n" + "-"*80 + "\n")

