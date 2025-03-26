import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_az_jobs(roles, days=7):
    """Main function to retrieve AstraZeneca jobs structured by roles"""

    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://astrazeneca.wd3.myworkdayjobs.com/wday/cxs/astrazeneca/Careers/jobs"
        payload = {
            "searchText": target_role,
            "limit": 20,
            "offset": 0,
            "appliedFacets": []
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Referer": "https://astrazeneca.wd3.myworkdayjobs.com/Careers"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)

            for job in data.get('jobPostings', []):
                job_id = extract_az_job_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_az_job, job, cutoff_date): job
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

def process_az_job(job, cutoff_date):
    try:
        job_url = f"https://astrazeneca.wd3.myworkdayjobs.com/en-US/Careers{job.get('externalPath', '')}"
        metadata = get_az_job_details(job_url)

        if not metadata.get('datePosted'):
            return None

        post_date = parse_az_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_az_job_data(job, metadata)

    except Exception as e:
        print(f"Error processing AZ job: {str(e)}")
    return None

def get_az_job_details(job_url):
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
                    'description': clean_az_description(data.get('description', ''))
                }
            except json.JSONDecodeError:
                pass

        # Meta tag fallback
        return {
            'datePosted': (soup.find('meta', {'property': 'og:article:published_time'}) or {}).get('content'),
            'employmentType': (soup.find('meta', {'name': 'employmentType'}) or {}).get('content'),
            'description': (soup.find('meta', {'name': 'description'}) or {}).get('content')
        }

    except Exception as e:
        print(f"Error fetching AZ details: {str(e)}")
        return {}

def format_az_job_data(job, metadata):
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_az_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"https://astrazeneca.wd3.myworkdayjobs.com/en-US/Careers{job.get('externalPath', '')}",
        "date_posted": format_az_date(metadata['datePosted']),
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }

def extract_az_job_id(job):
    try:
        return job['externalPath'].split('_')[-1].split('/')[-1]
    except:
        return job.get('bulletFields', ['N/A'])[0]

def parse_az_date(date_str):
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    return None

def format_az_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
    except:
        return date_str

def clean_az_description(desc):
    if not desc:
        return 'N/A'
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    return ' '.join(cleaned.split()[:250]) + '...'

# Example usage:
# if __name__ == "__main__":
#     pharma_roles = [
#         "Clinical Research Associate",
#         "Data Scientist",
#         "Medical Affairs",
#         "Regulatory Affairs",
#         "Biostatistician",
#         "Pharmacovigilance"
#     ]

#     az_jobs = get_az_jobs(roles=pharma_roles, days=7)
#     print(json.dumps(az_jobs, indent=2, ensure_ascii=False))