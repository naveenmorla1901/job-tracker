"""
Create an admin user for the Job Tracker application
"""
import argparse
import os
import sys
import logging
from sqlalchemy.orm import Session

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("job_tracker.create_admin")

# Add the current directory to the path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.db.database import get_db
from app.db import crud_user
from app.db.models import UserRole
from app.auth.security import get_password_hash

def create_admin_user(email, password):
    """Create a new admin user"""
    logger.info(f"Creating admin user: {email}")
    
    try:
        # Get database session
        db = next(get_db())
        
        # Check if user exists
        existing_user = crud_user.get_user_by_email(db, email)
        if existing_user:
            # If user exists but is not admin, update their role
            if existing_user.role != UserRole.ADMIN:
                logger.info(f"User {email} exists. Updating role to ADMIN")
                existing_user.role = UserRole.ADMIN
                db.commit()
                logger.info(f"User {email} updated to ADMIN role successfully")
            else:
                logger.info(f"User {email} already exists with ADMIN role")
            return
        
        # Create new admin user
        user = crud_user.create_user(
            db=db, 
            email=email, 
            password=password, 
            role=UserRole.ADMIN
        )
        
        logger.info(f"Admin user {email} created successfully")
        
    except Exception as e:
        logger.error(f"Error creating admin user: {str(e)}")
        raise

def main():
    """Main function to create an admin user from command line"""
    parser = argparse.ArgumentParser(description="Create an admin user for Job Tracker")
    parser.add_argument("email", help="Admin user email")
    parser.add_argument("password", help="Admin user password")
    
    args = parser.parse_args()
    
    try:
        create_admin_user(args.email, args.password)
    except Exception as e:
        logger.error(f"Failed to create admin user: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
