# app/scheduler/jobs.py
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta, timezone
import contextlib
import importlib
import io
import logging
import re
import sys
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import ScraperRun, Job
from app.db.crud import upsert_jobs, mark_inactive_jobs
from app.scrapers import get_all_scrapers

logger = logging.getLogger(__name__)

# Company name mappings for proper capitalization
COMPANY_NAMES = {
    "accenture": "Accenture",
    "acxiom": "Acxiom",
    "acxiomllc": "Acxiom LLC",
    "abbott": "Abbott",
    "adobe": "Adobe",
    "aep": "AEP",
    "allstate": "Allstate",
    "americanelectricpower": "American Electric Power",
    "amplify": "Amplify",
    "appliedmaterials": "Applied Materials",
    "airbus": "Airbus",
    "airliquide": "Air Liquide",
    "asmglobal": "ASM Global",
    "assurant": "Assurant",
    "att": "ATT",
    "autodesk": "Autodesk",
    "az":"astrazeneca",
    "baptist": "Baptist Health",
    "belron": "belron",
    "broadridge": "Broadridge",
    "bah":"Booz Allen Hamilton",
    "boeing": "Boeing",
    "cadence": "Cadence",
    "card": "Card",
    "cardinal": "Cardinal",
    "carmax": "CarMax",
    "carrier": "Carrier",
    "cat": "Caterpillar",
    "centrica": "Centrica",
    "chanel": "Chanel",
    "citi": "Citi bank",
    "clevelandclinic": "Cleveland Clinic",
    "cocacola": "Coca-Cola",
    "comcast": "Comcast",
    "covetrus": "Covetrus",
    "cox": "Cox",
    "cushmanwakefield": "Cushman & Wakefield",
    "cvshealth": "CVS Health",
    "cscc": "Columbus State Community College",
    "davita": "Davita",
    "deluxe": "Deluxe Corporation",
    "denverhealth": "Denver Health",
    "deutsche": "Deutsche Bank",
    "discover": "Capital One (Discover)",
    "disney": "Walt Disney Company",
    "encova": "Encova Insurance",
    "expedia": "Expedia",
    "factset": "FactSet",
    "fedex": "FedEx",
    "fidelity": "Fidelity",
    "fractal": "Fractal Analytics",
    "gartner": "Gartner",
    "geico": "GEICO",
    "gilead": "Gilead Sciences",
    "gm": "General Motors",
    "greif": "Greif",
    "grubhub": "Grubhub",
    "hartford": "Hartford Insurance",
    "hitachi": "Hitachi",
    "homedepot": "Home Depot",
    "humana": "Humana",
    "huntington": "Huntington Bank",
    "iheart": "iHeartMedia",
    "igs": "IGS Energy",
    "intel": "Intel",
    "ivy": "Ivy Tech",
    "illuminate": "Illuminate",
    "iqvia": "IQVIA",
    "jll": "JLL",
    "jonas": "Jonas Software",
    "kbr": "KBR",
    "kohls": "Kohl's",
    "kyndryl": "Kyn'dryl",
    "leidos": "Leidos",
    "lilly": "Eli Lilly",
    "logitech": "Logitech",
    "mckesson": "Mckesson",
    "montrose": "Onterris (Montrose)",
    "morganstanley": "Morgan Stanley",
    "mtbank": "M&T Bank",
    "marmon": "Marmon",
    "mcgill": "McGill",
    "motorola": "Motorola Solutions",
    "msd": "Merck Sharp & Dohme",
    "nationwide": "Nationwide",
    "nissan": "Nissan",
    "noblecorp": "Noble Corporation",
    "nordic":"nordic",
    "nordstrom": "Nordstrom",
    "nrel": "National Laboratory of the Rockies (NREL)",
    "nshs": "Northwell Health",
    "nvidia": "NVIDIA",
    "okgov": "State of Oklahoma",
    "oclc": "OCLC",
    "oregon": "State of Oregon",
    "otis": "Otis Worldwide",
    "osu":"ohio state university",
    "ohiohealth": "Ohio Health",
    "pennstate": "Pennsylvania State University",
    "premier": "Premier",
    "prologis": "Prologis",
    "progressiveleasing": "Progressive Leasing",
    "prysmian": "Prysmian Group",
    "ups": "UPS",
    "radian": "Radian",
    "rakuten": "Rakuten",
    "reliaquest": "ReliaQuest",
    "relx": "Relx",
    "republic": "Republic Services",
    "rochester": "University of Rochester",
    "rockwell": "Rockwell Automation",
    "ryan": "Ryan",
    "salesforce": "Salesforce",
    "samsung": "Samsung",
    "sanofi": "Sanofi",
    "scottsmiracle": "Scotts Miracle-Gro",
    "smg":"Scotts Miracle Gro",
    "snc": "SNC-Lavalin",
    "socure": "Socure",
    "statestreet": "State Street",
    "sunlife": "Sun Life",
    "takeda": "Takeda Pharmaceutical",
    "target": "Target Corporation",
    "thermofisher": "Thermo Fisher Scientific",
    "travelers": "Travelers Insurance",
    "tyson": "Tyson Foods",
    "ulse":"UL Research Institutes",
    "unhcr": "Office of the United Nations High Commissioner for Refugees",
    "umd":"University of Maryland",
    "usaa":"USAA",
    "ur":"united rentals",
    "usbank":"US Bank",
    "verily": "Verily",
    "verizon": "Verizon",
    "milwaukee":"milwaukee",
    "etsy":"etsy",
    "worldvision": "World Vision international",
    "woodward": "Woodwards",
    "walmart": "Walmart",
    "wellsfargo": "Wells Fargo & Company",
    "wellsky": "Wellsky",
    "warnerbros": "Warner Bros.",
    "workday": "Workday",
    "x": "xAI (X)",
    "xpanse": "Xpanse",
    "zillow": "Zillow",
    "zoom": "Zoom",
    "threem": "3M",
    "agilent": "Agilent Technologies",
    "aig": "AIG",
    "alteryx": "Alteryx",
    "amerilife": "AmeriLife",
    "amgen": "Amgen",
    "analogdevices": "Analog Devices",
    "bankofamerica": "Bank of America",
    "biogen": "Biogen",
    "baincapital": "Bain Capital",
    "broadcom": "Broadcom",
    "caresource": "CareSource",
    "centific": "Centific",
    "crowdstrike": "CrowdStrike",
    "draftkings": "DraftKings",
    "dukeenergy": "Duke Energy",
    "fiserv": "Fiserv",
    "fox": "Fox Corporation",
    "frostbank": "Frost Bank",
    "generac": "Generac",
    "generalmills": "General Mills",
    "gsk": "GSK",
    "guidehouse": "Guidehouse",
    "hollandknight": "Holland & Knight",
    "ibotta": "Ibotta",
    "illumina": "Illumina",
    "kiongroup": "KION Group",
    "kla": "KLA Corporation",
    "lennar": "Lennar",
    "marvell": "Marvell Semiconductor",
    "bcbsma": "Blue Cross Blue Shield of Massachusetts",
    "medtronic": "Medtronic",
    "modmed": "ModMed",
    "moderna": "Moderna",
    "morningstar": "Morningstar",
    "nxp": "NXP Semiconductors",
    "onemagnify": "OneMagnify",
    "pacificlife": "Pacific Life",
    "paper": "Paper",
    "pluralsight": "Pluralsight",
    "pnc": "PNC",
    "prodege": "Prodege",
    "radiancetech": "Radiance Technologies",
    "redhat": "Red Hat",
    "rocket": "Rocket",
    "root": "Root Insurance",
    "servicetitan": "ServiceTitan",
    "shipt": "Shipt",
    "signet": "Signet Jewelers",
    "snapfinance": "Snap Finance",
    "tiaa": "TIAA",
    "totalwine": "Total Wine & More",
    "tricorbraun": "TricorBraun",
    "turo": "Turo",
    "vertex": "Vertex Pharmaceuticals",
    "visa": "Visa",
    "vizient": "Vizient",
    "vumc": "Vanderbilt University Medical Center",
    "westernalliance": "Western Alliance Bank",
    "wework": "WeWork",
    "agilon": "Agilon Health",
    "ashland": "Ashland",
    "huron": "Huron (AXIA Consulting)",
    "epiq": "Epiq",
    "erpa": "ERP Analysts",
    "fifththird": "Fifth Third Bank",
    "genpact": "Genpact",
    "lower": "Lower",
    "nationwidechildrens": "Nationwide Children's Hospital",
    "sedgwick": "Sedgwick",
    "protiviti": "Protiviti",
    "abercrombie": "Abercrombie & Fitch",
    "roguefitness": "Rogue Fitness",
    "nisource": "NiSource",
    "brown": "Brown University"
}


def _init_scraper_role_maps():
    DS = "Data Science"
    DSPS = "Data Scientist python SQL"
    DA = "Data Analyst"
    DAV = "Data Analyst visualization"
    MLE = "Machine Learning Engineer python SQL"
    AI = "AI Engineer python SQL"
    AIR = "AI Research Engineer python"
    NLP = "Natural Language Processing Engineer AI python"
    CVE = "Computer Vision Engineer AI python"
    GAE = "Generative AI Engineer python"
    SQL = "SQL Developer"
    LLM = "LLM Engineer"
    PE = "Prompt Engineer"
    MLOPS = "MLOps Engineer"
    AIARCH = "AI/ML Architect"
    AIIE = "AI Infrastructure Engineer"
    DE = "Data Engineer"
    GENAI_ARCH = "Generative AI Architect"
    LLMR = "AI/LLM Researcher"
    FME = "Foundation Model Engineer"
    RAG_ENG = "RAG Engineer"
    AIAG = "AI Agent Engineer"
    default_roles = [DS, DSPS, DAV, DA, MLE, AI, AIR, NLP, CVE, GAE, SQL, LLM, PE, MLOPS, AIARCH, AIIE, DE, GENAI_ARCH, LLMR, FME, RAG_ENG, AIAG]
    base_roles = list(default_roles)
    companies_with_custom_roles = [
        "oclc", "accenture", "acxiom", "acxiomllc", "abbott", "adobe", "aep",
        "allstate", "americanelectricpower", "amplify",
        "appliedmaterials", "airliquide", "airbus", "asmglobal", "assurant",
        "att", "autodesk", "az", "baptist", "bah", "belron", "boeing",
        "broadridge", "cadence", "card", "cardinal", "carmax", "carrier", "cat",
        "centrica", "chanel", "citi", "clevelandclinic", "cocacola", "comcast",
        "covetrus", "cox", "cscc", "cushmanwakefield", "cvshealth", "davita",
        "deluxe", "denverhealth", "deutsche", "discover", "disney", "encova",
        "expedia", "etsy", "factset", "fedex", "fidelity", "fractal", "gartner",
        "geico", "gilead", "gm", "greif", "grubhub", "hartford", "hitachi",
        "homedepot", "humana", "huntington", "iheart", "igs", "intel", "iqvia",
        "illuminate", "ivy", "jll", "jonas", "leidos", "lilly", "kbr", "kohls",
        "kyndryl", "logitech", "marmon", "mcgill", "mckesson", "milwaukee",
        "montrose", "morganstanley", "motorola", "msd", "mtbank", "nationwide",
        "nissan", "noblecorp", "nordic", "nordstrom", "nrel", "nshs", "nvidia",
        "okgov", "oregon", "osu", "otis", "ohiohealth", "pennstate", "premier",
        "prologis", "progressiveleasing", "prysmian", "radian", "rakuten",
        "republic", "reliaquest", "relx", "rochester", "rockwell", "ryan",
        "salesforce", "samsung", "sanofi", "scottsmiracle", "smg", "snc",
        "socure", "statestreet", "sunlife", "takeda", "target", "thermofisher",
        "travelers", "tyson", "ulse", "umd", "unhcr", "ups", "ur", "usaa",
        "usbank", "verily", "verizon", "walmart", "warnerbros", "wellsfargo",
        "wellsky", "woodward", "workday", "worldvision", "x", "xpanse",
        "zillow", "zoom",
        "threem", "agilent", "aig", "alteryx", "amerilife", "amgen",
        "analogdevices", "bankofamerica", "biogen", "baincapital", "broadcom",
        "caresource", "centific", "crowdstrike", "draftkings", "dukeenergy",
        "fiserv", "fox", "frostbank", "generac", "generalmills", "gsk",
        "guidehouse", "hollandknight", "ibotta", "illumina", "kiongroup",
        "kla", "lennar", "marvell", "bcbsma", "medtronic", "modmed",
        "moderna", "morningstar", "nxp", "onemagnify", "pacificlife", "paper",
        "pluralsight", "pnc", "prodege", "radiancetech", "redhat", "rocket",
        "root", "servicetitan", "shipt", "signet", "snapfinance", "tiaa",
        "totalwine", "tricorbraun", "turo", "vertex", "visa", "vizient",
        "vumc", "westernalliance", "wework", "agilon", "ashland", "huron",
        "epiq", "erpa", "fifththird", "genpact", "lower",
        "nationwidechildrens", "sedgwick", "protiviti", "abercrombie",
        "roguefitness", "nisource", "brown"
    ]
    custom_roles = {name: list(base_roles) for name in companies_with_custom_roles}
    return default_roles, custom_roles


_DEFAULT_ROLES, _CUSTOM_ROLES = _init_scraper_role_maps()


def resolve_roles_for_scraper(scraper_name, roles=None):
    """Return the role query list for a scraper (same rules as run_scraper when roles is None)."""
    if roles is not None:
        return roles
    return _CUSTOM_ROLES.get(scraper_name, _DEFAULT_ROLES)


def fetch_scraper_jobs_raw(scraper_name, roles=None, days_back=7):
    """
    Run get_{scraper_name}_jobs with the same role resolution as the scheduler,
    without writing to the database.
    """
    resolved = resolve_roles_for_scraper(scraper_name, roles)
    scraper_module = importlib.import_module(f"app.scrapers.{scraper_name}")
    get_jobs_func = getattr(scraper_module, f"get_{scraper_name}_jobs")
    return get_jobs_func(roles=resolved, days=days_back)


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

# Scrapers catch their own request errors and print() them instead of raising,
# so a run that failed every request still "completes". We tee stdout while a
# scraper runs and count those printed errors to judge the run honestly.
_ERROR_LINE = re.compile(r"\b(error|exception|traceback|failed)\b", re.IGNORECASE)
STALE_RUN_AFTER = timedelta(hours=2)


class _TeeStdout(io.TextIOBase):
    """Write to the real stdout and keep a copy for error counting."""

    def __init__(self, original):
        self.original = original
        self.buffer_text = io.StringIO()

    def write(self, text):
        self.buffer_text.write(text)
        try:
            return self.original.write(text)
        except Exception:
            return len(text)

    def flush(self):
        try:
            self.original.flush()
        except Exception:
            pass


def classify_run(jobs_found, error_lines):
    """Return (status, message) for a finished scraper run.

    success  jobs returned and no errors printed
    partial  jobs returned but some requests errored
    empty    ran cleanly, nothing matched the searched roles
    failure  no jobs and errors printed (blocked, bad URL, API change)
    """
    sample = "\n".join(error_lines[:5])
    if jobs_found > 0 and not error_lines:
        return "success", None
    if jobs_found > 0:
        return "partial", f"{jobs_found} jobs returned; {len(error_lines)} error line(s):\n{sample}"
    if not error_lines:
        return "empty", "Ran without errors but returned 0 jobs for the searched roles"
    return "failure", f"Returned 0 jobs; {len(error_lines)} error line(s):\n{sample}"


def close_stale_runs(db):
    """Mark runs stuck in 'running' (process restarted mid-run) as interrupted."""
    cutoff = datetime.now(timezone.utc) - STALE_RUN_AFTER
    stale = db.query(ScraperRun).filter(
        ScraperRun.status == "running",
        ScraperRun.start_time < cutoff.replace(tzinfo=None),
    ).all()
    for run in stale:
        run.status = "interrupted"
        run.error_message = "Process stopped before this run finished (restart or deploy)"
    if stale:
        db.commit()
    return len(stale)


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
    
    # If roles not provided, use company-specific custom roles or default
    if roles is None:
        roles = resolve_roles_for_scraper(scraper_name)
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
        
        # Run the scraper, keeping a copy of what it prints so swallowed
        # request errors still count against the run
        tee = _TeeStdout(sys.stdout)
        with contextlib.redirect_stdout(tee):
            jobs_data = get_jobs_func(roles=roles, days=days_back) or {}
        error_lines = [
            line.strip() for line in tee.buffer_text.getvalue().splitlines()
            if _ERROR_LINE.search(line)
        ]

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
        status, message = classify_run(total_jobs_found, error_lines)
        scraper_run.status = status
        scraper_run.error_message = message
        scraper_run.end_time = datetime.now(timezone.utc)
        scraper_run.jobs_added = jobs_added
        scraper_run.jobs_updated = jobs_updated
        if status == "failure":
            global_stats["scraper_errors"] += 1

        logger.info(
            f"Scraper {scraper_name} {status}: {total_jobs_found} found, {jobs_added} added, "
            f"{jobs_updated} updated, {expired_count} expired, {len(error_lines)} error line(s)"
        )
        
    except Exception as e:
        # Log the error with full context and update the scraper run record
        error_msg = str(e)
        logger.error(f"SCRAPER FAILURE: {scraper_name} | Error: {error_msg}")
        logger.error(f"Full traceback for {scraper_name}:", exc_info=True)
        scraper_run.status = "failure"
        scraper_run.end_time = datetime.now(timezone.utc)
        scraper_run.error_message = error_msg
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

    db = next(get_db())
    try:
        stale = close_stale_runs(db)
        if stale:
            logger.info(f"Marked {stale} stale scraper run(s) as interrupted")
    finally:
        db.close()
    
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
        CronTrigger(hour='9-19', minute='0'),  # Run at the top of every hour from 7 AM to 5 PM
        id="run_all_scrapers",
        replace_existing=True
    )
    
    # Schedule a job to check for expired jobs daily
    scheduler.add_job(
        check_for_expired_jobs,
        CronTrigger(hour=18, minute=0),  # Run daily at 6 PM
        id="check_for_expired_jobs",
        replace_existing=True
    )
    
    # Run scrapers once at startup only if not already scheduled
    if scheduler.get_job('run_all_scrapers') is None:
        logger.warning("Scheduler reset detected, re-configuring all jobs")
        scheduler.add_job(
            run_all_scrapers,
            CronTrigger(hour='7-17', minute='0'),
            id="run_all_scrapers",
            replace_existing=True
        )
        
        scheduler.add_job(
            check_for_expired_jobs,
            CronTrigger(hour=18, minute=0),
            id="check_for_expired_jobs",
            replace_existing=True
        )
    
    scheduler.start()
    logger.info(f"Scheduler started with {len(available_scrapers)} scrapers running hourly from 7 AM to 5 PM")
    
    return scheduler
