# app/scheduler/jobs.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
import importlib
import logging
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ScraperRun, Job
from app.db.crud import upsert_jobs, mark_inactive_jobs
from app.scrapers import get_all_scrapers

logger = logging.getLogger(__name__)

# Company name mappings for proper capitalization
COMPANY_NAMES = {
    "accenture": "Accenture",
    "adobe": "Adobe",
    "appliedmaterials": "Applied Materials",
    "assurant": "Assurant",
    "autodesk": "Autodesk",
    "broadridge": "Broadridge",
    "cat": "Caterpillar",
    "cox": "Cox",
    "cushmanwakefield": "Cushman & Wakefield",
    "cvshealth": "CVS Health",
    "denverhealth": "Denver Health",
    "discover": "Discover",
    "expedia": "Expedia",
    "gartner": "Gartner",
    "grubhub": "Grubhub",
    "homedepot": "Home Depot",
    "lilly": "Eli Lilly",
    "marmon": "Marmon",
    "noblecorp": "Noble Corporation",
    "nvidia": "NVIDIA",
    "premier": "Premier",
    "radian": "Radian",
    "republic": "Republic Services",
    "salesforce": "Salesforce",
    "scottsmiracle": "Scotts Miracle-Gro",
    "sunlife": "Sun Life",
    "verily": "Verily",
    "verizon": "Verizon",
    "walmart": "Walmart",
    "workday": "Workday",
    "x": "X (Twitter)",
    "xpanse": "Xpanse",
    "hitachi": "Hitachi",
    "usaa":"USAA",
    "milwaukee":"milwaukee",
    "etsy":"etsy"
}

# Running statistics
global_stats = {
    "total_jobs_added": 0,
    "total_jobs_updated": 0,
    "total_jobs_expired": 0,
    "scrapers_run": 0,
    "scraper_errors": 0
}

def reset_global_stats():
    """Reset the global statistics counters"""
    global global_stats
    global_stats = {
        "total_jobs_added": 0,
        "total_jobs_updated": 0,
        "total_jobs_expired": 0,
        "scrapers_run": 0,
        "scraper_errors": 0
    }

def run_scraper(scraper_name, roles=None, days_back=7):
    """
    Run a specific scraper and update the database with results
    
    Args:
        scraper_name: Name of the scraper module (e.g., 'salesforce')
        roles: List of roles to search for, if None uses company-specific custom roles
        days_back: How many days back to check
    """
    global global_stats
    
    # Update counter
    global_stats["scrapers_run"] += 1
    current_scraper = global_stats["scrapers_run"]
    total_scrapers = len(get_all_scrapers())
    
    # Default roles to use for all scrapers
    default_roles = ["Data Scientist", "Data Analyst", "Machine Learning Engineer"]
    
    # Define custom roles for specific scrapers if needed
    custom_roles = {
        "accenture": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "adobe": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "appliedmaterials": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "assurant": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "autodesk": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "broadridge": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "cat": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "cox": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "cushmanwakefield": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "cvshealth": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "denverhealth": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "discover": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "expedia": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "gartner": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "grubhub": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "homedepot": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "lilly": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "marmon": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "noblecorp": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "nvidia": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "premier": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "radian": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "republic": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "salesforce": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "scottsmiracle": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "sunlife": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "verily": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "verizon": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "walmart": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "workday": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "x": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "xpanse": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "hitachi": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "usaa": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "milwaukee": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"],
        "etsy": ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"]
    }
    
    # If roles not provided, use company-specific custom roles or default
    if roles is None:
        roles = custom_roles.get(scraper_name, default_roles)
        logger.info(f"Using custom roles for {scraper_name}: {roles}")
    
    # Log the start of this scraper
    logger.info(f"Running scraper {current_scraper}/{total_scrapers}: {scraper_name}")
    
    db = next(get_db())
    
    # Get proper company name for display
    company_display_name = COMPANY_NAMES.get(scraper_name, scraper_name.capitalize())
    
    # Create a scraper run record
    scraper_run = ScraperRun(
        scraper_name=scraper_name,
        start_time=datetime.utcnow(),
        status="running"
    )
    db.add(scraper_run)
    db.commit()
    
    try:
        # Dynamically import the scraper module
        scraper_module = importlib.import_module(f"app.scrapers.{scraper_name}")
        
        # Get the main function from the module
        get_jobs_func = getattr(scraper_module, f"get_{scraper_name}_jobs")
        
        # Run the scraper
        jobs_data = get_jobs_func(roles=roles, days=days_back)
        
        # Count total jobs found
        total_jobs_found = sum(len(jobs) for jobs in jobs_data.values())
        logger.info(f"Scraper {scraper_name} found {total_jobs_found} jobs across {len(jobs_data)} roles")
        
        # Track active job IDs for this company
        active_job_ids = []
        
        # Update database with new job listings
        jobs_added, jobs_updated = upsert_jobs(db, jobs_data, company=company_display_name)
        
        # Collect active job IDs
        for role_jobs in jobs_data.values():
            for job in role_jobs:
                if job.get("job_id"):
                    active_job_ids.append(job.get("job_id"))
        
        # Mark jobs that are no longer active
        expired_count = 0
        if active_job_ids:
            expired_count = mark_inactive_jobs(db, company_display_name, active_job_ids)
        
        # Update global statistics
        global_stats["total_jobs_added"] += jobs_added
        global_stats["total_jobs_updated"] += jobs_updated
        global_stats["total_jobs_expired"] += expired_count
        
        # Update the scraper run record
        scraper_run.status = "success"
        scraper_run.end_time = datetime.utcnow()
        scraper_run.jobs_added = jobs_added
        scraper_run.jobs_updated = jobs_updated
        
        logger.info(f"Scraper {scraper_name} completed: {jobs_added} added, {jobs_updated} updated, {expired_count} expired")
        
    except Exception as e:
        # Log the error and update the scraper run record
        logger.error(f"Error running scraper {scraper_name}: {str(e)}")
        scraper_run.status = "failure"
        scraper_run.end_time = datetime.utcnow()
        scraper_run.error_message = str(e)
        global_stats["scraper_errors"] += 1
    
    finally:
        db.commit()
        db.close()
        
        # Print summary if this was the last scraper to run
        if current_scraper == total_scrapers:
            errors = global_stats["scraper_errors"]
            success_rate = ((total_scrapers - errors) / total_scrapers) * 100 if total_scrapers > 0 else 0
            
            logger.info("=" * 50)
            logger.info(f"SCRAPER RUN SUMMARY ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
            logger.info(f"Scrapers run: {total_scrapers}")
            logger.info(f"Successful: {total_scrapers - errors} ({success_rate:.1f}%)")
            logger.info(f"Failed: {errors}")
            logger.info(f"Total jobs added: {global_stats['total_jobs_added']}")
            logger.info(f"Total jobs updated: {global_stats['total_jobs_updated']}")
            logger.info(f"Total jobs expired: {global_stats['total_jobs_expired']}")
            logger.info("=" * 50)
            
            # Reset the global stats after logging the summary
            reset_global_stats()

def run_all_scrapers():
    """Run all scrapers immediately"""
    logger.info("Running all scrapers now...")
    
    # Reset the global stats before starting a new run
    reset_global_stats()
    
    # Get all available scrapers
    available_scrapers = get_all_scrapers()
    
    # Log the number of scrapers found
    logger.info(f"Found {len(available_scrapers)} scrapers to run")
    
    # Run each scraper with its custom roles
    for scraper_name in available_scrapers:
        # Custom roles will be used automatically in run_scraper
        run_scraper(scraper_name)

def check_for_expired_jobs():
    """Check for and mark expired jobs"""
    logger.info("Checking for expired jobs...")
    
    db = next(get_db())
    try:
        # Count active jobs
        active_count = db.query(Job).filter(Job.is_active == True).count()
        
        # Count inactive jobs
        inactive_count = db.query(Job).filter(Job.is_active == False).count()
        
        logger.info(f"Job status: {active_count} active, {inactive_count} inactive")
        
    except Exception as e:
        logger.error(f"Error checking job status: {str(e)}")
    finally:
        db.close()

def setup_scheduler():
    """Configure and start the background scheduler"""
    scheduler = BackgroundScheduler()
    
    # Get all available scrapers
    available_scrapers = get_all_scrapers()
    
    # Log the number of scrapers found
    logger.info(f"Found {len(available_scrapers)} scrapers to schedule")
    
    # Schedule all scrapers to run hourly from 7 AM to 5 PM
    scheduler.add_job(
        run_all_scrapers,
        CronTrigger(hour='7-17', minute='0'),  # Run at the top of every hour from 7 AM to 5 PM
        id="hourly_scraper_run",
        replace_existing=True
    )
    
    # Schedule a job to check for expired jobs daily
    scheduler.add_job(
        check_for_expired_jobs,
        CronTrigger(hour=18, minute=0),  # Run daily at 6 PM
        id="daily_expired_check",
        replace_existing=True
    )
    
    # Commented out to prevent scraping on every startup
    # scheduler.add_job(
    #     run_all_scrapers,
    #     'date',
    #     id="startup_scraper_run"
    # )
    
    scheduler.start()
    logger.info(f"Scheduler started with {len(available_scrapers)} scrapers running hourly from 7 AM to 5 PM")
    
    return scheduler
