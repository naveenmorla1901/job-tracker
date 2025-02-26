"""
Statistics endpoints for job tracker API
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from datetime import datetime, timedelta
import logging

from app.db.database import get_db
from app.db.models import Job, Role, ScraperRun

logger = logging.getLogger("job_tracker.api.stats")

router = APIRouter()

@router.get("/")
@router.get("/summary")  # Maintain backward compatibility
def get_summary_stats(db: Session = Depends(get_db)):
    """Get summary statistics about job listings"""
    try:
        # Total active jobs
        total_jobs = db.query(func.count(Job.id)).filter(Job.is_active == True).scalar()
        
        # Jobs added in last 24 hours
        cutoff = datetime.utcnow() - timedelta(days=1)
        new_jobs = db.query(func.count(Job.id)).filter(
            Job.first_seen >= cutoff,
            Job.is_active == True
        ).scalar()
        
        # Top companies by job count
        top_companies = db.query(
            Job.company, 
            func.count(Job.id).label('count')
        ).filter(
            Job.is_active == True
        ).group_by(
            Job.company
        ).order_by(
            desc('count')
        ).limit(5).all()
        
        # Top roles by job count
        top_roles = db.query(
            Role.name, 
            func.count(Job.id).label('count')
        ).join(
            Job.roles
        ).filter(
            Job.is_active == True
        ).group_by(
            Role.name
        ).order_by(
            desc('count')
        ).limit(5).all()
        
        return {
            "total_active_jobs": total_jobs,
            "new_jobs_24h": new_jobs,
            "top_companies": [{"company": c[0], "count": c[1]} for c in top_companies],
            "top_roles": [{"role": r[0], "count": r[1]} for r in top_roles],
        }
    except Exception as e:
        logger.error(f"Error generating summary stats: {str(e)}")
        return {"error": "Failed to generate statistics"}

@router.get("/trend")
def get_job_trend(db: Session = Depends(get_db), days: int = 30):
    """Get job posting trend over time"""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get daily job counts
        daily_counts = db.query(
            func.date_trunc('day', Job.date_posted).label('day'),
            func.count(Job.id).label('count')
        ).filter(
            Job.date_posted >= cutoff
        ).group_by(
            'day'
        ).order_by(
            'day'
        ).all()
        
        return {
            "trend": [
                {"date": day.strftime("%Y-%m-%d") if day else "unknown", "count": count}
                for day, count in daily_counts
            ]
        }
    except Exception as e:
        logger.error(f"Error generating trend data: {str(e)}")
        return {"error": "Failed to generate trend data"}
