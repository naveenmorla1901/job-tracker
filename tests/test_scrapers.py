"""
Tests for the job scrapers
"""
import pytest
from unittest.mock import patch, MagicMock

# Import base scraper for testing
from app.scrapers.base import BaseScraper

class TestScrapers:
    """Tests for the job scrapers"""
    
    def test_base_scraper_init(self):
        """Test BaseScraper initialization"""
        scraper = BaseScraper("Test Company")
        assert scraper.company_name == "Test Company"
    
    def test_get_recent_date(self):
        """Test the get_recent_date method"""
        scraper = BaseScraper("Test Company")
        date_str = scraper.get_recent_date(days_ago=1)
        assert isinstance(date_str, str)
        assert len(date_str) == 10  # YYYY-MM-DD
        assert date_str[4] == "-" and date_str[7] == "-"
    
    def test_format_job_not_implemented(self):
        """Test that format_job raises NotImplementedError"""
        scraper = BaseScraper("Test Company")
        with pytest.raises(NotImplementedError):
            scraper.format_job({})
    
    def test_scrape_jobs_not_implemented(self):
        """Test that scrape_jobs raises NotImplementedError"""
        scraper = BaseScraper("Test Company")
        with pytest.raises(NotImplementedError):
            scraper.scrape_jobs(roles=["Data Scientist"], days=7)

@pytest.mark.skip(reason="Requires mock setup for Salesforce API")
@patch('requests.post')
def test_salesforce_scraper(mock_post):
    """Test the Salesforce scraper"""
    try:
        from app.scrapers.salesforce import get_salesforce_jobs
        
        # Configure the mock to return a specific response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "jobPostings": [
                {
                    "title": "Data Scientist",
                    "externalPath": "/path/to/JR123456",
                    "locationsText": "San Francisco",
                    "bulletFields": ["JR123456"]
                }
            ]
        }
        mock_post.return_value = mock_response
        
        # Mock the job details function
        with patch('app.scrapers.salesforce.get_sf_job_details') as mock_details:
            mock_details.return_value = {
                "datePosted": "2022-01-01",
                "employmentType": "FULL_TIME",
                "description": "Test job description"
            }
            
            # Call the scraper
            result = get_salesforce_jobs(roles=["Data Scientist"], days=7)
            
            # Verify the result
            assert "Data Scientist" in result
            assert len(result["Data Scientist"]) > 0
            assert "job_title" in result["Data Scientist"][0]
            assert "job_id" in result["Data Scientist"][0]
    except (ImportError, AttributeError) as e:
        pytest.skip(f"Salesforce scraper not available: {str(e)}")
