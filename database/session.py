from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
# from typing import Generator

# Define the DATABASE_URL
DATABASE_URL = "sqlite:///./bulletmail.db"

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL, pool_timeout=30, pool_recycle=600, max_overflow=15, pool_size=10)

# Create a sessionmaker object
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Define the base class for declarative models
Base = declarative_base()

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
