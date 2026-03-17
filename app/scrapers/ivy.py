import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures
import re

def get_ivy_jobs(roles, days=7):
    """
    Main function to retrieve Ivy Tech jobs structured by roles
    
    Args:
        roles (list): List of job roles to search for
        days (int): Number of days to look back for jobs
    
    Returns:
        dict: Structured results with roles as keys and job lists as values
    """
    
    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://ivytech.wd1.myworkdayjobs.com/wday/cxs/ivytech/Ivy_Tech_Careers/jobs"
        
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
            "Referer": "https://ivytech.wd1.myworkdayjobs.com/Ivy_Tech_Careers"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for job in data.get('jobPostings', []):
                job_id = extract_ivytech_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            if not jobs_to_process:
                return []

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_ivytech_job, job, cutoff_date): job 
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

    def process_ivytech_job(job, cutoff_date):
        """Process individual job and fetch details"""
        try:
            job_url = f"https://ivytech.wd1.myworkdayjobs.com/en-US/Ivy_Tech_Careers{job.get('externalPath', '')}"
            metadata = get_ivytech_job_details(job_url)
            
            if not metadata.get('datePosted'):
                return None
                
            post_date = parse_ivytech_date(metadata['datePosted'])
            if post_date and post_date >= cutoff_date:
                return format_ivytech_job_data(job, metadata)
                
        except Exception as e:
            print(f"⚠️  Error processing job: {str(e)[:100]}")
        return None

    def get_ivytech_job_details(job_url):
        """Extract job details from job page"""
        try:
            response = requests.get(job_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Try JSON-LD first
            script = soup.find('script', {'type': 'application/ld+json'})
            if script:
                try:
                    data = json.loads(script.string)
                    return {
                        'datePosted': data.get('datePosted'),
                        'employmentType': data.get('employmentType'),
                        'description': clean_ivytech_description(data.get('description', ''))
                    }
                except json.JSONDecodeError:
                    pass
            
            # Try meta tags
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc:
                return {
                    'datePosted': extract_date_from_text(soup),
                    'employmentType': extract_employment_type(soup),
                    'description': meta_desc.get('content', 'N/A')
                }
            
            # Last resort - try to extract from page text
            return {
                'datePosted': extract_date_from_text(soup),
                'employmentType': 'N/A',
                'description': extract_description_from_page(soup)
            }
            
        except Exception as e:
            return {}

    def extract_date_from_text(soup):
        """Extract date from page text when meta tags are missing"""
        text = soup.get_text()
        patterns = [
            r'Posted[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Date[:\s]+(\d{4}-\d{2}-\d{2})',
            r'Published[:\s]+(\d{1,2}\s+\w+\s+\d{4})'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def extract_employment_type(soup):
        """Extract employment type from page"""
        text = soup.get_text()
        types = ['Full Time', 'Part Time', 'Adjunct', 'Contract', 'Temporary']
        for emp_type in types:
            if emp_type.lower() in text.lower():
                return emp_type
        return 'N/A'

    def extract_description_from_page(soup):
        """Extract description from page content"""
        desc_selectors = [
            'div.job-description',
            'div.description',
            'section[aria-label="Job Description"]',
            'div[data-automation-id="jobPostingDescription"]'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)[:500] + '...'
        
        paragraphs = soup.find_all('p')
        if paragraphs:
            return ' '.join([p.get_text() for p in paragraphs[:3]])[:500] + '...'
        
        return 'Description not available'

    def format_ivytech_job_data(job, metadata):
        """Format job data into standardized structure"""
        job_title = job.get('title', 'N/A')
        job_id = extract_ivytech_job_id(job)
        location = job.get('locationsText', 'N/A')
        
        if location != 'N/A' and 'locations' in location.lower():
            location = extract_primary_location(location)
        
        return {
            "job_title": job_title,
            "job_id": job_id,
            "location": location,
            "job_url": f"https://ivytech.wd1.myworkdayjobs.com/en-US/Ivy_Tech_Careers{job.get('externalPath', '')}",
            "date_posted": format_ivytech_date(metadata['datePosted']) if metadata.get('datePosted') else 'N/A',
            "employment_type": metadata.get('employmentType', 'N/A'),
            "description": metadata.get('description', 'N/A'),
            "department": extract_department(job_title)
        }

    def extract_primary_location(location_text):
        """Extract primary location from multi-location text"""
        if 'locations' in location_text.lower():
            parts = location_text.split(',')
            if parts:
                return parts[0].strip()
        return location_text

    def extract_department(job_title):
        """Extract department from job title"""
        dept_keywords = {
            'Faculty': 'Academic',
            'Professor': 'Academic',
            'Instructor': 'Academic',
            'Adjunct': 'Academic',
            'Dean': 'Administration',
            'Director': 'Administration',
            'Coordinator': 'Administration',
            'IT': 'Information Technology',
            'Technology': 'Information Technology',
            'Nurse': 'Healthcare',
            'Health': 'Healthcare',
            'Student': 'Student Services',
            'Advisor': 'Student Services'
        }
        
        for keyword, dept in dept_keywords.items():
            if keyword.lower() in job_title.lower():
                return dept
        return 'Other'

    def extract_ivytech_job_id(job):
        """Extract job ID from job data"""
        if job.get('externalPath'):
            parts = job['externalPath'].split('_')
            if len(parts) > 1:
                return parts[-1].split('/')[-1]
        
        if job.get('bulletFields'):
            return job['bulletFields'][0]
        
        title = job.get('title', '')
        id_match = re.search(r'([A-Z]{2,3}-\d{4,})', title)
        if id_match:
            return id_match.group(1)
        
        return 'N/A'

    def parse_ivytech_date(date_str):
        """Parse date from various formats"""
        if not date_str:
            return None
            
        formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%B %d, %Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None

    def format_ivytech_date(date_str):
        """Format date to YYYY-MM-DD"""
        parsed = parse_ivytech_date(date_str)
        if parsed:
            return parsed.strftime("%Y-%m-%d")
        return date_str

    def clean_ivytech_description(desc):
        """Clean HTML description"""
        if not desc:
            return 'N/A'
        cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
        return ' '.join(cleaned.split()[:250]) + '...'

    # Main execution
    structured_results = {}
    for role in roles:
        structured_results[role] = fetch_role_jobs(role)
    
    return structured_results

