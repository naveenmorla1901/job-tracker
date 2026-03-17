import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_acxiomllc_jobs(roles, days=7):
    """Main function to retrieve Acxiom jobs structured by roles"""
    
    # ================= CONFIGURATION =================
    # IMPORTANT: You may need to update these values
    COMPANY = "acxiomllc"
    BASE_URL = f"https://{COMPANY}.wd5.myworkdayjobs.com/en-US/AcxiomUSA"
    API_URL = f"https://{COMPANY}.wd5.myworkdayjobs.com/wday/cxs/{COMPANY}/AcxiomUSA/jobs"
    REFERER_URL = f"https://{COMPANY}.wd5.myworkdayjobs.com/AcxiomUSA"

    # Facets - You'll likely need to update these IDs
    FACETS = {
        # Example facets - replace with actual IDs from browser inspection
        # "locationCountry": ["bc33aa3152ec42d4995f4791a106ed09"],  # US example
    }
    
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
            "Referer": REFERER_URL
        }

        try:
            response = requests.post(API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            # Deduplicate and filter jobs
            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)
            
            for job in data.get('jobPostings', []):
                job_id = extract_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            # Parallel processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_single_job, job, cutoff_date): job 
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

    def process_single_job(job, cutoff_date):
        try:
            job_url = f"{BASE_URL}{job.get('externalPath', '')}"
            metadata = get_job_details(job_url)
            
            if not metadata.get('datePosted'):
                return None
                
            post_date = parse_date(metadata['datePosted'])
            if post_date and post_date >= cutoff_date:
                return format_job_data(job, metadata)
                
        except Exception as e:
            print(f"Error processing job: {str(e)}")
        return None

    def get_job_details(job_url):
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
                        'description': clean_description(data.get('description', ''))
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
            print(f"Error fetching details: {str(e)}")
            return {}

    def format_job_data(job, metadata):
        return {
            "job_title": job.get('title', 'N/A'),
            "job_id": extract_job_id(job),
            "location": job.get('locationsText', 'N/A'),
            "job_url": f"{BASE_URL}{job.get('externalPath', '')}",
            "date_posted": format_date(metadata['datePosted']),
            "employment_type": metadata.get('employmentType', 'N/A'),
            "description": metadata.get('description', 'N/A')
        }

    def extract_job_id(job):
        try:
            return job['externalPath'].split('_')[-1].split('/')[-1]
        except:
            return job.get('bulletFields', ['N/A'])[0]

    def parse_date(date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
        except:
            try:
                return datetime.fromisoformat(date_str.replace('Z', ''))
            except:
                return None

    def format_date(date_str):
        try:
            return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
        except:
            return date_str

    def clean_description(desc):
        if not desc:
            return 'N/A'
        cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
        return ' '.join(cleaned.split()[:200]) + '...'

    # Structure results by role
    structured_results = {}
    for role in roles:
        structured_results[role] = fetch_role_jobs(role)
    
    return structured_results