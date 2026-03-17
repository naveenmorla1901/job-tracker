import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_amplify_jobs(roles, days=7):
    """Main function to retrieve Amplify jobs structured by roles"""
    
    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://amplify.wd1.myworkdayjobs.com/wday/cxs/amplify/Amplify_Careers/jobs"
        
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
            "Referer": "https://amplify.wd1.myworkdayjobs.com/Amplify_Careers"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Optional debug: Save raw response
            # with open(f"amplify_debug_{target_role.replace(' ', '_')}.json", "w") as f:
            #     json.dump(data, f, indent=2)
            
            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for job in data.get('jobPostings', []):
                job_id = extract_amplify_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            # Process jobs in parallel
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_amplify_job, job, cutoff_date): job 
                    for job in jobs_to_process
                }
                
                results = []
                for future in concurrent.futures.as_completed(future_to_job):
                    result = future.result()
                    if result:
                        results.append(result)

            return sorted(results, key=lambda x: x['date_posted'], reverse=True)

        except Exception as e:
            print(f"Error fetching {target_role} jobs from Amplify: {str(e)}")
            return []

    # Structure results by role
    structured_results = {}
    for role in roles:
        structured_results[role] = fetch_role_jobs(role)
    
    return structured_results

def process_amplify_job(job, cutoff_date):
    """Process individual job and extract details"""
    try:
        job_url = f"https://amplify.wd1.myworkdayjobs.com/en-US/Amplify_Careers{job.get('externalPath', '')}"
        metadata = get_amplify_job_details(job_url)
        
        if not metadata.get('datePosted'):
            return None
            
        post_date = parse_amplify_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_amplify_job_data(job, metadata)
            
    except Exception as e:
        print(f"Error processing job: {str(e)}")
    return None

def get_amplify_job_details(job_url):
    """Fetch detailed job information from job page"""
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # First try JSON-LD format
        script = soup.find('script', {'type': 'application/ld+json'})
        if script:
            try:
                data = json.loads(script.string)
                return {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': clean_amplify_description(data.get('description', ''))
                }
            except json.JSONDecodeError:
                pass
        
        # Try to find job posting date in other meta tags
        meta_date = soup.find('meta', {'property': 'og:article:published_time'})
        if meta_date:
            return {
                'datePosted': meta_date.get('content'),
                'employmentType': (soup.find('meta', {'name': 'employmentType'}) or {}).get('content', 'N/A'),
                'description': (soup.find('meta', {'name': 'description'}) or {}).get('content', 'N/A')
            }
        
        # Look for date in other elements
        date_element = soup.find('div', {'class': 'css-1orml15'}) or soup.find('span', {'class': 'wd-date-posted'})
        if date_element:
            return {
                'datePosted': date_element.get_text(strip=True),
                'employmentType': 'N/A',
                'description': 'N/A'
            }
            
    except Exception as e:
        print(f"Error fetching details from {job_url}: {str(e)}")
    
    return {}

def format_amplify_job_data(job, metadata):
    """Format job data into standardized structure"""
    # Get location from job object, handle multiple formats
    location = job.get('locationsText', 'N/A')
    if location == 'N/A':
        location = job.get('primaryLocation', 'N/A')
    
    # Format date nicely
    date_posted = metadata.get('datePosted', 'N/A')
    if date_posted != 'N/A':
        try:
            date_posted = parse_amplify_date(date_posted).strftime("%Y-%m-%d")
        except:
            pass
    
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_amplify_job_id(job),
        "location": location,
        "job_url": f"https://amplify.wd1.myworkdayjobs.com/en-US/Amplify_Careers{job.get('externalPath', '')}",
        "date_posted": date_posted,
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')[:500] + "..." if metadata.get('description') != 'N/A' else 'N/A'
    }

def extract_amplify_job_id(job):
    """Extract job ID using multiple methods"""
    # Method 1: From externalPath
    if job.get('externalPath'):
        try:
            return job['externalPath'].split('_')[-1].split('/')[-1]
        except:
            pass
    
    # Method 2: From bulletFields
    if job.get('bulletFields'):
        return job['bulletFields'][0]
    
    # Method 3: From jobPostingId
    if job.get('jobPostingId'):
        return job['jobPostingId']
    
    return 'N/A'

def parse_amplify_date(date_str):
    """Parse various date formats that Amplify might use"""
    if not date_str or date_str == 'N/A':
        return datetime.now() - timedelta(days=30)  # Return old date if no date found
    
    # Try common date formats
    date_formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO with timezone
        "%Y-%m-%dT%H:%M:%S%z",      # ISO with timezone (simplified)
        "%Y-%m-%d",                  # Simple date
        "%B %d, %Y",                 # Month Day, Year
        "%b %d, %Y"                   # Abbreviated month
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    # Try parsing with fromisoformat
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        pass
    
    # Return old date if all parsing fails
    return datetime.now() - timedelta(days=30)

def clean_amplify_description(desc):
    """Clean HTML from description"""
    if not desc:
        return 'N/A'
    return BeautifulSoup(desc, 'html.parser').get_text(separator=' ')

def print_amplify_summary(results):
    """Print a summary of results by role"""
    print("\n" + "=" * 70)
    print("AMPLIFY CAREERS - JOB SEARCH SUMMARY")
    print("=" * 70)
    
    total_jobs = 0
    for role, jobs in results.items():
        if jobs:
            print(f"\n📋 {role}: {len(jobs)} job(s) found")
            total_jobs += len(jobs)
            
            # Show location breakdown for roles with jobs
            if jobs:
                locations = {}
                for job in jobs:
                    loc = job['location']
                    locations[loc] = locations.get(loc, 0) + 1
                
                # Show top 3 locations
                top_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)[:3]
                location_str = ", ".join([f"{loc} ({count})" for loc, count in top_locations])
                if location_str:
                    print(f"   📍 Top locations: {location_str}")
    
    print(f"\n📊 TOTAL: {total_jobs} job(s) found across {len([r for r, j in results.items() if j])} role(s)")
    print("=" * 70)
