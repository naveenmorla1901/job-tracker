import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_fidelity_jobs(roles, days=7):
    """Main function to retrieve Fidelity jobs structured by roles"""
    
    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://fmr.wd1.myworkdayjobs.com/wday/cxs/fmr/FidelityCareers/jobs"
        
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
            "Referer": "https://fmr.wd1.myworkdayjobs.com/FidelityCareers"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Deduplicate jobs
            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for job in data.get('jobPostings', []):
                job_id = extract_fidelity_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            if not jobs_to_process:
                return []

            # Parallel processing of job details
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_fidelity_job, job, cutoff_date): job 
                    for job in jobs_to_process
                }
                
                results = []
                for future in concurrent.futures.as_completed(future_to_job):
                    result = future.result()
                    if result:
                        results.append(result)

            return sorted(results, key=lambda x: x['date_posted'], reverse=True)

        except requests.exceptions.RequestException as e:
            print(f"❌ Network error for {target_role}: {str(e)}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ Data parsing error for {target_role}: {str(e)}")
            return []
        except Exception as e:
            print(f"❌ Unexpected error for {target_role}: {str(e)}")
            return []

    # Structure results by role
    structured_results = {}
    for role in roles:
        structured_results[role] = fetch_role_jobs(role)
    
    return structured_results

def process_fidelity_job(job, cutoff_date):
    """Process individual job and fetch details"""
    try:
        # Construct job URL
        external_path = job.get('externalPath', '')
        if not external_path:
            return None
            
        job_url = f"https://fmr.wd1.myworkdayjobs.com/en-US/FidelityCareers{external_path}"
        metadata = get_fidelity_job_details(job_url)
        
        if not metadata.get('datePosted'):
            # Try to get date from job object if metadata fails
            posted_on = job.get('postedOn', '')
            if posted_on:
                metadata['datePosted'] = parse_fidelity_posted_date(posted_on)
            else:
                return None
            
        post_date = parse_fidelity_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_fidelity_job_data(job, metadata)
            
    except Exception as e:
        print(f"⚠️ Error processing job: {str(e)}")
    return None

def get_fidelity_job_details(job_url):
    """Fetch detailed job information from job page"""
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract from JSON-LD (primary method)
        script = soup.find('script', {'type': 'application/ld+json'})
        if script:
            try:
                data = json.loads(script.string)
                return {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': clean_fidelity_description(data.get('description', ''))
                }
            except json.JSONDecodeError:
                pass
        
        # Fallback: Look for Workday-specific meta tags
        meta_tags = {
            'datePosted': None,
            'employmentType': None,
            'description': None
        }
        
        # Try to find meta tags
        meta_date = soup.find('meta', {'property': 'og:article:published_time'})
        if meta_date:
            meta_tags['datePosted'] = meta_date.get('content')
            
        meta_type = soup.find('meta', {'name': 'employmentType'})
        if meta_type:
            meta_tags['employmentType'] = meta_type.get('content')
            
        meta_desc = soup.find('meta', {'name': 'description'})
        if meta_desc:
            meta_tags['description'] = meta_desc.get('content')
        
        # If we found any meta tags, return them
        if any(meta_tags.values()):
            return meta_tags
        
        # Final fallback: Try to find data in script tags
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string and 'datePosted' in script.string:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('datePosted'):
                        return {
                            'datePosted': data.get('datePosted'),
                            'employmentType': data.get('employmentType'),
                            'description': clean_fidelity_description(data.get('description', ''))
                        }
                except:
                    continue
                    
        return {}
        
    except Exception as e:
        print(f"⚠️ Error fetching details for {job_url[:50]}...: {str(e)}")
        return {}

def format_fidelity_job_data(job, metadata):
    """Format job data consistently"""
    # Extract job ID from externalPath or bulletFields
    job_id = extract_fidelity_job_id(job)
    
    # Format location nicely
    location = job.get('locationsText', 'N/A')
    if location and 'Locations' in location:
        location = location.replace('Locations', 'locations').strip()
    
    # Format date nicely
    date_posted = metadata.get('datePosted', job.get('postedOn', 'N/A'))
    formatted_date = format_fidelity_date(date_posted)
    
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": job_id,
        "location": location,
        "job_url": f"https://fmr.wd1.myworkdayjobs.com/en-US/FidelityCareers{job.get('externalPath', '')}",
        "date_posted": formatted_date,
        "employment_type": format_employment_type(metadata.get('employmentType', 'N/A')),
        "description": metadata.get('description', 'N/A')
    }

def extract_fidelity_job_id(job):
    """Extract job ID from various possible locations"""
    # Try multiple methods to extract job ID
    if job.get('bulletFields') and len(job['bulletFields']) > 0:
        return job['bulletFields'][0]
    
    external_path = job.get('externalPath', '')
    if external_path:
        # Extract ID from externalPath (usually last part after _)
        parts = external_path.split('_')
        if len(parts) > 1:
            return parts[-1]
    
    return 'N/A'

def parse_fidelity_date(date_str):
    """Parse various date formats Fidelity might use"""
    if not date_str or date_str == 'N/A':
        return None
        
    # Handle relative dates like "Posted Today", "Posted 2 days ago"
    if isinstance(date_str, str):
        date_str_lower = date_str.lower()
        if 'today' in date_str_lower:
            return datetime.now()
        elif 'yesterday' in date_str_lower:
            return datetime.now() - timedelta(days=1)
        elif 'days ago' in date_str_lower:
            try:
                days = int(date_str_lower.split()[1])
                return datetime.now() - timedelta(days=days)
            except:
                pass
    
    # Try ISO format
    try:
        return datetime.fromisoformat(date_str.replace('Z', ''))
    except:
        pass
    
    # Try Workday's format
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    except:
        pass
        
    return None

def parse_fidelity_posted_date(posted_on):
    """Parse the postedOn field from job object"""
    if not posted_on:
        return None
        
    # Handle "Posted Today", "Posted 2 days ago" format
    if 'Posted' in posted_on:
        if 'Today' in posted_on:
            return datetime.now().isoformat()
        elif 'Yesterday' in posted_on:
            return (datetime.now() - timedelta(days=1)).isoformat()
        elif 'days' in posted_on:
            try:
                days = int(''.join(filter(str.isdigit, posted_on)))
                return (datetime.now() - timedelta(days=days)).isoformat()
            except:
                pass
    
    return posted_on

def format_fidelity_date(date_str):
    """Format date for display"""
    if not date_str or date_str == 'N/A':
        return 'N/A'
    
    # If it's already a simple date string, return as is
    if isinstance(date_str, str) and len(date_str) <= 12 and 'T' not in date_str:
        return date_str
    
    parsed_date = parse_fidelity_date(date_str)
    if parsed_date:
        return parsed_date.strftime("%Y-%m-%d")
    
    return str(date_str)[:10]  # Truncate long strings

def format_employment_type(emp_type):
    """Format employment type nicely"""
    if not emp_type or emp_type == 'N/A':
        return 'N/A'
    
    # Common variations
    emp_type = emp_type.upper()
    if 'FULL' in emp_type:
        return 'Full Time'
    elif 'PART' in emp_type:
        return 'Part Time'
    elif 'CONTRACT' in emp_type:
        return 'Contract'
    elif 'INTERN' in emp_type:
        return 'Internship'
    elif 'TEMPORARY' in emp_type:
        return 'Temporary'
    
    return emp_type.title()

def clean_fidelity_description(desc):
    """Clean and truncate job description"""
    if not desc:
        return 'N/A'
    
    # Remove HTML tags and clean up
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    # Remove extra whitespace
    cleaned = ' '.join(cleaned.split())
    # Truncate to reasonable length
    return cleaned[:500] + '...' if len(cleaned) > 500 else cleaned
