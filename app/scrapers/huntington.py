import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import concurrent.futures

def get_huntington_jobs(roles, days=7):
    """Main function to retrieve Huntington jobs structured by roles"""

    def fetch_role_jobs(target_role, cutoff_date):
        """Fetch and process jobs for a single role"""
        url = "https://huntington.wd12.myworkdayjobs.com/wday/cxs/huntington/HNBcareers/jobs"
        payload = {
            "appliedFacets": {"timeType": ["935efb19629601430173e15b13307200"]},
            "searchText": target_role
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Referer": "https://huntington.wd12.myworkdayjobs.com/HNBcareers"
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            job_postings = data.get('jobPostings', [])

            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = []
                for job in job_postings:
                    futures.append(executor.submit(process_job, job, cutoff_date))

                results = []
                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if result:
                        results.append(result)

            return sorted(results, key=lambda x: x['date_posted'], reverse=True)

        except Exception as e:
            print(f"Error fetching {target_role} jobs: {str(e)}")
            return []

    def process_job(job, cutoff_date):
        """Process individual job posting with date filtering"""
        try:
            job_title = job.get('title', 'Title Not Available')
            job_id = job.get('bulletFields', ['ID Not Available'])[0]
            location = job.get('locationsText', 'Location Not Available')

            # Get job URL
            try:
                job_url = get_job_url(job)
            except:
                job_url = "URL Not Available"

            # Fetch details with error handling
            try:
                date_posted, employment_type, seo_title, seo_description, address_location = get_job_details(job_url, location)
            except:
                return None

            # Parse and check date
            post_date = parse_date(date_posted)
            if not post_date or post_date < cutoff_date:
                return None

            return {
                "job_title": job_title,
                "job_id": job_id,
                "location": address_location or location,
                "job_url": job_url,
                "date_posted": format_date(post_date),
                "employment_type": employment_type,
                "description": seo_description
            }

        except Exception as e:
            print(f"Error processing job: {str(e)}")
            return None

    # Main logic
    structured_results = {}
    cutoff_date = datetime.now() - timedelta(days=days)

    for role in roles:
        structured_results[role] = fetch_role_jobs(role, cutoff_date)

    return structured_results

# Helper functions
def get_job_url(job):
    title = job.get('title', 'N/A').replace(' ', '-')
    job_id = job.get('bulletFields', ['N/A'])[0]
    return f"https://huntington.wd12.myworkdayjobs.com/en-US/HNBcareers/job/{title}_{job_id}"

def get_job_details(job_url, location):
    try:
        response = requests.get(job_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get canonical URL
        link_tag = soup.find('link', {'rel': 'canonical'})
        if link_tag:
            job_url = link_tag['href']

        # Parse JSON-LD data
        script_tag = soup.find('script', {'type': 'application/ld+json'})
        if not script_tag:
            return None, None, None, None, location

        data = json.loads(script_tag.string)
        return (
            data.get('datePosted'),
            data.get('employmentType', 'N/A'),
            data.get('title', 'N/A'),
            clean_description(data.get('description', 'N/A')),
            data.get('jobLocation', {}).get('address', {}).get('addressLocality', location)
        )
    except:
        return None, None, None, None, location

def parse_date(date_str):
    formats = [
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%d",
        "%m/%d/%Y"
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    return None

def format_date(date_obj):
    return date_obj.strftime("%Y-%m-%d")

def clean_description(desc):
    return ' '.join(BeautifulSoup(desc, 'html.parser').get_text().split()[:150]) + '...'

# Example usage
# if __name__ == "__main__":
#     roles = ["Machine Learning Engineer", "Data Scientist", "AI Scientist"]
#     results = get_huntington_jobs(roles=roles, days=14)
#     print(json.dumps(results, indent=2, ensure_ascii=False))