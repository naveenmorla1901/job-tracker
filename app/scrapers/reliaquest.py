import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_reliaquest_jobs(roles, days=40):
    """Main function to retrieve ReliaQuest jobs structured by roles"""

    def fetch_role_jobs(target_role):
        """Fetch jobs for a single role"""
        base_url = "https://reliaquest.wd5.myworkdayjobs.com/wday/cxs/reliaquest/Campus_Recruiting/jobs"

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
            "Referer": "https://reliaquest.wd5.myworkdayjobs.com/Campus_Recruiting"
        }

        try:
            response = requests.post(base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

            seen_ids = set()
            jobs_to_process = []
            cutoff_date = datetime.now() - timedelta(days=days)

            for job in data.get('jobPostings', []):
                job_id = extract_reliaquest_id(job)
                if job_id and job_id not in seen_ids:
                    seen_ids.add(job_id)
                    jobs_to_process.append(job)

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_job = {
                    executor.submit(process_reliaquest_job, job, cutoff_date): job
                    for job in jobs_to_process
                }

                results = []
                for future in concurrent.futures.as_completed(future_to_job):
                    result = future.result()
                    if result:
                        results.append(result)

            return sorted(results, key=lambda x: x['posted'], reverse=True)

        except Exception as e:
            print(f"Error fetching {target_role} jobs: {str(e)}")
            return []

    # Structure results by role
    structured_results = {}
    for role in roles:
        structured_results[role] = fetch_role_jobs(role)

    return structured_results

def process_reliaquest_job(job, cutoff_date):
    try:
        job_url = f"https://reliaquest.wd5.myworkdayjobs.com/en-US/Campus_Recruiting{job.get('externalPath', '')}"
        metadata = get_reliaquest_details(job_url)

        if not metadata.get('datePosted'):
            return None

        post_date = parse_reliaquest_date(metadata['datePosted'])
        if post_date and post_date >= cutoff_date:
            return format_reliaquest_data(job, metadata)

    except Exception as e:
        print(f"Error processing job: {str(e)}")
    return None

def get_reliaquest_details(job_url):
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
                    'description': clean_reliaquest_desc(data.get('description', ''))
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

def format_reliaquest_data(job, metadata):
    return {
        "position": job.get('title', 'N/A'),
        "req_id": extract_reliaquest_id(job),
        "location": job.get('locationsText', 'N/A'),
        "url": f"https://reliaquest.wd5.myworkdayjobs.com/en-US/Campus_Recruiting{job.get('externalPath', '')}",
        "posted": format_reliaquest_date(metadata['datePosted']),
        "type": metadata.get('employmentType', 'N/A'),
        "overview": metadata.get('description', 'N/A')
    }

def extract_reliaquest_id(job):
    try:
        return job['externalPath'].split('/')[-1].split('_')[-1]
    except:
        return job.get('bulletFields', ['N/A'])[0]

def parse_reliaquest_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z")
    except:
        try:
            return datetime.fromisoformat(date_str.replace('Z', ''))
        except:
            return None

def format_reliaquest_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%Y-%m-%d")
    except:
        return date_str

def clean_reliaquest_desc(desc):
    return ' '.join(BeautifulSoup(desc, 'html.parser').get_text().split()[:150]) + '...'

# Example usage:
# if __name__ == "__main__":
#     roles_to_check = [
#         "data scientist",
#         "bussiness",
#         "Cybersecurity Intern",
#         "Entry Level Engineer",
#         "Graduate Program",
#         "Junior Developer"
#     ]

#     jobs_data = get_reliaquest_jobs(roles=roles_to_check, days=40)
#     print(json.dumps(jobs_data, indent=2, ensure_ascii=False))