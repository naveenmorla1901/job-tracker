"""
API endpoints for role management and validation
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Role

# Set up logger
logger = logging.getLogger("job_tracker.api.roles")

# Import with error handling to prevent startup issues
try:
    from app.scrapers.role_utils import (
        get_filtered_roles,
        clear_filtered_roles,
        get_common_job_roles
    )
except ImportError as e:
    logger.error(f"Error importing role utilities: {e}")
    # Define dummy functions to prevent errors
    def get_filtered_roles():
        logger.warning("Using dummy get_filtered_roles function - role tracking disabled")
        return {}

    def clear_filtered_roles():
        logger.warning("Using dummy clear_filtered_roles function - role tracking disabled")
        return True

    def get_common_job_roles():
        logger.warning("Using dummy get_common_job_roles function - using default roles")
        return ["Software Engineer", "Data Scientist", "Product Manager"]

# Create router
router = APIRouter()

@router.get("/")
def get_roles(db: Session = Depends(get_db)):
    """Get all available role categories"""
    try:
        roles = db.query(Role).all()
        return {"roles": [role.name for role in roles]}
    except Exception as e:
        logger.error(f"Error fetching roles: {str(e)}")
        return {"roles": []}

@router.get("/common")
def get_common_roles():
    """Get a list of common job roles used for validation"""
    try:
        common_roles = get_common_job_roles()
        return {"roles": common_roles, "count": len(common_roles)}
    except Exception as e:
        logger.error(f"Error fetching common roles: {str(e)}")
        return {"roles": [], "count": 0}

@router.get("/filtered")
def get_invalid_roles(
    company: str = Query(None, description="Filter by company name"),
    min_count: int = Query(1, description="Minimum count to include a role")
):
    """
    Get roles that were filtered out during validation

    This endpoint returns roles that were deemed invalid by the role validation system.
    It can be filtered by company name and minimum occurrence count.
    """
    try:
        all_filtered = get_filtered_roles()

        # Apply company filter if provided
        if company:
            filtered_data = {company: all_filtered.get(company, {})} if company in all_filtered else {}
        else:
            filtered_data = all_filtered

        # Apply minimum count filter
        for company_name, roles in list(filtered_data.items()):
            filtered_data[company_name] = {
                role: count for role, count in roles.items()
                if count >= min_count
            }

        # Calculate totals
        total_companies = len(filtered_data)
        total_roles = sum(len(roles) for roles in filtered_data.values())
        total_occurrences = sum(sum(roles.values()) for roles in filtered_data.values())

        # Format the response
        return {
            "filtered_roles": filtered_data,
            "stats": {
                "companies": total_companies,
                "roles": total_roles,
                "occurrences": total_occurrences
            }
        }
    except Exception as e:
        logger.error(f"Error fetching filtered roles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching filtered roles: {str(e)}")

@router.delete("/filtered")
def clear_invalid_roles():
    """Clear the tracked filtered roles data"""
    try:
        clear_filtered_roles()
        return {"message": "Filtered roles tracking data cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing filtered roles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing filtered roles: {str(e)}")
