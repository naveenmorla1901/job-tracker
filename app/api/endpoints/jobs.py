from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Union
from datetime import datetime, timedelta
import logging

from app.db.database import get_db
from app.db.models import Job, Role
from app.db.crud import get_or_create_role
from app.role_categories import CATEGORIES, classify_title

# Configure logger
logger = logging.getLogger("job_tracker.api")

router = APIRouter()

@router.get("/")
def get_jobs(
    db: Session = Depends(get_db),
    role: Optional[List[str]] = Query(None),  # Changed to List
    company: Optional[List[str]] = Query(None),  # Changed to List
    location: Optional[str] = None,
    employment_type: Optional[str] = None,
    search: Optional[str] = None,
    days: Optional[int] = Query(None, description="Jobs posted within last N days"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0)
):
    """
    Get job listings with enhanced filtering
    """
    # Add debugging logs
    logger.info(f"Request params: role={role}, company={company}, days={days}, location={location}, employment_type={employment_type}")
    
    query = db.query(Job).filter(Job.is_active == True)
    
    # Apply filters
    if role:
        if isinstance(role, list):
            # Get all role objects
            role_objs = db.query(Role).filter(Role.name.in_(role)).all()
            if role_objs:
                # Filter jobs that have any of the selected roles
                role_ids = [r.id for r in role_objs]
                query = query.filter(Job.roles.any(Role.id.in_(role_ids)))
            else:
                return {"jobs": [], "total": 0}
        else:
            # For backward compatibility with single role
            role_obj = db.query(Role).filter(Role.name == role).first()
            if role_obj:
                query = query.filter(Job.roles.any(Role.id == role_obj.id))
            else:
                return {"jobs": [], "total": 0}
    
    if company:
        if isinstance(company, list):
            # Filter for multiple companies
            query = query.filter(Job.company.in_(company))
        else:
            # For backward compatibility with single company
            query = query.filter(Job.company == company)
    
    if location:
        query = query.filter(Job.location.ilike(f"%{location}%"))
    
    if employment_type:
        query = query.filter(Job.employment_type == employment_type)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                Job.job_title.ilike(search_term),
                Job.description.ilike(search_term)
            )
        )
    
    if days:
        # Calculate cutoff with time component and ensure timezone handling
        now = datetime.utcnow()
        logger.info(f"Current time: {now}")
        
        # IMPROVED DATE FILTERING:
        # 1. Increase buffer time to ensure we capture all jobs 
        # 2. Always include the full days for the range requested
        
        # Add a larger buffer (12 hours) to ensure we don't miss jobs
        date_cutoff = now - timedelta(days=days, hours=12)
        
        # Always include the full day by setting to start of day
        # For example, if days=3, we want to include all jobs from 3 days ago, not just from 72 hours ago
        day_start = datetime(date_cutoff.year, date_cutoff.month, date_cutoff.day, 0, 0, 0)
        
        logger.info(f"Date filter: showing jobs since {day_start} (inclusive), requested days: {days}")
        
        # Apply the filter using the day start to ensure we get full days
        query = query.filter(Job.date_posted >= day_start)
    
    # Get total before pagination
    total = query.count()
    
    # Order by date posted (newest first) and apply pagination
    query = query.order_by(Job.date_posted.desc()).offset(offset).limit(limit)
    
    jobs = query.all()
    
    # Log the number of jobs found
    logger.info(f"Found {len(jobs)} jobs (total: {total})")
    
    # Format jobs for response with more details
    jobs_list = []
    for job in jobs:
        try:
            job_dict = {
                "id": job.id,
                "job_id": job.job_id,
                "job_title": job.job_title,
                "company": job.company,
                "location": job.location,
                "job_url": job.job_url,
                "date_posted": job.date_posted.strftime("%Y-%m-%d"),
                "employment_type": job.employment_type,
                "roles": [role.name for role in job.roles],
                "first_seen": job.first_seen.strftime("%Y-%m-%d %H:%M:%S"),
            }
            jobs_list.append(job_dict)
        except Exception as e:
            logger.error(f"Error formatting job {job.id}: {str(e)}")
    
    return {"jobs": jobs_list, "total": total}

def _day_start_cutoff(days: int) -> datetime:
    """Start of the day `days` days ago (UTC), with the same 12h buffer as get_jobs."""
    date_cutoff = datetime.utcnow() - timedelta(days=days, hours=12)
    return datetime(date_cutoff.year, date_cutoff.month, date_cutoff.day)


@router.get("/ai-ds")
def get_ai_ds_jobs(
    db: Session = Depends(get_db),
    days: int = Query(7, ge=1, le=60),
    category: Optional[List[str]] = Query(None, description="Subset of /ai-ds/categories"),
    company: Optional[List[str]] = Query(None),
    search: Optional[str] = None,
):
    """Active AI / data jobs, classified by title on the server.

    Filtering by title (not the scraper's search-term role tag) drops loose
    matches like "Construction Engineer", and doing it before counting means
    the total is exact with no 1000-row truncation.
    """
    wanted = set(category or CATEGORIES)

    query = db.query(
        Job.id, Job.job_id, Job.job_title, Job.company, Job.location,
        Job.job_url, Job.date_posted, Job.employment_type, Job.first_seen,
    ).filter(Job.is_active == True, Job.date_posted >= _day_start_cutoff(days))

    if company:
        query = query.filter(Job.company.in_(company))
    if search:
        term = f"%{search}%"
        query = query.filter(or_(Job.job_title.ilike(term), Job.description.ilike(term)))

    jobs_list = []
    category_counts = {name: 0 for name in CATEGORIES}
    for row in query.order_by(Job.date_posted.desc()).all():
        categories = [c for c in classify_title(row.job_title) if c in wanted]
        if not categories:
            continue
        for c in categories:
            category_counts[c] += 1
        jobs_list.append({
            "id": row.id,
            "job_id": row.job_id,
            "job_title": row.job_title,
            "company": row.company,
            "location": row.location,
            "job_url": row.job_url,
            "date_posted": row.date_posted.strftime("%Y-%m-%d") if row.date_posted else None,
            "employment_type": row.employment_type,
            "categories": categories,
            "first_seen": row.first_seen.strftime("%Y-%m-%d %H:%M:%S") if row.first_seen else None,
        })

    return {"jobs": jobs_list, "total": len(jobs_list), "category_counts": category_counts}


@router.get("/ai-ds/categories")
def get_ai_ds_categories():
    """Category names accepted by /ai-ds."""
    return {"categories": CATEGORIES}


@router.get("/roles")
def get_roles(db: Session = Depends(get_db)):
    """Get all available role categories"""
    try:
        roles = db.query(Role).all()
        return {"roles": [role.name for role in roles]}
    except Exception as e:
        logger.error(f"Error fetching roles: {str(e)}")
        return {"roles": []}

@router.get("/companies")
def get_companies(db: Session = Depends(get_db)):
    """Get all companies with job listings"""
    try:
        companies = db.query(Job.company).distinct().all()
        return {"companies": [company[0] for company in companies if company[0]]}
    except Exception as e:
        logger.error(f"Error fetching companies: {str(e)}")
        return {"companies": []}

@router.get("/locations")
def get_locations(db: Session = Depends(get_db)):
    """Get all unique locations with job listings"""
    try:
        locations = db.query(Job.location).distinct().all()
        return {"locations": [location[0] for location in locations if location[0]]}
    except Exception as e:
        logger.error(f"Error fetching locations: {str(e)}")
        return {"locations": []}

@router.get("/employment-types")
def get_employment_types(db: Session = Depends(get_db)):
    """Get all unique employment types"""
    try:
        types = db.query(Job.employment_type).distinct().all()
        return {"employment_types": [t[0] for t in types if t[0]]}
    except Exception as e:
        logger.error(f"Error fetching employment types: {str(e)}")
        return {"employment_types": []}

@router.get("/stats")
def get_job_stats(db: Session = Depends(get_db)):
    """Get job statistics"""
    try:
        # Count jobs by date posted for the last 7 days
        now = datetime.utcnow()
        last_week = now - timedelta(days=7)
        
        # Use func instead of db.func
        from sqlalchemy import func
        
        jobs_by_date = db.query(
            Job.date_posted, 
            func.count(Job.id)
        ).filter(
            Job.date_posted >= last_week,
            Job.is_active == True
        ).group_by(
            Job.date_posted
        ).order_by(
            Job.date_posted.desc()
        ).all()
        
        # Count jobs by company
        jobs_by_company = db.query(
            Job.company,
            func.count(Job.id)
        ).filter(
            Job.is_active == True
        ).group_by(
            Job.company
        ).order_by(
            func.count(Job.id).desc()
        ).limit(10).all()
        
        # Count total active jobs
        total_active = db.query(Job).filter(Job.is_active == True).count()
        
        # Count jobs added today
        today = datetime(now.year, now.month, now.day)
        added_today = db.query(Job).filter(
            Job.first_seen >= today,
            Job.is_active == True
        ).count()
        
        return {
            "total_active_jobs": total_active,
            "added_today": added_today,
            "jobs_by_date": [{"date": date.strftime("%Y-%m-%d"), "count": count} for date, count in jobs_by_date],
            "top_companies": [{"company": company, "count": count} for company, count in jobs_by_company]
        }
    except Exception as e:
        logger.error(f"Error fetching job stats: {str(e)}")
        return {"error": "Failed to fetch job statistics"}
