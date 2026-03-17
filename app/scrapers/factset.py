import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_factset_jobs(roles, days=7):
    """Main function to retrieve FactSet jobs structured by roles"""
    
    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        # Base URL for FactSet jobs API
        base_url = "https://factset.wd108.myworkdayjobs.com/wday/cxs/factset/FactSetCareers/jobs"

        # Payload for the POST request
        payload = {
            "appliedFacets": {},
            "searchText": target_role,
            "limit": 20,
            "offset": 0
        }

        # Headers for the request
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Referer": "https://factset.wd108.myworkdayjobs.com/FactSetCareers"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Deduplication and filtering
            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)

            for job in data.get('jobPostings', []):
                job_id = extract_factset_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            # Parallel processing of job details
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_factset_job, job, cutoff_date): job
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

def process_factset_job(job, cutoff_date):
    """Process individual job details"""
    try:
        job_url = f"https://factset.wd108.myworkdayjobs.com/en-US/FactSetCareers{job.get('externalPath', '')}"
        metadata = get_factset_job_details(job_url)

        if not metadata.get('datePosted'):
            return None

        post_date = parse_factset_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_factset_job_data(job, metadata)

    except Exception as e:
        print(f"Error processing FactSet job: {str(e)}")
    return None

def get_factset_job_details(job_url):
    """Extract job details from the job page"""
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to extract JSON-LD data first
        script = soup.find('script', {'type': 'application/ld+json'})
        if script:
            try:
                data = json.loads(script.string)
                return {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': clean_factset_description(data.get('description', ''))
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback: try to find meta tags
        meta_date = soup.find('meta', {'property': 'og:article:published_time'})
        meta_description = soup.find('meta', {'name': 'description'})
        
        if meta_date or meta_description:
            return {
                'datePosted': meta_date.get('content') if meta_date else None,
                'employmentType': 'FULL_TIME',  # Default assumption
                'description': clean_factset_description(meta_description.get('content') if meta_description else '')
            }
        
        return {}
        
    except Exception as e:
        print(f"Error fetching FactSet details from {job_url}: {str(e)}")
        return {}

def format_factset_job_data(job, metadata):
    """Format job data into consistent structure"""
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_factset_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"https://factset.wd108.myworkdayjobs.com/en-US/FactSetCareers{job.get('externalPath', '')}",
        "date_posted": format_factset_date(metadata.get('datePosted', '')),
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }

def extract_factset_job_id(job):
    """Extract job ID from job data"""
    try:
        # Try to extract from externalPath
        path_parts = job.get('externalPath', '').split('/')
        for part in reversed(path_parts):
            if part and len(part) > 5:  # Assuming job IDs are reasonably long
                return part
        # Fallback to bulletFields
        return job.get('bulletFields', ['N/A'])[0]
    except:
        return job.get('bulletFields', ['N/A'])[0]

def parse_factset_date(date_str):
    """Parse date string to datetime object"""
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d"
    ]
    
    for fmt in formats:
        try:
            # Handle timezone by removing 'Z' if present
            clean_date = date_str.replace('Z', '+00:00') if 'Z' in date_str else date_str
            return datetime.strptime(clean_date, fmt)
        except (ValueError, TypeError):
            continue
    
    try:
        # Last resort: try fromisoformat
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        return None

def format_factset_date(date_str):
    """Format date to YYYY-MM-DD"""
    if not date_str:
        return 'N/A'
    
    parsed_date = parse_factset_date(date_str)
    if parsed_date:
        return parsed_date.strftime("%Y-%m-%d")
    return date_str

def clean_factset_description(desc):
    """Clean and truncate job description"""
    if not desc:
        return 'N/A'
    
    # Remove HTML tags and clean up text
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    # Remove extra whitespace and truncate
    cleaned = ' '.join(cleaned.split())
    return cleaned[:500] + '...' if len(cleaned) > 500 else cleaned

def print_factset_results(jobs_data):
    """Pretty print the structured results"""
    print(json.dumps(jobs_data, indent=2, ensure_ascii=False))
