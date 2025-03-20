# app/db/crud.py
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime
from typing import Dict, List, Tuple, Any
import logging
import time

from app.db.models import Job, Role
from app.db.database import get_db

# Set up logger
logger = logging.getLogger('job_tracker.crud')

# Predefined valid roles - used for validation
VALID_ROLES = {
    "Software Engineer", 
    "Data Scientist", 
    "Product Manager",
    "UX Designer",
    "DevOps Engineer",
    "Full Stack Developer",
    "Frontend Engineer",
    "Backend Engineer",
    "Machine Learning Engineer",
    "QA Engineer",
    "Data Engineer",
    "Site Reliability Engineer",
    "Technical Program Manager",
    "Research Scientist",
    "Security Engineer",
    "Cloud Engineer",
    "AI Engineer",
    "Business Analyst",
    "Technical Writer",
    "Systems Engineer", 
    "Data Analyst",
    "Data Science",
    "Python Engineer",
    "SQL Developer",
    "Data Administrator",
    "MLOps Engineer",
    "AI Researcher"
}

def clean_role_name(role_name: str) -> str:
    """Clean up role name for consistency"""
    if not role_name:
        return "Software Engineer"  # Default role
    
    # Clean and normalize role name
    cleaned = role_name.strip()
    
    # Find the closest match in valid roles if needed
    if cleaned not in VALID_ROLES:
        # Check if any valid role is a substring of the role name
        for valid_role in VALID_ROLES:
            if valid_role.lower() in cleaned.lower():
                logger.debug(f"Mapped role '{cleaned}' to valid role '{valid_role}'")
                return valid_role
        
        # If no match found, but role name seems valid (not empty or too generic),
        # accept it as a new valid role
        if len(cleaned) > 3 and cleaned.lower() not in ["job", "general", "position", "opening"]:
            logger.info(f"Adding new valid role: {cleaned}")
            VALID_ROLES.add(cleaned)  # Add dynamically to valid roles
    
    return cleaned

def get_or_create_role(db: Session, role_name: str) -> Role:
    """Get a role by name or create it if it doesn't exist"""
    # Clean and validate role name
    cleaned_role_name = clean_role_name(role_name)
    
    # Skip empty roles
    if not cleaned_role_name or cleaned_role_name == "General":
        cleaned_role_name = "Software Engineer"  # Default role
    
    # Try to get the role from database
    role = db.query(Role).filter(Role.name == cleaned_role_name).first()
    if not role:
        # Create the role if it doesn't exist
        logger.info(f"Creating new role: {cleaned_role_name}")
        role = Role(name=cleaned_role_name)
        db.add(role)
        db.commit()
        db.refresh(role)
    
    return role

def add_role_to_job(db: Session, job: Job, role: Role) -> bool:
    """Add a role to a job if it's not already associated"""
    try:
        if role and role not in job.roles:
            job.roles.append(role)
            db.commit()
            return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding role to job: {str(e)}")
    return False

def safely_get_job_by_id(db: Session, job_id: str, company: str, max_retries: int = 3) -> Job:
    """
    Try to retrieve a job with retries to handle potential transaction delays
    """
    for attempt in range(max_retries):
        try:
            job = db.query(Job).filter(
                Job.job_id == job_id,
                Job.company == company
            ).first()
            
            if job:
                return job
                
            # If not found and not the last attempt, wait briefly and retry
            if attempt < max_retries - 1:
                time.sleep(0.1 * (attempt + 1))  # Exponential backoff
        except Exception as e:
            logger.error(f"Error retrieving job {job_id} (attempt {attempt+1}): {str(e)}")
            
            # If this is the last attempt, just continue to return None
            if attempt < max_retries - 1:
                # Try with a fresh DB session
                db.close()
                db = next(get_db())
    
    return None

def upsert_job(db: Session, job_data: Dict[str, Any], company: str, role: Role) -> Tuple[bool, Job, bool]:
    """
    Insert or update a job in the database with improved duplicate handling
    
    Returns:
        Tuple of (is_new, job_model, is_duplicate)
        where is_new is True if this was a new job, False if updated
        is_duplicate is True if this job was skipped due to being a duplicate
    """
    # Validate required fields
    job_id = job_data.get("job_id")
    if not job_id:
        logger.warning(f"Missing job_id for job: {job_data.get('job_title')}. Skipping.")
        return False, None, False
    
    # Parse date or use current date if invalid
    try:
        date_posted = datetime.strptime(job_data.get("date_posted", ""), "%Y-%m-%d")
    except (ValueError, TypeError):
        logger.warning(f"Invalid date format: {job_data.get('date_posted')}. Using current date.")
        date_posted = datetime.utcnow()
    
    # FIRST, check if job exists by ID to prevent UniqueViolation errors
    existing_job = safely_get_job_by_id(db, job_id, company)
    
    if existing_job:
        try:
            # Update existing job
            logger.debug(f"Updating existing job: {job_id} - {job_data.get('job_title')}")
            
            existing_job.job_title = job_data.get("job_title", existing_job.job_title)
            existing_job.location = job_data.get("location", existing_job.location)
            existing_job.job_url = job_data.get("job_url", existing_job.job_url)
            existing_job.date_posted = date_posted
            existing_job.employment_type = job_data.get("employment_type", existing_job.employment_type)
            existing_job.description = job_data.get("description", existing_job.description)
            existing_job.last_updated = datetime.utcnow()
            existing_job.is_active = True  # Ensure it's marked as active
            existing_job.raw_data = job_data
            
            # Check if this role is already associated with the job
            add_role_to_job(db, existing_job, role)
            
            return False, existing_job, False
        except Exception as update_error:
            db.rollback()
            logger.error(f"Error updating job {job_id}: {str(update_error)}")
            return False, None, False
    else:
        # Check for potential duplicate by title and location before creating
        try:
            potential_duplicate = db.query(Job).filter(
                Job.job_title == job_data.get("job_title", ""),
                Job.location == job_data.get("location", ""),
                Job.company == company,
                Job.is_active == True
            ).first()
            
            if potential_duplicate:
                logger.info(f"Potential duplicate found: {job_data.get('job_title')} at {job_data.get('location')} (existing job_id: {potential_duplicate.job_id}, new job_id: {job_id})")
                # Add this role to the existing duplicate if needed
                add_role_to_job(db, potential_duplicate, role)
                return False, potential_duplicate, True
        except Exception as dup_error:
            logger.error(f"Error checking for duplicates for job {job_id}: {str(dup_error)}")
        
        # Create new job - with better transaction handling
        try:
            # Try a more robust upsert approach using SQLAlchemy's insert with on_conflict_do_update
            stmt = insert(Job).values(
                job_id=job_id,
                job_title=job_data.get("job_title", ""),
                location=job_data.get("location", ""),
                job_url=job_data.get("job_url", ""),
                company=company,
                date_posted=date_posted,
                employment_type=job_data.get("employment_type", ""),
                description=job_data.get("description", ""),
                first_seen=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                is_active=True,
                raw_data=job_data
            )
            
            # On conflict, update the record
            stmt = stmt.on_conflict_do_update(
                index_elements=['job_id'],
                set_={
                    'job_title': job_data.get("job_title", ""),
                    'location': job_data.get("location", ""),
                    'job_url': job_data.get("job_url", ""),
                    'date_posted': date_posted,
                    'employment_type': job_data.get("employment_type", ""),
                    'description': job_data.get("description", ""),
                    'last_updated': datetime.utcnow(),
                    'is_active': True,
                    'raw_data': job_data
                }
            )
            
            # Execute the statement
            result = db.execute(stmt)
            db.commit()
            
            # Check if this was an insert or update
            is_insert = result.rowcount > 0
            
            # Now retrieve the job to add the role
            job = safely_get_job_by_id(db, job_id, company)
            
            if job:
                add_role_to_job(db, job, role)
                return is_insert, job, False
            else:
                logger.error(f"Failed to retrieve job {job_id} after upsert")
                return False, None, False
                
        except IntegrityError as integrity_error:
            db.rollback()
            logger.warning(f"IntegrityError during job upsert for {job_id}: {str(integrity_error)}")
            
            # Retry one more time with a get + update approach
            try:
                # Let's wait a brief moment for any concurrent transaction to finish
                time.sleep(0.1)
                
                # Get a fresh session
                db.close()
                new_db = next(get_db())
                
                # Try to get the job that must now exist (since we got an integrity error)
                job = new_db.query(Job).filter(
                    Job.job_id == job_id,
                    Job.company == company
                ).first()
                
                if job:
                    logger.info(f"Successfully found existing job {job_id} after IntegrityError")
                    add_role_to_job(new_db, job, role)
                    return False, job, True
                else:
                    logger.error(f"Failed to find job {job_id} after IntegrityError")
                    return False, None, False
            except Exception as retry_error:
                logger.error(f"Error in retry handling for job {job_id}: {str(retry_error)}")
                return False, None, False
                
        except Exception as general_error:
            db.rollback()
            logger.error(f"Error creating job {job_id}: {str(general_error)}")
            return False, None, False

def upsert_jobs(db: Session, jobs_by_role: Dict[str, List[Dict[str, Any]]], company: str) -> Tuple[int, int]:
    """
    Process all jobs from a scraper run with improved error handling
    
    Args:
        db: Database session
        jobs_by_role: Dictionary of jobs organized by role
        company: Company name
        
    Returns:
        Tuple of (jobs_added, jobs_updated)
    """
    jobs_added = 0
    jobs_updated = 0
    duplicates_skipped = 0
    errors = 0
    
    # Track processed job_ids to avoid duplicates
    processed_job_ids = set()
    
    total_roles = len(jobs_by_role)
    roles_processed = 0
    total_jobs = sum(len(jobs) for jobs in jobs_by_role.values())
    
    logger.info(f"Processing {total_jobs} jobs across {total_roles} roles for {company}")
    
    for role_name, jobs in jobs_by_role.items():
        roles_processed += 1
        
        # Skip empty role names
        if not role_name or role_name.lower() == "general":
            logger.warning(f"Skipping invalid role: {role_name}")
            continue
        
        # Get or create the role
        try:
            role = get_or_create_role(db, role_name)
        except Exception as role_error:
            logger.error(f"Error getting/creating role {role_name}: {str(role_error)}")
            continue
        
        job_count = len(jobs)
        logger.info(f"Processing role {roles_processed}/{total_roles}: {role_name} ({job_count} jobs)")
        
        # Process each job
        for job_data in jobs:
            # Skip if this job_id was already processed (avoid duplicates)
            job_id = job_data.get("job_id")
            if not job_id or job_id in processed_job_ids:
                continue
            
            # Process the job with our improved handler
            try:
                is_new, job, is_duplicate = upsert_job(db, job_data, company, role)
                
                # Track statistics
                if job:  # Only count if job was successfully upserted
                    processed_job_ids.add(job_id)
                    if is_duplicate:
                        duplicates_skipped += 1
                    elif is_new:
                        jobs_added += 1
                    else:
                        jobs_updated += 1
                else:
                    errors += 1
            except Exception as job_error:
                logger.error(f"Unexpected error processing job {job_id}: {str(job_error)}")
                errors += 1
    
    # Log detailed stats
    job_stats = {
        "company": company,
        "roles_processed": roles_processed,
        "total_jobs": total_jobs,
        "jobs_added": jobs_added,
        "jobs_updated": jobs_updated,
        "duplicates_skipped": duplicates_skipped,
        "errors": errors,
        "unique_jobs": len(processed_job_ids)
    }
    
    logger.info(f"Job processing summary for {company}: {job_stats}")
                
    return jobs_added, jobs_updated

def mark_inactive_jobs(db: Session, company: str, active_job_ids: List[str]) -> int:
    """
    Mark jobs as inactive if they no longer appear in the latest scrape
    
    Returns:
        Number of jobs marked inactive
    """
    # Skip if no active job IDs provided
    if not active_job_ids:
        logger.warning(f"No active job IDs provided for {company}. Skipping mark_inactive_jobs.")
        return 0
    
    try:
        # First, get a count of currently active jobs for this company
        total_active = db.query(Job).filter(
            Job.company == company,
            Job.is_active == True
        ).count()
        
        # Then find jobs that need to be marked inactive
        query = db.query(Job).filter(
            Job.company == company,
            Job.is_active == True,
            ~Job.job_id.in_(active_job_ids)
        )
        
        inactive_count = query.count()
        
        # Only proceed if we found jobs to mark inactive
        if inactive_count > 0:
            # Get details of jobs being marked inactive for logging
            jobs_to_mark = query.all()
            job_titles = [job.job_title for job in jobs_to_mark[:5]]  # First 5 jobs for logging
            
            # Update all matching jobs
            query.update({Job.is_active: False}, synchronize_session=False)
            db.commit()
            
            # Calculate remaining active jobs
            remaining_active = total_active - inactive_count
            
            logger.info(f"Marked {inactive_count} jobs as inactive for {company}. Examples: {', '.join(job_titles[:5])}")
            logger.info(f"Active jobs for {company}: {remaining_active} (was {total_active})")
        else:
            logger.info(f"No jobs to mark inactive for {company}. All {total_active} jobs are still active.")
        
        return inactive_count
    except Exception as e:
        logger.error(f"Error marking inactive jobs for {company}: {str(e)}")
        db.rollback()
        return 0

def get_role_stats(db: Session) -> List[Dict]:
    """Get statistics about roles"""
    try:
        # Find roles and their job counts
        role_stats = db.query(
            Role.name,
            db.func.count(Job.id).label('job_count')
        ).join(
            Job.roles
        ).group_by(
            Role.name
        ).order_by(
            db.func.count(Job.id).desc()
        ).all()
        
        return [{"role": name, "count": count} for name, count in role_stats]
    except Exception as e:
        logger.error(f"Error getting role stats: {str(e)}")
        return []
