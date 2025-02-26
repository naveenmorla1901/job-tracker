import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_sunlife_jobs(roles, days=7):
    """Main function to retrieve SunLife jobs structured by roles"""

    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://sunlife.wd3.myworkdayjobs.com/wday/cxs/sunlife/Experienced/jobs"
        payload = {
            "appliedFacets": {"Location_Country": ["bc33aa3152ec42d4995f4791a106ed09"]},
            "searchText": target_role,
            "limit": 20,
            "offset": 0
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://sunlife.wd3.myworkdayjobs.com/Experienced"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            job_postings = data.get('jobPostings', [])

            # Remove duplicates and prepare for processing
            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)

            for job in job_postings:
                job_id = job.get('bulletFields', [''])[0]
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            # Parallel processing of job details
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_job, job, cutoff_date): job
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

    def process_job(job, cutoff_date):
        """Process individual job details with date filtering"""
        try:
            job_url = f"https://sunlife.wd3.myworkdayjobs.com/en-US/Experienced{job.get('externalPath', '')}"
            metadata = get_job_details(job_url)

            # Date filtering
            date_str = metadata.get('datePosted')
            if not date_str:
                return None

            try:
                post_date = datetime.strptime(date_str, "%Y-%m-%d")
            except:
                return None

            if post_date >= cutoff_date:
                return {
                    "job_title": job.get('title', 'N/A'),
                    "job_id": job.get('bulletFields', ['N/A'])[0],
                    "location": job.get('locationsText', 'N/A'),
                    "job_url": job_url,
                    "date_posted": post_date.strftime("%Y-%m-%d"),
                    "employment_type": metadata.get('employmentType', 'N/A'),
                    "description": metadata.get('description', 'N/A')[:500] + "..."
                }
            return None

        except Exception as e:
            print(f"Error processing job: {str(e)}")
            return None

    # Structure results by role
    structured_results = {}
    for role in roles:
        structured_results[role] = fetch_role_jobs(role)

    return structured_results

# Helper function for job details
def get_job_details(job_url):
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # JSON-LD data extraction
        script = soup.find('script', {'type': 'application/ld+json'})
        if script:
            try:
                data = json.loads(script.string)
                return {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': BeautifulSoup(data.get('description', ''), 'html.parser').get_text(separator='\n').strip()
                }
            except json.JSONDecodeError:
                pass

        # Meta tag fallback
        return {
            'datePosted': (soup.find('meta', {'property': 'og:article:published_time'}) or {}).get('content'),
            'employmentType': (soup.find('meta', {'name': 'employmentType'}) or {}).get('content'),
            'description': (soup.find('meta', {'name': 'description'}) or {}).get('content', '')[:500] + "..."
        }

    except Exception as e:
        print(f"Error fetching details for {job_url}: {str(e)}")
        return {}

# Example usage:
# if __name__ == "__main__":
#     roles_to_check = ["Machine Learning", "Data Scientist"]
#     jobs_data = get_sunlife_jobs(roles=roles_to_check, days=30)

#     # Print structured results
#     print(json.dumps(jobs_data, indent=2, ensure_ascii=False))