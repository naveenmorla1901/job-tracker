# app/api/endpoints/auth.py
# DEPRECATED: This file is no longer used. Authentication endpoints are defined in auth/routes.py
# Keeping this file for reference only. Any changes should be made to auth/routes.py instead.

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List

# Set up logger
logger = logging.getLogger("job_tracker.api.auth.deprecated")
logger.warning("The deprecated auth.py file is being imported. Use auth/routes.py instead.")

from app.db.database import get_db
from app.db import crud_user
from app.db.models import UserRole
from app.auth import security
from app.auth.schemas import Token, UserCreate, UserRead, UserLogin, UserUpdate, UserAdminUpdate
from app.auth.dependencies import get_current_user, get_admin_user

router = APIRouter()

@router.post("/register", response_model=UserRead)
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.
    """
    try:
        db_user = crud_user.create_user(db, user.email, user.password)
        return db_user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = crud_user.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/email", response_model=Token)
def login_with_email(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Email/password login, get an access token for future requests.
    This endpoint is an alternative to the OAuth2 flow.
    """
    user = crud_user.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=security.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
def read_users_me(current_user: UserRead = Depends(get_current_user)):
    """
    Get current user.
    """
    return current_user

@router.put("/me", response_model=UserRead)
def update_user_me(
    user_update: UserUpdate,
    current_user: UserRead = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's information.
    """
    # Update password if provided
    if user_update.password:
        success = crud_user.update_user_password(db, current_user.id, user_update.password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
    
    # Get fresh user data
    user = crud_user.get_user_by_id(db, current_user.id)
    return user

@router.get("/users", response_model=List[UserRead])
def read_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserRead = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get all users. Admin only.
    """
    users = crud_user.list_users(db, skip=skip, limit=limit)
    return users

@router.put("/users/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    user_update: UserAdminUpdate,
    current_user: UserRead = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update a user's information. Admin only.
    """
    # Get user first to check if it exists
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    
    # Update password if provided
    if user_update.password:
        success = crud_user.update_user_password(db, user_id, user_update.password)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
    
    # Update role if provided
    if user_update.role:
        success = crud_user.update_user_role(db, user_id, user_update.role)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update role"
            )
    
    # Update active status if provided
    if user_update.is_active is not None:
        user.is_active = user_update.is_active
        db.commit()
    
    # Get fresh user data
    updated_user = crud_user.get_user_by_id(db, user_id)
    return updated_user
