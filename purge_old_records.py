"""
Script to delete job records older than 7 days
"""
import os
import sys
import psycopg2
from datetime import datetime, timedelta
import logging

# Configure logging if running as a standalone script
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

logger = logging.getLogger('job_tracker.purge')

from app.config import SQLALCHEMY_DATABASE_URI

def get_connection():
    """Get a connection to the database"""
    try:
        conn = psycopg2.connect(SQLALCHEMY_DATABASE_URI)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        sys.exit(1)

def purge_old_records(days=7):
    """
    Delete records older than the specified number of days
    
    Returns:
        int: Number of records deleted
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    logger.info(f"===== PURGING RECORDS OLDER THAN {days} DAYS =====")
    
    # Calculate the cutoff date
    cutoff_date = datetime.now() - timedelta(days=days)
    formatted_date = cutoff_date.strftime("%Y-%m-%d")
    
    try:
        # Start transaction
        conn.autocommit = False
        
        # Get the count of jobs that will be deleted
        cursor.execute(
            "SELECT COUNT(*) FROM jobs WHERE date_posted < %s",
            (formatted_date,)
        )
        count_to_delete = cursor.fetchone()[0]
        logger.info(f"Found {count_to_delete} jobs older than {formatted_date}")
        
        if count_to_delete > 0:
            # Get the IDs of jobs to be deleted
            cursor.execute(
                "SELECT id FROM jobs WHERE date_posted < %s",
                (formatted_date,)
            )
            job_ids = [row[0] for row in cursor.fetchall()]
            
            # Delete from job_roles first (due to foreign key constraints)
            if job_ids:
                # Convert list to tuple for SQL IN clause
                if len(job_ids) == 1:
                    job_ids_str = f"({job_ids[0]})"
                else:
                    job_ids_str = str(tuple(job_ids))
                
                cursor.execute(
                    f"DELETE FROM job_roles WHERE job_id IN {job_ids_str}"
                )
                role_rows_deleted = cursor.rowcount
                logger.info(f"Deleted {role_rows_deleted} entries from job_roles table")
            
            # Now delete the jobs
            cursor.execute(
                "DELETE FROM jobs WHERE date_posted < %s",
                (formatted_date,)
            )
            job_rows_deleted = cursor.rowcount
            logger.info(f"Deleted {job_rows_deleted} jobs from the database")
            
            # Commit the changes
            conn.commit()
            logger.info("Purge completed successfully")
            return job_rows_deleted
        else:
            logger.info("No records to delete")
            return 0
        
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        logger.error(f"Error purging old records: {str(e)}")
        return 0
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # Default to 7 days
    days = 7
    
    # Check for command-line argument
    if len(sys.argv) > 1:
        try:
            days = int(sys.argv[1])
        except ValueError:
            logger.error(f"Invalid number of days: {sys.argv[1]}")
            logger.info("Using default: 7 days")
    
    deleted_count = purge_old_records(days)
    logger.info(f"Purge completed: {deleted_count} jobs removed")
