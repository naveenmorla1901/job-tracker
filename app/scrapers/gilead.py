import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_gilead_jobs(roles, days=7):
    """
    Main function to retrieve Gilead jobs structured by roles
    
    Args:
        roles (list): List of job roles to search for
        days (int): Number of days to look back for job postings
    
    Returns:
        dict: Structured dictionary with roles as keys and job lists as values
    """
    
    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://gilead.wd1.myworkdayjobs.com/wday/cxs/gilead/gileadcareers/jobs"
        
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
            "Referer": "https://gilead.wd1.myworkdayjobs.com/gileadcareers"
        }
        
        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for job in data.get('jobPostings', []):
                job_id = extract_gilead_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)
            
            # Process jobs in parallel for speed
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_gilead_job, job, cutoff_date): job
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
        print(f"Fetching {role} jobs...")
        structured_results[role] = fetch_role_jobs(role)
    
    return structured_results

def process_gilead_job(job, cutoff_date):
    """Process individual job and fetch details"""
    try:
        job_url = f"https://gilead.wd1.myworkdayjobs.com/en-US/gileadcareers{job.get('externalPath', '')}"
        metadata = get_gilead_job_details(job_url)
        
        if not metadata.get('datePosted'):
            return None
        
        post_date = parse_gilead_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_gilead_job_data(job, metadata)
    
    except Exception as e:
        print(f"Error processing job: {str(e)}")
    return None

def get_gilead_job_details(job_url):
    """Fetch detailed job information from job page"""
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract from JSON-LD (standard for Workday)
        script = soup.find('script', {'type': 'application/ld+json'})
        if script:
            try:
                data = json.loads(script.string)
                return {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': clean_gilead_description(data.get('description', ''))
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

def format_gilead_job_data(job, metadata):
    """Format job data into consistent structure"""
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_gilead_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"https://gilead.wd1.myworkdayjobs.com/en-US/gileadcareers{job.get('externalPath', '')}",
        "date_posted": format_gilead_date(metadata['datePosted']),
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }

def extract_gilead_job_id(job):
    """Extract job ID, trying multiple common Workday formats."""
    # Try externalPath first (often contains the ID at the end)
    if job.get('externalPath'):
        path_parts = job['externalPath'].split('_')
        if len(path_parts) > 1:
            return path_parts[-1].split('/')[-1]
    # Fallback to bulletFields
    return job.get('bulletFields', ['N/A'])[0]

def parse_gilead_date(date_str):
    """Parse dates in common Workday formats."""
    try:
        # Try ISO format with timezone
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    except:
        try:
            # Try ISO format without microseconds
            return datetime.fromisoformat(date_str.replace('Z', ''))
        except:
            try:
                # Try simple date format
                return datetime.strptime(date_str, "%Y-%m-%d")
            except:
                return None

def format_gilead_date(date_str):
    """Convert date to YYYY-MM-DD string."""
    parsed_date = parse_gilead_date(date_str)
    return parsed_date.strftime("%Y-%m-%d") if parsed_date else date_str

def clean_gilead_description(desc):
    """Clean and truncate job description"""
    if not desc:
        return 'N/A'
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    # Truncate to 250 words for readability
    return ' '.join(cleaned.split()[:250]) + '...'

def save_results_to_file(results, filename="gilead_jobs.json"):
    """Save results to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"Results saved to {filename}")

