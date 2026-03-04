import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_oclc_jobs(roles, days=7):
    """
    Main function to retrieve OCLC jobs structured by roles
    
    Args:
        roles (list): List of job roles to search for
        days (int): Number of days to look back for jobs
    
    Returns:
        dict: Structured results with roles as keys
    """
    
    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://oclc.wd1.myworkdayjobs.com/wday/cxs/oclc/OCLC_Careers/jobs"
        
        # TODO: Replace facet IDs with OCLC's actual values after inspection
        payload = {
            "appliedFacets": {
                # Example facet - uncomment after verifying actual values
                # "locationCountry": ["bc33aa3152ec42d4995f4791a106ed09"]
            },
            "searchText": target_role,
            "limit": 20,
            "offset": 0
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://oclc.wd1.myworkdayjobs.com/OCLC_Careers"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Process jobs with deduplication and date filtering
            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for job in data.get('jobPostings', []):
                job_id = extract_oclc_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            # Parallel processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_oclc_job, job, cutoff_date): job 
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
        print(f"Fetching {role} jobs...")  # Progress indicator
        structured_results[role] = fetch_role_jobs(role)
    
    return structured_results

def process_oclc_job(job, cutoff_date):
    """Process individual job and fetch additional details"""
    try:
        # Construct job URL using OCLC's pattern
        job_url = f"https://oclc.wd1.myworkdayjobs.com/en-US/OCLC_Careers{job.get('externalPath', '')}"
        metadata = get_oclc_job_details(job_url)
        
        if metadata.get('datePosted'):
            post_date = parse_oclc_date(metadata['datePosted'])
            if post_date and post_date >= cutoff_date:
                return {
                    "job_title": job.get('title', 'N/A'),
                    "job_id": extract_oclc_job_id(job),
                    "location": job.get('locationsText', 'N/A'),
                    "job_url": job_url,
                    "date_posted": format_oclc_date(metadata['datePosted']),
                    "employment_type": metadata.get('employmentType', 'N/A'),
                    "description": clean_oclc_description(metadata.get('description', 'N/A'))
                }
    except Exception as e:
        print(f"Error processing job: {str(e)}")
    return None

def get_oclc_job_details(job_url):
    """Fetch detailed job information from job page"""
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try JSON-LD first
        script = soup.find('script', {'type': 'application/ld+json'})
        if script and script.string:
            try:
                data = json.loads(script.string)
                return {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': data.get('description', '')
                }
            except json.JSONDecodeError:
                pass
        
        # Try meta tags as fallback
        meta_date = soup.find('meta', {'property': 'og:article:published_time'})
        meta_type = soup.find('meta', {'name': 'employmentType'})
        meta_desc = soup.find('meta', {'name': 'description'})
        
        # Try to find date in other locations
        if not meta_date:
            # Look for date in job posting structure
            date_elem = soup.find('span', {'data-automation-id': 'postedOn'})
            if date_elem:
                meta_date = type('obj', (), {'get': lambda self, x: date_elem.text})()
        
        return {
            'datePosted': meta_date.get('content') if meta_date else None,
            'employmentType': meta_type.get('content') if meta_type else None,
            'description': meta_desc.get('content') if meta_desc else None
        }
    except Exception as e:
        print(f"Error fetching job details from {job_url}: {str(e)}")
        return {}

def extract_oclc_job_id(job):
    """Extract job ID from job data"""
    # Try multiple extraction methods
    if job.get('externalPath'):
        # Extract ID from path (usually last part after slash or underscore)
        path_parts = job['externalPath'].split('/')
        for part in reversed(path_parts):
            if part and not part.startswith('job'):
                return part.split('_')[-1]
    
    # Fallback to bulletFields
    return job.get('bulletFields', ['N/A'])[0]

def parse_oclc_date(date_str):
    """Parse various date formats"""
    if not date_str:
        return None
    
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
        "%B %d, %Y"  # For text dates like "February 24, 2025"
    ]
    
    # Handle Z timezone
    date_str = date_str.replace('Z', '+00:00')
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    # Try fromisoformat as last resort
    try:
        return datetime.fromisoformat(date_str)
    except:
        pass
    
    return None

def format_oclc_date(date_str):
    """Format date to YYYY-MM-DD"""
    parsed_date = parse_oclc_date(date_str)
    if parsed_date:
        return parsed_date.strftime("%Y-%m-%d")
    return date_str

def clean_oclc_description(desc):
    """Clean and truncate description"""
    if not desc or desc == 'N/A':
        return 'N/A'
    
    # If it's HTML, clean it
    if '<' in desc and '>' in desc:
        cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    else:
        cleaned = desc
    
    # Remove extra whitespace and truncate
    cleaned = ' '.join(cleaned.split())
    if len(cleaned) > 500:
        cleaned = cleaned[:497] + '...'
    
    return cleaned

def save_results_to_file(results, filename="oclc_jobs.json"):
    """Save results to JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nResults saved to {filename}")

def print_formatted_results(results):
    """Print results in a nicely formatted way"""
    print("\n" + "="*80)
    print("OCLC JOB SEARCH RESULTS")
    print("="*80)
    
    total_jobs = 0
    for role, jobs in results.items():
        print(f"\n📋 {role.upper()} ({len(jobs)} jobs found)")
        print("-" * 60)
        
        if not jobs:
            print("  No jobs found")
            continue
            
        for job in jobs:
            print(f"\n  🔹 {job['job_title']}")
            print(f"     ID: {job['job_id']}")
            print(f"     Location: {job['location']}")
            print(f"     Posted: {job['date_posted']}")
            print(f"     Type: {job['employment_type']}")
            print(f"     URL: {job['job_url']}")
            if job['description'] != 'N/A':
                desc_preview = job['description'][:100] + "..." if len(job['description']) > 100 else job['description']
                print(f"     Description: {desc_preview}")
        
        total_jobs += len(jobs)
    
    print("\n" + "="*80)
    print(f"SUMMARY: Found {total_jobs} total jobs across {len(results)} roles")
    print("="*80)