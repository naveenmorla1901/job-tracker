# app/db/models.py
import os
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, Table, UniqueConstraint, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

# Check if we're using SQLite (for testing)
TESTING = os.environ.get("TESTING", "False").lower() in ("true", "1", "t")

Base = declarative_base()

# Association table for many-to-many relationship between Job and Role
job_roles = Table(
    'job_roles',
    Base.metadata,
    Column('job_id', Integer, ForeignKey('jobs.id'), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True)
)

class Job(Base):
    """Job posting information model"""
    __tablename__ = 'jobs'
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(255), unique=True, index=True, nullable=False)  # External job ID
    job_title = Column(String(255), nullable=False)
    location = Column(String(255))
    job_url = Column(String(1024), nullable=False)
    company = Column(String(255), nullable=False, index=True)  # Store the company name
    date_posted = Column(DateTime, default=datetime.utcnow)
    employment_type = Column(String(50))
    description = Column(Text)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Use standard JSON type for SQLite compatibility
    raw_data = Column(JSON, nullable=True)  # Store the full JSON for future reference
    
    is_active = Column(Boolean, default=True)  # Flag to mark if the job is still active
    
    # Relationships
    roles = relationship("Role", secondary=job_roles, back_populates="jobs")
    
    __table_args__ = (
        UniqueConstraint('job_id', 'company', name='uix_job_company'),
    )

class Role(Base):
    """Role categories for jobs"""
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    
    # Relationships
    jobs = relationship("Job", secondary=job_roles, back_populates="roles")

class ScraperRun(Base):
    """Records of scraper execution runs"""
    __tablename__ = 'scraper_runs'
    
    id = Column(Integer, primary_key=True, index=True)
    scraper_name = Column(String(100), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(50))  # success, failure, partial
    jobs_added = Column(Integer, default=0)
    jobs_updated = Column(Integer, default=0)
    error_message = Column(Text)
