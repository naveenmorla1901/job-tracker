from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import SQLALCHEMY_DATABASE_URI

# Create SQLAlchemy engine
engine = create_engine(SQLALCHEMY_DATABASE_URI)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Generator function to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
