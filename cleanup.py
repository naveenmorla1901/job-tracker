"""
Script to clean up the project and fix data issues
"""
import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
import shutil
from app.config import SQLALCHEMY_DATABASE_URI

def get_connection():
    """Get a connection to the database"""
    try:
        conn = psycopg2.connect(SQLALCHEMY_DATABASE_URI)
        return conn
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        sys.exit(1)

def cleanup_database():
    """Clean up the database by removing duplicate records and fixing issues"""
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n===== CLEANING UP DATABASE =====")
    
    try:
        # Start transaction
        conn.autocommit = False
        
        # 1. Find and remove duplicate jobs
        print("Checking for duplicate jobs...")
        cursor.execute("""
            WITH duplicate_jobs AS (
                SELECT job_id, company, MIN(id) as keep_id
                FROM jobs
                GROUP BY job_id, company
                HAVING COUNT(*) > 1
            )
            DELETE FROM jobs
            WHERE id IN (
                SELECT j.id
                FROM jobs j
                JOIN duplicate_jobs d ON j.job_id = d.job_id AND j.company = d.company
                WHERE j.id <> d.keep_id
            )
            RETURNING id
        """)
        deleted_count = len(cursor.fetchall() or [])
        print(f"Removed {deleted_count} duplicate job entries")
        
        # 2. Make sure all jobs have at least one role
        print("Checking for jobs without roles...")
        cursor.execute("""
            SELECT j.id, j.job_title, j.company
            FROM jobs j
            LEFT JOIN job_roles jr ON j.id = jr.job_id
            WHERE jr.job_id IS NULL
        """)
        jobs_without_roles = cursor.fetchall() or []
        
        # Get default role ID or create one
        cursor.execute("SELECT id FROM roles WHERE name = 'General' LIMIT 1")
        result = cursor.fetchone()
        if result:
            default_role_id = result[0]
        else:
            cursor.execute("INSERT INTO roles (name) VALUES ('General') RETURNING id")
            default_role_id = cursor.fetchone()[0]
        
        # Add default role to jobs without roles
        for job in jobs_without_roles:
            cursor.execute(
                "INSERT INTO job_roles (job_id, role_id) VALUES (%s, %s)",
                (job[0], default_role_id)
            )
        
        print(f"Added default role to {len(jobs_without_roles)} jobs without roles")
        
        # 3. Fix any NULL values in important fields
        print("Fixing NULL values in critical fields...")
        cursor.execute("""
            UPDATE jobs
            SET 
                job_title = CASE WHEN job_title IS NULL OR job_title = '' THEN 'Untitled Position' ELSE job_title END,
                location = CASE WHEN location IS NULL OR location = '' THEN 'Unknown Location' ELSE location END,
                date_posted = CASE WHEN date_posted IS NULL THEN CURRENT_DATE ELSE date_posted END,
                is_active = CASE WHEN is_active IS NULL THEN TRUE ELSE is_active END
            WHERE
                job_title IS NULL OR job_title = '' OR
                location IS NULL OR location = '' OR
                date_posted IS NULL OR
                is_active IS NULL
            RETURNING id
        """)
        fixed_count = len(cursor.fetchall() or [])
        print(f"Fixed {fixed_count} records with NULL values")
        
        # Commit all changes
        conn.commit()
        print("Database cleanup completed successfully")
        
    except Exception as e:
        # Rollback in case of error
        conn.rollback()
        print(f"Error cleaning up database: {str(e)}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

def cleanup_project_files():
    """Clean up unnecessary project files"""
    print("\n===== CLEANING UP PROJECT FILES =====")
    
    # Files to remove
    files_to_remove = [
        "test_scraper.py",
        "test_db_integration.py"
    ]
    
    # Files to keep (renamed from test files)
    files_to_rename = {
        "full_integration_test.py": "integration_test.py"
    }
    
    # Remove unnecessary files
    for file in files_to_remove:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"Removed: {file}")
            except Exception as e:
                print(f"Error removing {file}: {str(e)}")
    
    # Rename files
    for old_name, new_name in files_to_rename.items():
        if os.path.exists(old_name):
            try:
                # If destination exists, remove it first
                if os.path.exists(new_name):
                    os.remove(new_name)
                os.rename(old_name, new_name)
                print(f"Renamed: {old_name} -> {new_name}")
            except Exception as e:
                print(f"Error renaming {old_name}: {str(e)}")
    
    # Cleanup pycache directories
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            pycache_path = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(pycache_path)
                print(f"Removed: {pycache_path}")
            except Exception as e:
                print(f"Error removing {pycache_path}: {str(e)}")
    
    print("Project file cleanup completed")

if __name__ == "__main__":
    print("======= PROJECT CLEANUP =======")
    
    try:
        cleanup_database()
        cleanup_project_files()
        
        print("\n======= CLEANUP COMPLETE =======")
        print("Your project has been cleaned up and is ready for final use.")
        print("You can run the application with: python run.py api")
        print("And the dashboard with: python run.py dashboard")
        
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
        sys.exit(1)
