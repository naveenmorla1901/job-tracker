"""
Database connection handling
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os

from app.config import SQLALCHEMY_DATABASE_URL, ENVIRONMENT

# Create SQLAlchemy engine with specific settings based on connection type
if SQLALCHEMY_DATABASE_URL.startswith('sqlite'):
    # SQLite needs these parameters
    connect_args = {"check_same_thread": False}
    poolclass = StaticPool if ENVIRONMENT == "test" else None
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args=connect_args,
        poolclass=poolclass
    )
else:
    # PostgreSQL or other database
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Generator function to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
