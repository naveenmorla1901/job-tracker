import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures
import re

def get_intel_jobs(roles, days=7):
    """Main function to retrieve Intel jobs structured by roles"""
    
    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://intel.wd1.myworkdayjobs.com/wday/cxs/intel/External/jobs"
        
        payload = {
            "searchText": target_role,
            "limit": 20,
            "offset": 0
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://intel.wd1.myworkdayjobs.com/External"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            job_postings = data.get('jobPostings', [])
            
            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for job in job_postings:
                job_id = extract_intel_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                future_to_job = {
                    executor.submit(process_intel_job, job, cutoff_date): job 
                    for job in jobs_to_process
                }
                
                results = []
                for future in concurrent.futures.as_completed(future_to_job):
                    result = future.result()
                    if result:
                        results.append(result)
            
            return sorted(results, key=lambda x: x['date_posted'], reverse=True)

        except Exception as e:
            print(f"Error fetching Intel jobs: {str(e)}")
            return []

    def process_intel_job(job, cutoff_date):
        """Process individual Intel job"""
        try:
            job_url = construct_intel_job_url(job)
            metadata = get_intel_job_details(job_url)
            
            if metadata.get('datePosted'):
                post_date = parse_intel_date(metadata['datePosted'])
                if post_date and post_date >= cutoff_date:
                    return format_intel_job_data(job, metadata, job_url)
                
        except Exception as e:
            print(f"Error processing Intel job: {str(e)}")
        return None

    def construct_intel_job_url(job):
        """Construct proper Intel job URL"""
        try:
            external_path = job.get('externalPath', '')
            if external_path:
                return f"https://intel.wd1.myworkdayjobs.com/en-US/External{external_path}"
            
            title = job.get('title', '')
            job_id = job.get('bulletFields', [''])[0]
            clean_title = re.sub(r'[^\w\s-]', '', title).replace(' ', '-')
            
            return f"https://intel.wd1.myworkdayjobs.com/en-US/External/job/{clean_title}_{job_id}"
        except:
            return "URL not available"

    def get_intel_job_details(job_url):
        """Extract job details from the job page"""
        try:
            response = requests.get(job_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            scripts = soup.find_all('script', {'type': 'application/ld+json'})
            
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    
                    if isinstance(data, dict):
                        if data.get('@type') == 'JobPosting':
                            return extract_job_data_from_jsonld(data)
                    elif isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and item.get('@type') == 'JobPosting':
                                return extract_job_data_from_jsonld(item)
                except:
                    continue
            
            return extract_job_data_from_page(soup)
            
        except Exception as e:
            print(f"Error fetching Intel details: {str(e)}")
            return {}

    def extract_job_data_from_jsonld(data):
        """Extract relevant data from JSON-LD"""
        return {
            'datePosted': data.get('datePosted'),
            'employmentType': data.get('employmentType'),
            'description': clean_description(data.get('description', ''))
        }

    def extract_job_data_from_page(soup):
        """Extract job data from page HTML if JSON-LD not available"""
        date_posted = None
        date_patterns = [
            r'posted (\d+) days? ago',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\w+ \d{1,2}, \d{4})'
        ]
        
        page_text = soup.get_text().lower()
        for pattern in date_patterns:
            match = re.search(pattern, page_text)
            if match:
                date_posted = match.group(1)
                break
        
        employment_type = None
        if 'full-time' in page_text or 'full time' in page_text:
            employment_type = 'FULL_TIME'
        elif 'part-time' in page_text or 'part time' in page_text:
            employment_type = 'PART_TIME'
        
        description = None
        desc_elem = soup.find('div', {'class': re.compile(r'description|job-details', re.I)})
        if desc_elem:
            description = clean_description(desc_elem.get_text())
        
        return {
            'datePosted': date_posted,
            'employmentType': employment_type,
            'description': description
        }

    def format_intel_job_data(job, metadata, job_url):
        """Format job data for output"""
        location = job.get('locationsText', 'N/A')
        location = location.replace('United States of America', 'USA')
        
        return {
            "job_title": job.get('title', 'N/A'),
            "job_id": extract_intel_job_id(job),
            "location": location,
            "job_url": job_url,
            "date_posted": format_intel_date(metadata.get('datePosted')),
            "employment_type": metadata.get('employmentType', 'N/A'),
            "description": metadata.get('description', 'N/A')
        }

    def extract_intel_job_id(job):
        """Extract job ID from job object"""
        try:
            if job.get('bulletFields'):
                return job['bulletFields'][0]
            
            if job.get('externalPath'):
                path = job['externalPath']
                jr_match = re.search(r'(JR\d+)', path)
                if jr_match:
                    return jr_match.group(1)
                
                num_match = re.search(r'(\d+)(?:-\d+)?$', path)
                if num_match:
                    return num_match.group(1)
            
            return 'N/A'
        except:
            return 'N/A'

    def parse_intel_date(date_str):
        """Parse various date formats"""
        if not date_str or date_str == 'N/A':
            return None
        
        if isinstance(date_str, str):
            date_str_lower = date_str.lower()
            if 'today' in date_str_lower:
                return datetime.now()
            elif 'yesterday' in date_str_lower:
                return datetime.now() - timedelta(days=1)
            
            days_ago_match = re.search(r'(\d+)\s+days?\s+ago', date_str_lower)
            if days_ago_match:
                days = int(days_ago_match.group(1))
                return datetime.now() - timedelta(days=days)
        
        date_formats = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d",
            "%b %d, %Y",
            "%B %d, %Y",
            "%d %b %Y",
            "%d %B %Y"
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(str(date_str), fmt)
            except ValueError:
                continue
        
        return None

    def format_intel_date(date_str):
        """Format date to YYYY-MM-DD"""
        if not date_str or date_str == 'N/A':
            return 'N/A'
        
        parsed_date = parse_intel_date(date_str)
        if parsed_date:
            return parsed_date.strftime("%Y-%m-%d")
        
        return str(date_str)

    def clean_description(desc):
        """Clean HTML from description and truncate"""
        if not desc:
            return 'N/A'
        
        cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
        cleaned = ' '.join(cleaned.split())
        
        if len(cleaned) > 500:
            cleaned = cleaned[:500] + '...'
        
        return cleaned

    # Main execution
    structured_results = {}
    for role in roles:
        structured_results[role] = fetch_role_jobs(role)
    
    return structured_results

