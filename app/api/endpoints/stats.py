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

@router.get("/scraper-runs")
def get_scraper_runs(db: Session = Depends(get_db)):
    """Latest run of every registered scraper, plus all-time counts by status.

    One row per scraper answers "is each company working right now?" — a
    window of the last N rows mixes several cycles and hides scrapers that
    never ran.
    """
    try:
        from app.scrapers import get_all_scrapers
        from app.scheduler.jobs import COMPANY_NAMES

        registered = sorted(get_all_scrapers().keys())

        latest_ids = db.query(func.max(ScraperRun.id)).group_by(ScraperRun.scraper_name)
        latest_runs = {
            run.scraper_name: run
            for run in db.query(ScraperRun).filter(ScraperRun.id.in_(latest_ids)).all()
        }

        scrapers = []
        counts = {s: 0 for s in ("success", "partial", "empty", "failure", "interrupted", "running", "never_run")}
        for name in registered:
            run = latest_runs.get(name)
            status = run.status if run else "never_run"
            counts[status] = counts.get(status, 0) + 1
            scrapers.append({
                "scraper_name": name,
                "company": COMPANY_NAMES.get(name, name),
                "status": status,
                "jobs_added": run.jobs_added if run else 0,
                "jobs_updated": run.jobs_updated if run else 0,
                "start_time": run.start_time.isoformat() if run and run.start_time else None,
                "end_time": run.end_time.isoformat() if run and run.end_time else None,
                "error_message": run.error_message if run else None,
            })

        ran = len(registered) - counts["never_run"]
        working = counts["success"] + counts["partial"]
        all_time = dict(
            db.query(ScraperRun.status, func.count(ScraperRun.id)).group_by(ScraperRun.status).all()
        )
        last_run = db.query(func.max(ScraperRun.end_time)).scalar()

        return {
            "summary": {
                "registered": len(registered),
                "ran": ran,
                "working": working,
                "working_rate": round(working / ran * 100, 1) if ran else 0,
                "by_status": counts,
                "last_run": last_run.isoformat() if last_run else None,
                "all_time": all_time,
                "total_all_time": sum(all_time.values()),
            },
            "scrapers": scrapers,
        }
    except Exception as e:
        logger.error(f"Error getting scraper runs: {str(e)}")
        return {"error": f"Failed to get scraper runs: {str(e)}"}
