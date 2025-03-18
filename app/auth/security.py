# app/auth/security.py
from datetime import datetime, timedelta
from typing import Optional, Union, Any
import os
import logging
from jose import jwt
from passlib.context import CryptContext
from dotenv import load_dotenv

# Set up logger
logger = logging.getLogger("job_tracker.auth.security")

# Load environment variables
load_dotenv()

# Get JWT secret key from environment or use a default (for development only)
default_jwt_key = "temporary_secret_key_replace_in_production"
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", default_jwt_key)

# Generate a secure random key if not provided and not in development mode
if JWT_SECRET_KEY == default_jwt_key and os.environ.get("ENVIRONMENT") != "development":
    import secrets
    new_key = secrets.token_hex(32)
    JWT_SECRET_KEY = new_key
    logger.warning(
        f"Generated a random JWT secret key. For better security, set this key in your .env file:\nJWT_SECRET_KEY={new_key}"
    )

# Log a warning if using the default JWT secret in production
if JWT_SECRET_KEY == default_jwt_key and os.environ.get("ENVIRONMENT") == "production":
    logger.warning(
        "WARNING: Using default JWT secret key in production environment. "
        "This is a security risk. Please set JWT_SECRET_KEY in your environment variables."
    )

ALGORITHM = "HS256"
# Increase token expiration time to 24 hours for better user experience
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Password hashing setup
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        subject: Subject of the token (typically user_id)
        expires_delta: Optional expiration time. If not provided, default is used.
        
    Returns:
        JWT access token as a string
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
