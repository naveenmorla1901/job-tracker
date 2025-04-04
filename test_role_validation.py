#!/usr/bin/env python
"""
Utility script to test the role validation functionality.
"""
import os
import sys
import json
import logging
import argparse
from pprint import pprint
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(description="Test the role validation functionality")
    parser.add_argument("--scraper", "-s", type=str, help="Specific scraper to test")
    parser.add_argument("--roles", "-r", type=str, nargs="+", help="Roles to test")
    parser.add_argument("--days", "-d", type=int, default=3, help="Number of days to look back")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    # Default roles to test
    if not args.roles:
        args.roles = [
            "Data Scientist",
            "Machine Learning Engineer",
            "AI Engineer",
            "NLP Engineer",
            "Computer Vision Engineer"
        ]
    
    logger.info(f"Testing with roles: {args.roles}")
    logger.info(f"Looking back {args.days} days")
    
    # Import the role validation utilities
    try:
        from app.scrapers.role_utils import (
            is_valid_role, normalize_role, validate_job_roles, 
            filter_jobs_by_role, filter_roles
        )
        
        # Test basic functions
        logger.info("Testing role validation functions...")
        
        # Test normalize_role
        test_roles = [
            "Data Scientist",
            "MACHINE LEARNING ENGINEER",
            "AI & Machine Learning Engineer",
            "Software Engineer (Python)",
            "O9 Technical Architect"
        ]
        
        logger.info("Testing normalize_role:")
        for role in test_roles:
            normalized = normalize_role(role)
            logger.info(f"  {role} -> {normalized}")
        
        # Test is_valid_role
        logger.info("\nTesting is_valid_role:")
        for role in test_roles:
            valid = is_valid_role(role, args.roles)
            logger.info(f"  {role} -> {'Valid' if valid else 'Invalid'}")
        
        # If a specific scraper was provided, test it
        if args.scraper:
            logger.info(f"\nTesting scraper: {args.scraper}")
            try:
                # Import the specific scraper
                module_name = f"app.scrapers.{args.scraper}"
                function_name = f"get_{args.scraper}_jobs"
                
                module = __import__(module_name, fromlist=[function_name])
                scraper_func = getattr(module, function_name)
                
                # Run the scraper
                logger.info(f"Running {function_name}...")
                results = scraper_func(args.roles, days=args.days)
                
                # Count original jobs
                original_count = 0
                for role, jobs in results.items():
                    original_count += len(jobs)
                
                logger.info(f"Original results: {len(results)} roles, {original_count} jobs")
                
                # Apply role filtering
                filtered_results = filter_roles(results, args.roles)
                
                # For each role, filter the jobs as well
                filtered_job_count = 0
                for role, jobs in filtered_results.items():
                    filtered_jobs = filter_jobs_by_role(jobs, args.roles)
                    filtered_results[role] = filtered_jobs
                    filtered_job_count += len(filtered_jobs)
                
                logger.info(f"Filtered results: {len(filtered_results)} roles, {filtered_job_count} jobs")
                
                # Print detailed results if verbose
                if args.verbose:
                    logger.info("\nDetailed results:")
                    
                    # Print original roles
                    logger.info("Original roles:")
                    for role in results.keys():
                        logger.info(f"  {role}")
                    
                    # Print filtered roles
                    logger.info("\nFiltered roles:")
                    for role in filtered_results.keys():
                        logger.info(f"  {role}")
                    
                    # Print sample filtered jobs
                    logger.info("\nSample filtered jobs:")
                    for role, jobs in filtered_results.items():
                        logger.info(f"\nRole: {role}")
                        for i, job in enumerate(jobs[:3]):  # Show first 3 jobs per role
                            logger.info(f"  Job {i+1}: {job.get('job_title')} - {job.get('company', 'Unknown')} ({job.get('location', 'Unknown')})")
                
            except ImportError as e:
                logger.error(f"Error importing scraper {args.scraper}: {e}")
            except Exception as e:
                logger.error(f"Error testing scraper {args.scraper}: {e}")
        
        # Include a brief test of validation against non-standard roles
        logger.info("\nTesting validation against non-standard roles:")
        edge_case_roles = [
            "O9 Technical Architect",
            "L5 Software Developer",
            "Project 2021 Manager",
            "ID-10-T Error Specialist",
            "Product Marketing Team Member",
            "Senior Backend Developer",
            "Python Programmer"
        ]
        
        for role in edge_case_roles:
            valid = is_valid_role(role, args.roles)
            logger.info(f"  {role} -> {'Valid' if valid else 'Invalid'}")
        
    except ImportError as e:
        logger.error(f"Error importing role validation utilities: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
