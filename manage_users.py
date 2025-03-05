#!/usr/bin/env python
"""
User management utility for Job Tracker

Usage:
    python manage_users.py list
    python manage_users.py create <email> <password> [--role admin|premium|regular]
    python manage_users.py info <user_id>
    python manage_users.py delete <user_id>
    python manage_users.py change-password <user_id> <new_password>
    python manage_users.py change-role <user_id> <new_role>
"""

import sys
import argparse
import logging
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db, engine
from app.db.models import User, UserRole
from app.db import crud_user

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('manage_users')


def format_user(user: User) -> str:
    """Format user information for display"""
    created = user.registration_date.strftime('%Y-%m-%d %H:%M:%S') if user.registration_date else 'N/A'
    last_login = user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'N/A'
    
    return f"""
User ID: {user.id}
Email: {user.email}
Role: {user.role.value}
Status: {'Active' if user.is_active else 'Inactive'}
Created: {created}
Last Login: {last_login}
"""


def list_users(db: Session):
    """List all users in the database"""
    users = crud_user.list_users(db)
    if not users:
        print("No users found in the database.")
        return
    
    print(f"Found {len(users)} users:")
    for user in users:
        print(f"ID: {user.id:<5} | Email: {user.email:<30} | Role: {user.role.value:<10} | Status: {'Active' if user.is_active else 'Inactive'}")


def create_user(db: Session, email: str, password: str, role: str = 'regular'):
    """Create a new user"""
    try:
        # Convert role string to enum
        role_enum = UserRole.REGULAR
        if role.lower() == 'admin':
            role_enum = UserRole.ADMIN
        elif role.lower() == 'premium':
            role_enum = UserRole.PREMIUM
        
        user = crud_user.create_user(db, email, password, role_enum)
        print(f"User created successfully:")
        print(format_user(user))
    except ValueError as e:
        print(f"Error creating user: {str(e)}")


def get_user_info(db: Session, user_id: int):
    """Get detailed information about a user"""
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        print(f"User with ID {user_id} not found.")
        return
    
    print(format_user(user))
    
    # Get tracked jobs count
    tracked_jobs = len(crud_user.get_tracked_jobs(db, user_id))
    applied_jobs = len(crud_user.get_tracked_jobs(db, user_id, applied_only=True))
    
    print(f"Tracked Jobs: {tracked_jobs}")
    print(f"Applied Jobs: {applied_jobs}")


def delete_user(db: Session, user_id: int):
    """Delete a user"""
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        print(f"User with ID {user_id} not found.")
        return
    
    print(f"You are about to delete the following user:")
    print(format_user(user))
    
    confirmation = input("Are you sure you want to delete this user? (yes/no): ")
    if confirmation.lower() != 'yes':
        print("User deletion canceled.")
        return
    
    success = crud_user.delete_user(db, user_id)
    if success:
        print(f"User {user.email} (ID: {user_id}) has been deleted.")
    else:
        print(f"Failed to delete user. Please check the logs for details.")


def change_password(db: Session, user_id: int, new_password: str):
    """Change a user's password"""
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        print(f"User with ID {user_id} not found.")
        return
    
    success = crud_user.update_user_password(db, user_id, new_password)
    if success:
        print(f"Password updated successfully for user {user.email} (ID: {user_id}).")
    else:
        print(f"Failed to update password. Please check the logs for details.")


def change_role(db: Session, user_id: int, new_role: str):
    """Change a user's role"""
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        print(f"User with ID {user_id} not found.")
        return
    
    # Convert role string to enum
    try:
        if new_role.lower() == 'admin':
            role_enum = UserRole.ADMIN
        elif new_role.lower() == 'premium':
            role_enum = UserRole.PREMIUM
        elif new_role.lower() == 'regular':
            role_enum = UserRole.REGULAR
        else:
            print(f"Invalid role: {new_role}. Valid roles are: admin, premium, regular")
            return
        
        success = crud_user.update_user_role(db, user_id, role_enum)
        if success:
            print(f"Role updated to {new_role} for user {user.email} (ID: {user_id}).")
        else:
            print(f"Failed to update role. Please check the logs for details.")
    except Exception as e:
        print(f"Error updating role: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description='Job Tracker User Management Utility')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List users command
    list_parser = subparsers.add_parser('list', help='List all users')
    
    # Create user command
    create_parser = subparsers.add_parser('create', help='Create a new user')
    create_parser.add_argument('email', help='User email')
    create_parser.add_argument('password', help='User password')
    create_parser.add_argument('--role', choices=['admin', 'premium', 'regular'], default='regular', help='User role')
    
    # Get user info command
    info_parser = subparsers.add_parser('info', help='Get user information')
    info_parser.add_argument('user_id', type=int, help='User ID')
    
    # Delete user command
    delete_parser = subparsers.add_parser('delete', help='Delete a user')
    delete_parser.add_argument('user_id', type=int, help='User ID')
    
    # Change password command
    pwd_parser = subparsers.add_parser('change-password', help='Change user password')
    pwd_parser.add_argument('user_id', type=int, help='User ID')
    pwd_parser.add_argument('new_password', help='New password')
    
    # Change role command
    role_parser = subparsers.add_parser('change-role', help='Change user role')
    role_parser.add_argument('user_id', type=int, help='User ID')
    role_parser.add_argument('new_role', choices=['admin', 'premium', 'regular'], help='New role')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Get database session
    try:
        db = next(get_db())
        
        if args.command == 'list':
            list_users(db)
        elif args.command == 'create':
            create_user(db, args.email, args.password, args.role)
        elif args.command == 'info':
            get_user_info(db, args.user_id)
        elif args.command == 'delete':
            delete_user(db, args.user_id)
        elif args.command == 'change-password':
            change_password(db, args.user_id, args.new_password)
        elif args.command == 'change-role':
            change_role(db, args.user_id, args.new_role)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()


if __name__ == '__main__':
    main()
