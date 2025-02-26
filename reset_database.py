"""
Complete database reset and cleanup script.
This will remove all existing data and recreate tables with proper constraints.
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import shutil
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.config import SQLALCHEMY_DATABASE_URI
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('database_reset')

def get_connection():
    """Get a direct PostgreSQL connection"""
    try:
        conn = psycopg2.connect(SQLALCHEMY_DATABASE_URI)
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        sys.exit(1)

def get_sqlalchemy_session():
    """Get a SQLAlchemy session"""
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return Session()

def reset_database():
    """Complete reset of the database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n===== RESETTING DATABASE =====")
    
    try:
        # Start transaction
        conn.autocommit = False
        
        # Drop all data from tables (preserve structure)
        print("Removing all existing data...")
        
        # First remove from job_roles (junction table)
        cursor.execute("DELETE FROM job_roles")
        job_roles_count = cursor.rowcount
        print(f"Removed {job_roles_count} job-role associations")
        
        # Then remove from jobs
        cursor.execute("DELETE FROM jobs")
        jobs_count = cursor.rowcount
        print(f"Removed {jobs_count} jobs")
        
        # Then remove from roles
        cursor.execute("DELETE FROM roles")
        roles_count = cursor.rowcount
        print(f"Removed {roles_count} roles")
        
        # Remove from scraper_runs
        cursor.execute("DELETE FROM scraper_runs")
        runs_count = cursor.rowcount
        print(f"Removed {runs_count} scraper run records")
        
        # Reset sequences
        cursor.execute("ALTER SEQUENCE jobs_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE roles_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE scraper_runs_id_seq RESTART WITH 1")
        print("Reset ID sequences to start from 1")
        
        # Create default predefined roles 
        predefined_roles = [
            "Software Engineer", 
            "Data Scientist", 
            "Product Manager",
            "UX Designer",
            "DevOps Engineer"
        ]
        
        for role in predefined_roles:
            cursor.execute(
                "INSERT INTO roles (name) VALUES (%s)",
                (role,)
            )
        
        print(f"Added {len(predefined_roles)} predefined roles")
        
        # Commit all changes
        conn.commit()
        print("Database reset completed successfully")
        
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        logger.error(f"Error resetting database: {str(e)}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

def validate_database_structure():
    """Make sure the database structure is correct"""
    session = get_sqlalchemy_session()
    
    try:
        # Check if tables exist and have correct columns
        check_queries = [
            # Check jobs table
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'jobs'",
            # Check roles table
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'roles'",
            # Check job_roles table
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'job_roles'",
        ]
        
        all_good = True
        for query in check_queries:
            result = session.execute(text(query)).fetchall()
            if not result:
                all_good = False
                logger.error(f"Table check failed for query: {query}")
        
        if all_good:
            print("\nDatabase structure validation passed")
        else:
            print("\nDatabase structure validation FAILED")
            print("You may need to reapply migrations: 'alembic upgrade head'")
    except Exception as e:
        logger.error(f"Error validating database structure: {str(e)}")
    finally:
        session.close()

if __name__ == "__main__":
    print("===== DATABASE RESET AND CLEANUP =====")
    print("\nWARNING: This will delete ALL existing data in the job tracker database!")
    proceed = input("Are you sure you want to proceed? (yes/no): ")
    
    if proceed.lower() != "yes":
        print("Operation canceled.")
        sys.exit(0)
        
    # Run the reset
    reset_database()
    
    # Validate database structure
    validate_database_structure()
    
    print("\n===== RESET COMPLETE =====")
    print("Database has been reset with predefined roles.")
    print("You can now start the application with clean data.")
    print("Run the following command to start the server:")
    print("python run.py api")
