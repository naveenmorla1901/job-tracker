import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_unhcr_jobs(roles, days=30):
    """Main function to retrieve UNHCR jobs structured by roles"""

    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://unhcr.wd3.myworkdayjobs.com/wday/cxs/unhcr/External/jobs"
        payload = {
            "appliedFacets": {"locationCountry": ["bc33aa3152ec42d4995f4791a106ed09"]},
            "searchText": target_role,
            "limit": 20,
            "offset": 0
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://unhcr.wd3.myworkdayjobs.com/External"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)

            for job in data.get('jobPostings', []):
                job_id = extract_unhcr_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_unhcr_job, job, cutoff_date): job
                    for job in jobs_to_process
                }

                results = []
                for future in concurrent.futures.as_completed(future_to_job):
                    result = future.result()
                    if result:
                        results.append(result)

            return sorted(results, key=lambda x: x['posting_date'], reverse=True)

        except Exception as e:
            print(f"Error fetching {target_role} jobs: {str(e)}")
            return []

    # Structure results by role
    structured_results = {}
    for role in roles:
        structured_results[role] = fetch_role_jobs(role)

    return structured_results

def process_unhcr_job(job, cutoff_date):
    try:
        job_url = f"https://unhcr.wd3.myworkdayjobs.com/en-US/External{job.get('externalPath', '')}"
        metadata = get_unhcr_job_details(job_url)

        if not metadata.get('datePosted'):
            return None

        post_date = parse_unhcr_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_unhcr_job_data(job, metadata)

    except Exception as e:
        print(f"Error processing job: {str(e)}")
    return None

def get_unhcr_job_details(job_url):
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        lang_requirements = []
        for li in soup.select('.job-details li'):
            if 'language' in li.text.lower():
                lang_requirements.append(li.text.strip())

        script = soup.find('script', {'type': 'application/ld+json'})
        metadata = {}
        if script:
            try:
                data = json.loads(script.string)
                metadata = {
                    'datePosted': data.get('datePosted'),
                    'employmentType': data.get('employmentType'),
                    'description': clean_description(data.get('description', '')),
                    'languages': ', '.join(lang_requirements) or 'English required'
                }
            except json.JSONDecodeError:
                pass

        return metadata

    except Exception as e:
        print(f"Error fetching details: {str(e)}")
        return {}

def format_unhcr_job_data(job, metadata):
    return {
        "position": job.get('title', 'N/A'),
        "job_id": extract_unhcr_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "posting_date": format_unhcr_date(metadata.get('datePosted')),
        "contract_type": metadata.get('employmentType', 'N/A'),
        "language_requirements": metadata.get('languages', 'English required'),
        "application_url": f"https://unhcr.wd3.myworkdayjobs.com/en-US/External{job.get('externalPath', '')}",
        "description": metadata.get('description', 'N/A')[:500] + "..."
    }

def extract_unhcr_job_id(job):
    try:
        return job['externalPath'].split('_')[-1].split('/')[-1]
    except:
        return job.get('bulletFields', ['N/A'])[0]

def parse_unhcr_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    except:
        return None

def format_unhcr_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
    except:
        return date_str

def clean_description(desc):
    return BeautifulSoup(desc, 'html.parser').get_text(separator=' ').strip()

# Example usage:
# if __name__ == "__main__":
#     unhcr_roles = [
#         "Protection Officer",
#         "Field Coordinator",
#         "Resettlement Expert",
#         "Emergency Response",
#         "Public Health",
#         "Legal Advisor",
#         "Community Services"
#     ]

#     jobs_data = get_unhcr_jobs(roles=unhcr_roles, days=30)
#     print(json.dumps(jobs_data, indent=2, ensure_ascii=False))