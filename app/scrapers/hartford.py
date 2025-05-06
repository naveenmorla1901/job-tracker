import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_hartford_jobs(roles, days=7):
    base_url = "https://thehartford.wd5.myworkdayjobs.com/wday/cxs/thehartford/Careers_External/jobs"

    payload = {
        "appliedFacets": {
            "locationCountry": ["bc33aa3152ec42d4995f4791a106ed09"]
        },
        "searchText": roles,
        "limit": 20,
        "offset": 0
    }

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://thehartford.wd5.myworkdayjobs.com/Careers_External"
    }

    try:
        response = requests.post(base_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

        seen_ids = set()
        jobs_to_process = []
        cutoff_date = datetime.now() - timedelta(days=days)

        for job in data.get('jobPostings', []):
            job_id = extract_hartford_job_id(job)
            if job_id and job_id not in seen_ids:
                seen_ids.add(job_id)
                jobs_to_process.append(job)

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_job = {
                executor.submit(process_hartford_job, job, cutoff_date): job
                for job in jobs_to_process
            }

            results = []
            for future in concurrent.futures.as_completed(future_to_job):
                result = future.result()
                if result:
                    results.append(result)

        print_hartford_output(results, roles, days)

    except Exception as e:
        print(f"Error fetching jobs: {str(e)}")

def process_hartford_job(job, cutoff_date):
    try:
        job_url = f"https://thehartford.wd5.myworkdayjobs.com/en-US/Careers_External{job.get('externalPath', '')}"
        metadata = get_hartford_job_details(job_url)

        if not metadata.get('datePosted'):
            return None

        post_date = parse_hartford_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_hartford_job_data(job, metadata)

    except Exception as e:
        print(f"Error processing job: {str(e)}")
    return None

def get_hartford_job_details(job_url):
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
                    'description': clean_hartford_description(data.get('description', ''))
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

def format_hartford_job_data(job, metadata):
    return {
        "job_title": job.get('title', 'N/A'),
        "job_id": extract_hartford_job_id(job),
        "location": job.get('locationsText', 'N/A'),
        "job_url": f"https://thehartford.wd5.myworkdayjobs.com/en-US/Careers_External{job.get('externalPath', '')}",
        "date_posted": format_hartford_date(metadata['datePosted']),
        "employment_type": metadata.get('employmentType', 'N/A'),
        "description": metadata.get('description', 'N/A')
    }

def extract_hartford_job_id(job):
    try:
        return job['externalPath'].split('_')[-1].split('/')[-1]
    except:
        return job.get('bulletFields', ['N/A'])[0]

def parse_hartford_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    except:
        try:
            return datetime.fromisoformat(date_str.replace('Z', ''))
        except:
            return None

def format_hartford_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
    except:
        return date_str

def clean_hartford_description(desc):
    if not desc:
        return 'N/A'
    cleaned = BeautifulSoup(desc, 'html.parser').get_text(separator=' ')
    return ' '.join(cleaned.split()[:200]) + '...'

def print_hartford_output(results, roles, days):
    if not results:
        print(f"\nNo {roles} jobs found at The Hartford in last {days} days :cite[1]")
        return

    print(f"\n{len(results)} RECENT {roles} JOBS AT THE HARTFORD (LAST {days} DAYS)")
    print("=" * 70)
    print(json.dumps(sorted(results, key=lambda x: x['date_posted'], reverse=True), indent=2, ensure_ascii=False))

# The Hartford specific roles based on their career focus areas :cite[1]:cite[3]
# hartford_roles = [
#     "Data Scientist",
#     "Cyber Security Analyst",
#     "Claims Specialist",
#     "Actuarial Analyst",
#     "Customer Service Representative",
#     "Underwriting Associate"
# ]

# for role in hartford_roles:
#     fetch_hartford_jobs(role, days=7)
#     print("\n" + "-"*80 + "\n")