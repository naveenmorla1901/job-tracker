"""
Script to directly fix job application status in the database.
This bypasses the API and makes changes directly to the database.
"""
import argparse
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Add project directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import models and database connection
from app.db.models import UserJob, Job, User
from app.db.database import get_db

def fix_job_status(user_email, job_id, applied=False):
    """
    Directly update the job application status in the database.
    
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
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"User with email {user_email} not found.")
            return False
        
        # Check if job exists
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            print(f"Job with ID {job_id} not found.")
            return False
        
        # Check if user already tracks this job
        user_job = db.query(UserJob).filter(
            UserJob.user_id == user.id,
            UserJob.job_id == job_id
        ).first()
        
        if user_job:
            # Update existing record
            print(f"Updating existing record: job_id={job_id}, user_id={user.id}, old status={user_job.is_applied}, new status={applied}")
            user_job.is_applied = applied
            user_job.date_updated = datetime.utcnow()
        else:
            # Create new record
            print(f"Creating new record: job_id={job_id}, user_id={user.id}, status={applied}")
            user_job = UserJob(
                user_id=user.id,
                job_id=job_id,
                is_applied=applied,
                date_saved=datetime.utcnow()
            )
            db.add(user_job)
        
        # Commit changes
        db.commit()
        print(f"Successfully updated job {job_id} status to {'applied' if applied else 'not applied'} for user {user_email}")
        return True
    
    except Exception as e:
        db.rollback()
        print(f"Error updating job status: {str(e)}")
        return False
    finally:
        db.close()

def list_user_jobs(user_email):
    """List all jobs for a user and their application status"""
    # Get database session
    db = next(get_db())
    
    try:
        # Get the user
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"User with email {user_email} not found.")
            return False
        
        # Get all user jobs
        user_jobs = db.query(UserJob, Job).join(
            Job, UserJob.job_id == Job.id
        ).filter(
            UserJob.user_id == user.id
        ).all()
        
        if not user_jobs:
            print(f"No tracked jobs found for user {user_email}.")
            return False
        
        # Print job information
        print(f"Tracked jobs for user {user_email}:")
        print("=" * 80)
        print(f"{'ID':<10} {'Job Title':<40} {'Company':<20} {'Applied':<10}")
        print("-" * 80)
        
        for user_job, job in user_jobs:
            print(f"{job.id:<10} {job.job_title[:38]:<40} {job.company[:18]:<20} {'Yes' if user_job.is_applied else 'No':<10}")
        
        return True
    
    except Exception as e:
        print(f"Error listing jobs: {str(e)}")
        return False
    finally:
        db.close()

def delete_user_job(user_email, job_id):
    """Delete a specific user-job tracking record"""
    # Get database session
    db = next(get_db())
    
    try:
        # Get the user
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            print(f"User with email {user_email} not found.")
            return False
        
        # Delete the record
        result = db.query(UserJob).filter(
            UserJob.user_id == user.id,
            UserJob.job_id == job_id
        ).delete()
        
        if result:
            db.commit()
            print(f"Successfully deleted tracking for job {job_id} for user {user_email}")
            return True
        else:
            print(f"Job {job_id} is not tracked by user {user_email}")
            return False
    
    except Exception as e:
        db.rollback()
        print(f"Error deleting job tracking: {str(e)}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix job application status in the database")
    parser.add_argument("--action", choices=["update", "list", "delete"], default="list", 
                      help="Action to perform (update, list, or delete)")
    parser.add_argument("--user", required=True, help="User email")
    parser.add_argument("--job-id", help="Job ID")
    parser.add_argument("--applied", action="store_true", help="Mark as applied (default is not applied)")
    
    args = parser.parse_args()
    
    if args.action == "update":
        if not args.job_id:
            print("Error: --job-id is required for update action")
            sys.exit(1)
        
        # Call the function to update job status
        success = fix_job_status(args.user, int(args.job_id), args.applied)
        
        if not success:
            print("Failed to update job status.")
            sys.exit(1)
    
    elif args.action == "list":
        # List all user jobs
        list_user_jobs(args.user)
    
    elif args.action == "delete":
        if not args.job_id:
            print("Error: --job-id is required for delete action")
            sys.exit(1)
        
        # Delete the user-job record
        success = delete_user_job(args.user, int(args.job_id))
        
        if not success:
            print("Failed to delete job tracking.")
            sys.exit(1)
