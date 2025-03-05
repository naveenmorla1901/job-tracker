# app/auth/dependencies.py
from typing import Optional
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError, ExpiredSignatureError
from sqlalchemy.orm import Session
from pydantic import ValidationError
from datetime import datetime

# Set up logger
logger = logging.getLogger("job_tracker.auth.dependencies")
from app.db.database import get_db
from app.db import crud
from app.auth.security import JWT_SECRET_KEY, ALGORITHM
from app.auth.schemas import TokenPayload, UserRead
from app.db.models import UserRole

# Define the token URL (where the client should get the token)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> UserRead:
    """
    Get the current authenticated user based on the JWT token.
    
    Args:
        db: Database session
        token: JWT token from request
        
    Returns:
        Current authenticated user
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[ALGORITHM])
        token_data = TokenPayload(**payload)
        
        # Verify token hasn't expired
        if token_data.exp < datetime.utcnow().timestamp():
            logger.warning(f"Token expired for user ID: {token_data.sub}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except ExpiredSignatureError:
        logger.warning("Expired JWT token received")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except ValidationError:
        logger.warning("Invalid token payload format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token format. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        logger.warning("Invalid JWT token received")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get the user from the database
    try:
        user_id = int(token_data.sub)
    except (TypeError, ValueError):
        logger.error(f"Invalid user ID in token: {token_data.sub}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user identifier in token. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = crud.get_user_by_id(db, user_id)
    if not user:
        logger.warning(f"User not found: ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User no longer exists. Please contact support.",
        )
    
    # Check if user is active
    if not user.is_active:
        logger.warning(f"Inactive user attempted login: ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated. Please contact support."
        )
    
    return user

def get_current_active_user(
    current_user: UserRead = Depends(get_current_user),
) -> UserRead:
    """
    Verify the user is active.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current authenticated user if active
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def get_admin_user(
    current_user: UserRead = Depends(get_current_user),
) -> UserRead:
    """
    Verify the user has admin role.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current authenticated user if admin
        
    Raises:
        HTTPException: If user is not an admin
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user
