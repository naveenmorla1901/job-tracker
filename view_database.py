#!/usr/bin/env python
"""
Database viewer utility for Job Tracker

Usage:
    python view_database.py tables
    python view_database.py users [--limit N]
    python view_database.py jobs [--limit N] [--company COMPANY]
    python view_database.py roles
    python view_database.py stats
"""

import sys
import argparse
import logging
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from tabulate import tabulate
from datetime import datetime
import json

from app.db.database import get_db, engine
from app.db.models import User, Job, Role, UserJob, Base
from app.db import crud_user

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('view_database')


def list_tables(db: Session):
    """List all tables in the database"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print("Database tables:")
    for i, table in enumerate(tables, 1):
        print(f"{i}. {table}")


def view_users(db: Session, limit: int = 10):
    """View users in the database"""
    users = db.query(User).limit(limit).all()
    
    if not users:
        print("No users found in the database.")
        return
    
    rows = []
    for user in users:
        rows.append([
            user.id,
            user.email,
            user.role.value,
            'Yes' if user.is_active else 'No',
            user.registration_date.strftime('%Y-%m-%d %H:%M') if user.registration_date else 'N/A',
            user.last_login.strftime('%Y-%m-%d %H:%M') if user.last_login else 'N/A'
        ])
    
    headers = ['ID', 'Email', 'Role', 'Active', 'Registered', 'Last Login']
    print(tabulate(rows, headers=headers, tablefmt='pretty'))
    
    user_count = db.query(User).count()
    if user_count > limit:
        print(f"\nShowing {limit} of {user_count} users. Use --limit to show more.")


def view_jobs(db: Session, limit: int = 10, company: str = None):
    """View jobs in the database"""
    query = db.query(Job)
    
    if company:
        query = query.filter(Job.company == company)
    
    jobs = query.order_by(Job.date_posted.desc()).limit(limit).all()
    
    if not jobs:
        print(f"No jobs found in the database{' for company ' + company if company else ''}.")
        return
    
    rows = []
    for job in jobs:
        rows.append([
            job.id,
            job.job_title[:30] + '...' if len(job.job_title) > 30 else job.job_title,
            job.company,
            job.location[:20] + '...' if len(job.location) > 20 else job.location,
            job.date_posted.strftime('%Y-%m-%d') if job.date_posted else 'N/A',
            'Yes' if job.is_active else 'No',
            ', '.join([role.name for role in job.roles])
        ])
    
    headers = ['ID', 'Title', 'Company', 'Location', 'Posted', 'Active', 'Roles']
    print(tabulate(rows, headers=headers, tablefmt='pretty'))
    
    total_jobs = db.query(Job)
    if company:
        total_jobs = total_jobs.filter(Job.company == company)
    job_count = total_jobs.count()
    
    if job_count > limit:
        print(f"\nShowing {limit} of {job_count} jobs. Use --limit to show more.")


def view_roles(db: Session):
    """View roles and their job counts"""
    roles = db.query(
        Role.name,
        db.func.count(Job.id).label('job_count')
    ).join(
        Job.roles,
        isouter=True
    ).group_by(
        Role.name
    ).order_by(
        db.func.count(Job.id).desc()
    ).all()
    
    if not roles:
        print("No roles found in the database.")
        return
    
    rows = []
    for role_name, job_count in roles:
        rows.append([role_name, job_count])
    
    headers = ['Role', 'Job Count']
    print(tabulate(rows, headers=headers, tablefmt='pretty'))


def view_stats(db: Session):
    """View database statistics"""
    stats = {
        "Users": {
            "Total": db.query(User).count(),
            "Active": db.query(User).filter(User.is_active == True).count(),
            "Admin": db.query(User).filter(User.role == 'admin').count(),
            "Premium": db.query(User).filter(User.role == 'premium').count(),
            "Regular": db.query(User).filter(User.role == 'regular').count()
        },
        "Jobs": {
            "Total": db.query(Job).count(),
            "Active": db.query(Job).filter(Job.is_active == True).count(),
            "Companies": db.query(Job.company).distinct().count()
        },
        "Tracked Jobs": {
            "Total": db.query(UserJob).count(),
            "Applied": db.query(UserJob).filter(UserJob.is_applied == True).count()
        },
        "Roles": {
            "Total": db.query(Role).count()
        }
    }
    
    # Print stats in a formatted way
    print("=== Database Statistics ===\n")
    for section, section_stats in stats.items():
        print(f"--- {section} ---")
        for stat, value in section_stats.items():
            print(f"{stat}: {value}")
        print()
    
    # Top 5 companies by job count
    top_companies = db.query(
        Job.company,
        db.func.count(Job.id).label('job_count')
    ).group_by(
        Job.company
    ).order_by(
        db.func.count(Job.id).desc()
    ).limit(5).all()
    
    print("--- Top Companies ---")
    for company, count in top_companies:
        print(f"{company}: {count} jobs")
    print()
    
    # Most recent jobs
    recent_jobs = db.query(
        Job.job_title,
        Job.company,
        Job.date_posted
    ).order_by(
        Job.date_posted.desc()
    ).limit(5).all()
    
    print("--- Most Recent Jobs ---")
    for title, company, date in recent_jobs:
        print(f"{title} at {company} - {date.strftime('%Y-%m-%d') if date else 'N/A'}")


def main():
    parser = argparse.ArgumentParser(description='Job Tracker Database Viewer')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # List tables command
    tables_parser = subparsers.add_parser('tables', help='List all database tables')
    
    # View users command
    users_parser = subparsers.add_parser('users', help='View users')
    users_parser.add_argument('--limit', type=int, default=10, help='Maximum number of users to show')
    
    # View jobs command
    jobs_parser = subparsers.add_parser('jobs', help='View jobs')
    jobs_parser.add_argument('--limit', type=int, default=10, help='Maximum number of jobs to show')
    jobs_parser.add_argument('--company', help='Filter jobs by company')
    
    # View roles command
    roles_parser = subparsers.add_parser('roles', help='View roles and job counts')
    
    # View stats command
    stats_parser = subparsers.add_parser('stats', help='View database statistics')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Get database session
    try:
        db = next(get_db())
        
        if args.command == 'tables':
            list_tables(db)
        elif args.command == 'users':
            view_users(db, args.limit)
        elif args.command == 'jobs':
            view_jobs(db, args.limit, args.company)
        elif args.command == 'roles':
            view_roles(db)
        elif args.command == 'stats':
            view_stats(db)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if 'db' in locals():
            db.close()


if __name__ == '__main__':
    main()
