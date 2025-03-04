# app/auth/schemas.py
from typing import Optional
from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from app.db.models import UserRole

# Token schemas
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[float] = None

# User schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserRead(UserBase):
    id: int
    role: UserRole
    is_active: bool
    registration_date: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        orm_mode = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    password: Optional[str] = None
    
    @validator('password')
    def password_min_length(cls, v):
        if v is not None and len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserAdminUpdate(UserUpdate):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
