# app/scheduler/jobs.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone
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
    "airbus": "Airbus",
    "assurant": "Assurant",
    "att": "ATT",
    "autodesk": "Autodesk",
    "az":"astrazeneca",
    "belron": "belron",
    "broadridge": "Broadridge",
    "bah":"Booz Allen Hamilton",
    "boeing": "Boeing",
    "card": "Card",
    "cardinal": "Cardinal",
    "cat": "Caterpillar",
    "centrica": "Centrica",
    "chanel": "Chanel",
    "citi": "Citi bank",
    "clevelandclinic": "Cleveland Clinic",
    "covetrus": "Covetrus",
    "cox": "Cox",
    "cushmanwakefield": "Cushman & Wakefield",
    "cvshealth": "CVS Health",
    "cscc": "Columbus State Community College",
    "davita": "Davita",
    "denverhealth": "Denver Health",
    "discover": "Discover",
    "encova": "Encova Insurance",
    "expedia": "Expedia",
    "gartner": "Gartner",
    "gm": "General Motors",
    "greif": "Greif",
    "grubhub": "Grubhub",
    "homedepot": "Home Depot",
    "igs": "IGS Energy",
    "illuminate": "Illuminate",
    "iqvia": "IQVIA",
    "jll": "JLL",
    "kbr": "KBR",
    "kyndryl": "Kyn'dryl",
    "lilly": "Eli Lilly",
    "mckesson": "Mckesson",
    "montrose": "Montrose",
    "marmon": "Marmon",
    "mcgill": "McGill",
    "nationwide": "Nationwide",
    "noblecorp": "Noble Corporation",
    "nordic":"nordic",
    "nvidia": "NVIDIA",
    "osu":"ohio state university",
    "ohiohealth": "Ohio Health",
    "premier": "Premier",
    "prologis": "Prologis",
    "ups": "UPS",
    "radian": "Radian",
    "relx": "Relx",
    "republic": "Republic Services",
    "rochester": "University of Rochester",
    "ryan": "Ryan",
    "salesforce": "Salesforce",
    "samsung": "Samsung",
    "sanofi": "Sanofi",
    "scottsmiracle": "Scotts Miracle-Gro",
    "smg":"Scotts Miracle Gro",
    "sunlife": "Sun Life",
    "verily": "Verily",
    "verizon": "Verizon",
    "walmart": "Walmart",
    "workday": "Workday",
    "x": "X (Twitter)",
    "xpanse": "Xpanse",
    "hitachi": "Hitachi",
    "usaa":"USAA",
    "ur":"united rentals",
    "milwaukee":"milwaukee",
    "etsy":"etsy",
    "worldvision": "World Vision international",
    "woodward": "Woodwards",
    "wellsky": "Wellsky",
    "warnerbros": "Warner Bros."
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
    default_roles = ["Data  Science python SQL", "Data Analyst", "Machine Learning Engineer python SQL", "AI Engineer python SQL"]
    DS="Data  Science python SQL"
    DA="Data Analyst"
    MLE="Machine Learning Engineer python SQL"
    AI="AI Engineer python SQL"
    
    # Define custom roles for specific scrapers if needed
    custom_roles = {
        "accenture": [DS, DA, MLE, AI],
        "adobe": [DS, DA, MLE, AI],
        "appliedmaterials": [DS, DA, MLE, AI],
        "airbus": [DS, DA, MLE, AI],
        "assurant": [DS, DA, MLE, AI],
        "att": [DS, DA, MLE, AI],
        "autodesk": [DS, DA, MLE, AI],
        "az": [DS, DA, MLE, AI],
        "bah": [DS, DA, MLE, AI],
        "belron": [DS, DA, MLE, AI],
        "boeing": [DS, DA, MLE, AI],
        "broadridge": [DS, DA, MLE, AI],
        "card": [DS, DA, MLE, AI],
        "cardinal": [DS, DA, MLE, AI],
        "cat": [DS, DA, MLE, AI],
        "centrica": [DS, DA, MLE, AI],
        "chanel": [DS, DA, MLE, AI],
        "citi": [DS, DA, MLE, AI],
        "clevelandclinic": [DS, DA, MLE, AI],
        "covetrus": [DS, DA, MLE, AI],
        "cox": [DS, DA, MLE, AI],
        "cscc": [DS, DA, MLE, AI],
        "cushmanwakefield": [DS, DA, MLE, AI],
        "cvshealth": [DS, DA, MLE, AI],
        "davita": [DS, DA, MLE, AI],
        "denverhealth": [DS, DA, MLE, AI],
        "discover": [DS, DA, MLE, AI],
        "encova": [DS, DA, MLE, AI],
        "expedia": [DS, DA, MLE, AI],
        "gartner": [DS, DA, MLE, AI],
        "gm": [DS, DA, MLE, AI],
        "greif": [DS, DA, MLE, AI],
        "grubhub": [DS, DA, MLE, AI],
        "homedepot": [DS, DA, MLE, AI],
        "igs": [DS, DA, MLE, AI],
        "iqvia": [DS, DA, MLE, AI],
        "illuminate": [DS, DA, MLE, AI],
        "jll": [DS, DA, MLE, AI],
        "lilly": [DS, DA, MLE, AI],
        "kbr": [DS, DA, MLE, AI],
        "kyndryl": [DS, DA, MLE, AI],
        "marmon": [DS, DA, MLE, AI],
        "mcgill": [DS, DA, MLE, AI],
        "mckesson": [DS, DA, MLE, AI],
        "montrose": [DS, DA, MLE, AI],
        "nationwide": [DS, DA, MLE, AI],
        "noblecorp": [DS, DA, MLE, AI],
        "nordic": [DS, DA, MLE, AI],
        "nvidia": [DS, DA, MLE, AI],
        "osu": [DS, DA, MLE, AI],
        "ohiohealth": [DS, DA, MLE, AI],
        "premier": [DS, DA, MLE, AI],
        "prologis": [DS, DA, MLE, AI],
        "radian": [DS, DA, MLE, AI],
        "republic": [DS, DA, MLE, AI],
        "relx": [DS, DA, MLE, AI],
        "rochester": [DS, DA, MLE, AI],
        "ryan": [DS, DA, MLE, AI],
        "salesforce": [DS, DA, MLE, AI],
        "samsung": [DS, DA, MLE, AI],
        "sanofi": [DS, DA, MLE, AI],
        "scottsmiracle": [DS, DA, MLE, AI],
        "smg": [DS, DA, MLE, AI],
        "sunlife": [DS, DA, MLE, AI],
        "verily": [DS, DA, MLE, AI],
        "verizon": [DS, DA, MLE, AI],
        "walmart": [DS, DA, MLE, AI],
        "workday": [DS, DA, MLE, AI],
        "x": [DS, DA, MLE, AI],
        "xpanse": [DS, DA, MLE, AI],
        "hitachi": [DS, DA, MLE, AI],
        "usaa": [DS, DA, MLE, AI],
        "ups": [DS, DA, MLE, AI],
        "ur": [DS, DA, MLE, AI],
        "milwaukee": [DS, DA, MLE, AI],
        "etsy": [DS, DA, MLE, AI],
        "worldvision": [DS, DA, MLE, AI],
        "woodward": [DS, DA, MLE, AI],
        "wellsky": [DS, DA, MLE, AI],
        "warnerbros": [DS, DA, MLE, AI]
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
        start_time=datetime.now(timezone.utc),
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
        scraper_run.end_time = datetime.now(timezone.utc)
        scraper_run.jobs_added = jobs_added
        scraper_run.jobs_updated = jobs_updated
        
        logger.info(f"Scraper {scraper_name} completed: {jobs_added} added, {jobs_updated} updated, {expired_count} expired")
        
    except Exception as e:
        # Log the error and update the scraper run record
        logger.error(f"Error running scraper {scraper_name}: {str(e)}")
        scraper_run.status = "failure"
        scraper_run.end_time = datetime.now(timezone.utc)
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
            logger.info(f"SCRAPER RUN SUMMARY ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')})")
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
