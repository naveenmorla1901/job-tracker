import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_mtbank_jobs(roles, days=7):
    """Main function to retrieve M&T Bank jobs structured by roles"""
    
    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://mtb.wd5.myworkdayjobs.com/wday/cxs/mtb/MTB/jobs"
        
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
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://mtb.wd5.myworkdayjobs.com/MTB"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Optional: Save debug info (commented out for production)
            # with open(f"mtb_debug_{target_role.replace(' ', '_')}.json", "w") as f:
            #     json.dump(data, f, indent=2)
            
            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for job in data.get('jobPostings', []):
                job_id = extract_mtb_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_mtb_job, job, cutoff_date): job 
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

def process_mtb_job(job, cutoff_date):
    try:
        job_url = f"https://mtb.wd5.myworkdayjobs.com/en-US/MTB{job.get('externalPath', '')}"
        metadata = get_mtb_job_details(job_url)
        
        if not metadata.get('datePosted'):
            return None
            
        post_date = parse_mtb_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_mtb_job_data(job, metadata)
            
    except Exception as e:
        print(f"Error processing MTB job: {str(e)}")
    return None

def get_mtb_job_details(job_url):
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
                    'description': clean_mtb_description(data.get('description', ''))
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback to meta tags
        date_posted = None
        meta_date = soup.find('meta', {'property': 'og:article:published_time'})
        if meta_date:
            date_posted = meta_date.get('content')
        
        # Also try Workday-specific meta
        if not date_posted:
            meta_workday = soup.find('meta', {'name': 'postedDate'})
            if meta_workday:
                date_posted = meta_workday.get('content')
        
        return {
            'datePosted': date_posted,
            'employmentType': (soup.find('meta', {'name': 'employmentType'}) or {}).get('content'),
            'description': (soup.find('meta', {'name': 'description'}) or {}).get('content')
        }
        
    except Exception as e:
        print(f"Error fetching MTB job details: {str(e)}")
        return {}

def format_mtb_job_data(job, metadata):
    # Clean job title (remove HTML entities if any)
    job_title = job.get('title', 'N/A')
    if isinstance(job_title, str):
        job_title = BeautifulSoup(job_title, 'html.parser').get_text()
    
    return {
        "job_title": job_title,
        "job_id": extract_mtb_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"https://mtb.wd5.myworkdayjobs.com/en-US/MTB{job.get('externalPath', '')}",
        "date_posted": format_mtb_date(metadata['datePosted']),
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }

def extract_mtb_job_id(job):
    # Try multiple methods to extract job ID
    try:
        # Method 1: From bulletFields
        if job.get('bulletFields'):
            return job['bulletFields'][0]
        
        # Method 2: From externalPath
        if job.get('externalPath'):
            path_parts = job['externalPath'].split('_')
            return path_parts[-1].split('/')[-1]
        
        # Method 3: From jobPostingId if available
        if job.get('jobPostingId'):
            return job['jobPostingId']
            
    except Exception:
        pass
    
    return 'N/A'

def parse_mtb_date(date_str):
    if not date_str:
        return None
        
    # Try different date formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%SZ"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    try:
        return datetime.fromisoformat(date_str.replace('Z', ''))
    except:
        return None

def format_mtb_date(date_str):
    if not date_str:
        return 'N/A'
    
    try:
        # Try to parse and format nicely
        parsed_date = parse_mtb_date(date_str)
        if parsed_date:
            return parsed_date.strftime("%Y-%m-%d")
    except:
        pass
    
    # Return original if parsing fails
    return date_str[:10] if date_str else 'N/A'

def clean_mtb_description(desc):
    if not desc:
        return 'N/A'
    
    # Clean HTML and truncate
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    # Remove extra whitespace
    cleaned = ' '.join(cleaned.split())
    # Truncate to 250 words for banking job descriptions
    words = cleaned.split()
    if len(words) > 250:
        return ' '.join(words[:250]) + '...'
    return cleaned
