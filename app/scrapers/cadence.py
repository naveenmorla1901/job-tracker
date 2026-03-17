import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_cadence_jobs(roles, days=7):
    """Main function to retrieve Cadence jobs structured by roles"""
    
    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://cadence.wd1.myworkdayjobs.com/wday/cxs/cadence/External_Careers/jobs"

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
            "Referer": "https://cadence.wd1.myworkdayjobs.com/External_Careers"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)

            for job in data.get('jobPostings', []):
                job_id = extract_cadence_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_cadence_job, job, cutoff_date): job
                    for job in jobs_to_process
                }

                results = []
                for future in concurrent.futures.as_completed(future_to_job):
                    result = future.result()
                    if result:
                        results.append(result)

            return sorted(results, key=lambda x: x['date_posted'], reverse=True)

        except Exception as e:
            print(f"Error fetching Cadence {target_role} jobs: {str(e)}")
            return []

    def process_cadence_job(job, cutoff_date):
        """Process individual Cadence job"""
        try:
            job_url = f"https://cadence.wd1.myworkdayjobs.com/en-US/External_Careers{job.get('externalPath', '')}"
            metadata = get_cadence_job_details(job_url)

            if not metadata.get('datePosted'):
                return None

            post_date = parse_cadence_date(metadata['datePosted'])
            if post_date and post_date >= cutoff_date:
                return format_cadence_job_data(job, metadata)

        except Exception as e:
            print(f"Error processing Cadence job: {str(e)}")
        return None

    def get_cadence_job_details(job_url):
        """Fetch detailed job information from job page"""
        try:
            response = requests.get(job_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            script = soup.find('script', {'type': 'application/ld+json'})
            if script:
                try:
                    data = json.loads(script.string)
                    return {
                        'datePosted': data.get('datePosted'),
                        'employmentType': data.get('employmentType'),
                        'description': clean_cadence_description(data.get('description', ''))
                    }
                except json.JSONDecodeError:
                    pass

            return {
                'datePosted': (soup.find('meta', {'property': 'og:article:published_time'}) or {}).get('content'),
                'employmentType': (soup.find('meta', {'name': 'employmentType'}) or {}).get('content'),
                'description': (soup.find('meta', {'name': 'description'}) or {}).get('content')
            }

        except Exception as e:
            print(f"Error fetching details: {str(e)}")
            return {}

    def format_cadence_job_data(job, metadata):
        """Format job data into consistent structure"""
        return {
            "job_title": job.get('title', 'N/A'),
            "job_id": extract_cadence_job_id(job),
            "location": job.get('locationsText', 'N/A'),
            "job_url": f"https://cadence.wd1.myworkdayjobs.com/en-US/External_Careers{job.get('externalPath', '')}",
            "date_posted": format_cadence_date(metadata.get('datePosted', 'N/A')),
            "employment_type": metadata.get('employmentType', 'N/A'),
            "description": metadata.get('description', 'N/A')
        }

    def extract_cadence_job_id(job):
        """Extract job ID from job data"""
        try:
            return job['externalPath'].split('_')[-1].split('/')[-1]
        except:
            return job.get('bulletFields', ['N/A'])[0]

    def parse_cadence_date(date_str):
        """Parse various date formats"""
        try:
            return datetime.fromisoformat(date_str.replace('Z', ''))
        except:
            try:
                return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
            except:
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d")
                except:
                    return None

    def format_cadence_date(date_str):
        """Format date to YYYY-MM-DD"""
        try:
            dt = parse_cadence_date(date_str)
            return dt.strftime("%Y-%m-%d") if dt else date_str
        except:
            return date_str

    def clean_cadence_description(desc):
        """Clean and truncate job description"""
        if not desc:
            return 'N/A'
        cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
        return ' '.join(cleaned.split()[:200]) + '...'

    # Structure results by role
    structured_results = {}
    for role in roles:
        print(f"Fetching {role} jobs from Cadence...")
        structured_results[role] = fetch_role_jobs(role)
    
    return structured_results
