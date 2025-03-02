"""
Functions to gather application API statistics
"""
import logging
from typing import Dict, Any

# Configure logging
logger = logging.getLogger("job_tracker.api_stats")

def get_api_stats() -> Dict[str, Any]:
    """Get statistics about API usage if available"""
    try:
        api_stats = {}
        
        # Try to count job entries in the database
        try:
            from app.db.database import get_db
            from app.db.models import Job, ScraperRun, Role, job_roles
            from sqlalchemy import func
            
            db = next(get_db())
            
            # Count jobs
            total_jobs = db.query(Job).count()
            active_jobs = db.query(Job).filter(Job.is_active == True).count()
            inactive_jobs = db.query(Job).filter(Job.is_active == False).count()
            
            # Count companies
            companies = db.query(Job.company).distinct().count()
            
            # Count roles
            roles = db.query(Role).count()
            
            # Count recent scraper runs
            recent_runs = db.query(ScraperRun).order_by(ScraperRun.id.desc()).limit(100).all()
            
            success_runs = sum(1 for run in recent_runs if run.status == "success")
            failure_runs = sum(1 for run in recent_runs if run.status == "failure")
            
            # Calculate success rate
            if recent_runs:
                success_rate = (success_runs / len(recent_runs)) * 100
            else:
                success_rate = 0
                
            # Count jobs by posting date
            jobs_by_date = []
            dates_query = db.query(Job.date_posted, func.count(Job.id)).group_by(Job.date_posted).order_by(Job.date_posted.desc()).limit(7).all()
            
            for date, count in dates_query:
                jobs_by_date.append({
                    "date": date.strftime("%Y-%m-%d") if date else "Unknown",
                    "count": count
                })
                
            # Count jobs by role
            jobs_by_role = []
            try:
                roles_query = db.query(Role.name, func.count(job_roles.c.job_id)).join(
                    job_roles, Role.id == job_roles.c.role_id
                ).group_by(Role.name).order_by(func.count(job_roles.c.job_id).desc()).limit(10).all()
                
                for role, count in roles_query:
                    jobs_by_role.append({
                        "role": role,
                        "count": count
                    })
            except Exception as e:
                logger.error(f"Error getting jobs by role: {str(e)}")
                
            api_stats["database"] = {
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "inactive_jobs": inactive_jobs,
                "companies": companies,
                "roles": roles,
                "recent_scraper_runs": len(recent_runs),
                "success_rate": round(success_rate, 2),
                "jobs_by_date": jobs_by_date,
                "jobs_by_role": jobs_by_role
            }
            
            db.close()
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            api_stats["database_error"] = str(e)
        
        return api_stats
    except Exception as e:
        logger.error(f"Error getting API stats: {str(e)}")
        return {"error": str(e)}
