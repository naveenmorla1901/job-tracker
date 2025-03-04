# app/api/endpoints/auth/routes.py
from datetime import timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db import crud_user
from app.db.models import User, UserRole
from app.auth.schemas import (
    Token, UserCreate, UserRead, UserLogin, UserUpdate, UserAdminUpdate
)
from app.auth.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.auth.dependencies import get_current_user, get_admin_user

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        user = crud_user.create_user(
            db=db,
            email=user_data.email,
            password=user_data.password
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login and get access token"""
    user = crud_user.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with specified expiration
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login/json", response_model=Token)
async def login_json(login_data: UserLogin, db: Session = Depends(get_db)):
    """Alternative login endpoint that accepts JSON instead of form data"""
    user = crud_user.authenticate_user(db, login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token with specified expiration
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserRead)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get information about the current authenticated user"""
    return current_user

@router.put("/me", response_model=UserRead)
async def update_user_info(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's information"""
    # Currently only password updates are supported
    if user_data.password:
        success = crud_user.update_user_password(
            db, current_user.id, user_data.password
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
    
    # Refresh user data
    user = crud_user.get_user_by_id(db, current_user.id)
    return user

# Admin routes
@router.get("/users", response_model=List[UserRead])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only)"""
    users = crud_user.list_users(db, skip=skip, limit=limit)
    return users

@router.get("/users/{user_id}", response_model=UserRead)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Get a specific user by ID (admin only)"""
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/users/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_data: UserAdminUpdate,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    """Update a user's information (admin only)"""
    user = crud_user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password if provided
    if user_data.password:
        success = crud_user.update_user_password(
            db, user_id, user_data.password
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
    
    # Update role if provided
    if user_data.role is not None:
        success = crud_user.update_user_role(
            db, user_id, user_data.role
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update role"
            )
    
    # Update active status if provided
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
        db.commit()
    
    # Refresh user data
    user = crud_user.get_user_by_id(db, user_id)
    return user
