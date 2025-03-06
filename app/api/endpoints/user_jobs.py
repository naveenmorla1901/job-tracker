# app/api/endpoints/user_jobs.py
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud_user
from app.db.models import User
from app.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_user_tracked_jobs(
    applied_only: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all jobs tracked by the current user.
    
    Query parameters:
    - applied_only: If True, only return jobs marked as applied
    """
    jobs = crud_user.get_tracked_jobs(
        db=db,
        user_id=current_user.id,
        applied_only=applied_only
    )
    return jobs

@router.get("/{job_id}", response_model=Dict[str, Any])
async def get_user_tracked_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific job tracked by the current user.
    
    Path parameters:
    - job_id: The ID of the job to retrieve
    """
    # First check if job is tracked
    user_job = crud_user.get_user_job(
        db=db,
        user_id=current_user.id,
        job_id=job_id
    )
    
    if not user_job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found or not tracked by user"
        )
    
    # Get the job details
    jobs = crud_user.get_tracked_jobs(
        db=db,
        user_id=current_user.id,
        job_id=job_id
    )
    
    if not jobs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )
    
    return jobs[0]

@router.post("/{job_id}/track", status_code=status.HTTP_201_CREATED)
async def track_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Track a job (add it to user's saved jobs)"""
    result = crud_user.track_job(
        db=db,
        user_id=current_user.id,
        job_id=job_id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to track job"
        )
    
    return {"success": True, "message": "Job tracked successfully"}

@router.delete("/{job_id}/track", status_code=status.HTTP_200_OK)
async def untrack_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Untrack a job (remove it from user's saved jobs)"""
    success = crud_user.untrack_job(
        db=db,
        user_id=current_user.id,
        job_id=job_id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job was not tracked or could not be untracked"
        )
    
    return {"success": True, "message": "Job untracked successfully"}

@router.put("/{job_id}/applied", status_code=status.HTTP_200_OK)
async def mark_job_applied(
    job_id: int,
    applied: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a job as applied or not applied"""
    success = crud_user.mark_job_applied(
        db=db,
        user_id=current_user.id,
        job_id=job_id,
        applied=applied
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update job application status"
        )
    
    status_msg = "applied" if applied else "not applied"
    return {
        "success": True,
        "message": f"Job marked as {status_msg} successfully"
    }
