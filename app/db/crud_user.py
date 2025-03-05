# app/db/crud_user.py
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional, Dict, Any

import logging
from app.db.models import User, UserJob, Job, UserRole
from app.auth.security import get_password_hash, verify_password

# Set up logger
logger = logging.getLogger('job_tracker.crud_user')

def create_user(db: Session, email: str, password: str, role: UserRole = UserRole.REGULAR) -> User:
    """
    Create a new user in the database.
    
    Args:
        db: Database session
        email: User's email (must be unique)
        password: Plain password to be hashed
        role: User role (defaults to REGULAR)
        
    Returns:
        Created user object
        
    Raises:
        ValueError: If user with this email already exists
    """
    # Check if user exists
    existing_user = get_user_by_email(db, email)
    if existing_user:
        raise ValueError(f"User with email {email} already exists")
    
    # Create new user
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        role=role,
        registration_date=datetime.utcnow(),
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"Created new user: {email}")
    
    return user

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authenticate a user with email and password.
    
    Args:
        db: Database session
        email: User's email
        password: Plain password to verify
        
    Returns:
        User object if authentication successful, None otherwise
    """
    user = get_user_by_email(db, email)
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    # Update last login timestamp
    user.last_login = datetime.utcnow()
    db.commit()
    
    return user

def update_user_password(db: Session, user_id: int, new_password: str) -> bool:
    """
    Update a user's password.
    
    Args:
        db: Database session
        user_id: User ID
        new_password: New plain password to be hashed
        
    Returns:
        True if successful, False otherwise
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        logger.info(f"Updated password for user ID {user_id}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating password for user ID {user_id}: {str(e)}")
        return False

def update_user_role(db: Session, user_id: int, new_role: UserRole) -> bool:
    """
    Update a user's role.
    
    Args:
        db: Database session
        user_id: User ID
        new_role: New role to assign
        
    Returns:
        True if successful, False otherwise
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            return False
        
        user.role = new_role
        db.commit()
        logger.info(f"Updated role for user ID {user_id} to {new_role.value}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating role for user ID {user_id}: {str(e)}")
        return False

def list_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    List users with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List of users
    """
    return db.query(User).offset(skip).limit(limit).all()

def track_job(db: Session, user_id: int, job_id: int) -> Optional[UserJob]:
    """
    Track a job for a user (save it to their list).
    
    Args:
        db: Database session
        user_id: User ID
        job_id: Job ID
        
    Returns:
        UserJob object if successful, None otherwise
    """
    try:
        # Check if already tracked
        existing = db.query(UserJob).filter(
            UserJob.user_id == user_id,
            UserJob.job_id == job_id
        ).first()
        
        if existing:
            # Already tracked, just return it
            return existing
        
        # Create new tracking entry
        user_job = UserJob(
            user_id=user_id,
            job_id=job_id,
            is_applied=False,
            date_saved=datetime.utcnow()
        )
        
        db.add(user_job)
        db.commit()
        logger.info(f"User {user_id} is now tracking job {job_id}")
        
        return user_job
    except Exception as e:
        db.rollback()
        logger.error(f"Error tracking job {job_id} for user {user_id}: {str(e)}")
        return None

def untrack_job(db: Session, user_id: int, job_id: int) -> bool:
    """
    Remove a job from a user's tracked list.
    
    Args:
        db: Database session
        user_id: User ID
        job_id: Job ID
        
    Returns:
        True if successful, False otherwise
    """
    try:
        result = db.query(UserJob).filter(
            UserJob.user_id == user_id,
            UserJob.job_id == job_id
        ).delete()
        
        db.commit()
        
        if result:
            logger.info(f"User {user_id} is no longer tracking job {job_id}")
            return True
        else:
            logger.warning(f"Job {job_id} was not tracked by user {user_id}")
            return False
    except Exception as e:
        db.rollback()
        logger.error(f"Error untracking job {job_id} for user {user_id}: {str(e)}")
        return False

def mark_job_applied(db: Session, user_id: int, job_id: int, applied: bool = True) -> bool:
    """
    Mark a job as applied or not applied.
    
    Args:
        db: Database session
        user_id: User ID
        job_id: Job ID
        applied: True if applied, False if not
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the user-job relationship
        user_job = db.query(UserJob).filter(
            UserJob.user_id == user_id,
            UserJob.job_id == job_id
        ).first()
        
        if not user_job:
            # Not tracked yet, create it
            user_job = UserJob(
                user_id=user_id,
                job_id=job_id,
                is_applied=applied,
                date_saved=datetime.utcnow()
            )
            db.add(user_job)
        else:
            # Update existing
            user_job.is_applied = applied
            user_job.date_updated = datetime.utcnow()
        
        db.commit()
        logger.info(f"User {user_id} marked job {job_id} as {'applied' if applied else 'not applied'}")
        
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error marking job {job_id} as {'applied' if applied else 'not applied'} for user {user_id}: {str(e)}")
        return False

def get_tracked_jobs(db: Session, user_id: int, applied_only: bool = False) -> List[Dict[str, Any]]:
    """
    Get jobs tracked by a user.
    
    Args:
        db: Database session
        user_id: User ID
        applied_only: If True, only return jobs marked as applied
        
    Returns:
        List of job dictionaries with tracking status
    """
    try:
        # Start with base query
        query = db.query(
            Job,
            UserJob.is_applied,
            UserJob.date_saved,
            UserJob.date_updated
        ).join(
            UserJob, Job.id == UserJob.job_id
        ).filter(
            UserJob.user_id == user_id
        )
        
        # Apply additional filters if needed
        if applied_only:
            query = query.filter(UserJob.is_applied == True)
        
        # Execute query
        results = query.order_by(Job.date_posted.desc()).all()
        
        # Format results
        tracked_jobs = []
        for job, is_applied, date_saved, date_updated in results:
            job_dict = {
                "id": job.id,
                "job_id": job.job_id,
                "job_title": job.job_title,
                "company": job.company,
                "location": job.location,
                "date_posted": job.date_posted,
                "job_url": job.job_url,
                "employment_type": job.employment_type,
                "is_active": job.is_active,
                "tracking": {
                    "is_applied": is_applied,
                    "date_saved": date_saved,
                    "date_updated": date_updated
                }
            }
            tracked_jobs.append(job_dict)
        
        return tracked_jobs
    except Exception as e:
        logger.error(f"Error getting tracked jobs for user {user_id}: {str(e)}")
        return []

def delete_user(db: Session, user_id: int) -> bool:
    """
    Delete a user from the database.
    
    Args:
        db: Database session
        user_id: ID of the user to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        user = get_user_by_id(db, user_id)
        if not user:
            logger.warning(f"Attempted to delete non-existent user with ID {user_id}")
            return False
        
        # First delete related UserJob records
        db.query(UserJob).filter(UserJob.user_id == user_id).delete()
        
        # Then delete the user
        db.delete(user)
        db.commit()
        logger.info(f"Successfully deleted user ID {user_id}")
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user ID {user_id}: {str(e)}")
        return False

def get_database_stats(db: Session) -> Dict[str, Any]:
    """
    Get statistics about the database.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with statistics
    """
    try:
        stats = {
            "users": {
                "total": db.query(User).count(),
                "active": db.query(User).filter(User.is_active == True).count(),
                "roles": {
                    "regular": db.query(User).filter(User.role == UserRole.REGULAR).count(),
                    "premium": db.query(User).filter(User.role == UserRole.PREMIUM).count(),
                    "admin": db.query(User).filter(User.role == UserRole.ADMIN).count(),
                },
                "recent": db.query(User).order_by(User.registration_date.desc()).limit(5).all()
            },
            "jobs": {
                "total": db.query(Job).count(),
                "active": db.query(Job).filter(Job.is_active == True).count(),
                "tracked": db.query(UserJob).count()
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        return stats
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return {"error": str(e)}
