"""
Direct job actions component for the dashboard
This bypasses the API and directly modifies the database
"""
import streamlit as st
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.db.database import get_db
from app.db.models import UserJob, Job, User

# Configure logging
logger = logging.getLogger("job_tracker.dashboard.direct_job_actions")

def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def mark_job_applied_direct(user_email: str, job_id: int, applied: bool = True):
    """
    Directly mark a job as applied or not applied in the database.
    
    Args:
        user_email: Email of the user
        job_id: ID of the job
        applied: New applied status (True or False)
    
    Returns:
        True if successful, False otherwise
    """
    # Get database session
    db = next(get_db())
    
    try:
        # First get the user
        user = get_user_by_email(db, user_email)
        if not user:
            logger.error(f"User with email {user_email} not found.")
            return False
        
        # Check if job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job with ID {job_id} not found.")
            return False
        
        # Check if user already tracks this job
        user_job = db.query(UserJob).filter(
            UserJob.user_id == user.id,
            UserJob.job_id == job_id
        ).first()
        
        if user_job:
            # Update existing record
            logger.info(f"Updating existing record: job_id={job_id}, user_id={user.id}, old status={user_job.is_applied}, new status={applied}")
            user_job.is_applied = applied
            user_job.date_updated = datetime.utcnow()
        else:
            # Create new record
            logger.info(f"Creating new record: job_id={job_id}, user_id={user.id}, status={applied}")
            user_job = UserJob(
                user_id=user.id,
                job_id=job_id,
                is_applied=applied,
                date_saved=datetime.utcnow()
            )
            db.add(user_job)
        
        # Commit changes
        db.commit()
        logger.info(f"Successfully updated job {job_id} status to {'applied' if applied else 'not applied'} for user {user_email}")
        return True
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating job status: {str(e)}")
        return False
    finally:
        db.close()

def delete_job_tracking_direct(user_email: str, job_id: int):
    """
    Directly delete a job tracking record.
    
    Args:
        user_email: Email of the user
        job_id: ID of the job
    
    Returns:
        True if successful, False otherwise
    """
    # Get database session
    db = next(get_db())
    
    try:
        # Get the user
        user = get_user_by_email(db, user_email)
        if not user:
            logger.error(f"User with email {user_email} not found.")
            return False
        
        # Delete the record
        result = db.query(UserJob).filter(
            UserJob.user_id == user.id,
            UserJob.job_id == job_id
        ).delete()
        
        if result:
            db.commit()
            logger.info(f"Successfully deleted tracking for job {job_id} for user {user_email}")
            return True
        else:
            logger.warning(f"Job {job_id} is not tracked by user {user_email}")
            return False
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting job tracking: {str(e)}")
        return False
    finally:
        db.close()

def get_user_tracked_jobs_direct(user_email: str):
    """
    Get all jobs tracked by a user directly from the database.
    
    Args:
        user_email: Email of the user
    
    Returns:
        Dictionary of job_id -> applied status
    """
    # Get database session
    db = next(get_db())
    
    try:
        # Get the user
        user = get_user_by_email(db, user_email)
        if not user:
            logger.error(f"User with email {user_email} not found.")
            return {}
        
        # Get all user jobs
        user_jobs = db.query(UserJob).filter(
            UserJob.user_id == user.id
        ).all()
        
        # Convert to dictionary
        tracked_jobs = {}
        for user_job in user_jobs:
            tracked_jobs[str(user_job.job_id)] = user_job.is_applied
        
        logger.info(f"Found {len(tracked_jobs)} tracked jobs for user {user_email}")
        return tracked_jobs
    
    except Exception as e:
        logger.error(f"Error getting tracked jobs: {str(e)}")
        return {}
    finally:
        db.close()
