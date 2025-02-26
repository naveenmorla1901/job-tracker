"""
Base scraper class with common functionality
"""
import requests
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class BaseScraper:
    """Base scraper class that provides common functionality"""
    
    def __init__(self, company_name):
        self.company_name = company_name
        
    def get_recent_date(self, days_ago):
        """Get date string for a number of days ago"""
        date = datetime.now() - timedelta(days=days_ago)
        return date.strftime("%Y-%m-%d")
    
    def format_job(self, job_data, role=""):
        """Format job data to common structure"""
        # Child classes should implement this method
        raise NotImplementedError("Child classes must implement format_job method")
    
    def scrape_jobs(self, roles, days):
        """Scrape jobs for given roles and time period"""
        # Child classes should implement this method
        raise NotImplementedError("Child classes must implement scrape_jobs method")
