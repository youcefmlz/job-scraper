from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from app.config import settings

# Create database engine
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    search_profiles = relationship("SearchProfile", back_populates="user")
    notifications = relationship("Notification", back_populates="user")


class SearchProfile(Base):
    __tablename__ = "search_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String)
    keywords = Column(JSON)  # List of keywords
    location = Column(String)
    job_type = Column(String)  # remote, hybrid, onsite, any
    experience_level = Column(String)  # entry, mid, senior, any
    salary_min = Column(Float)
    salary_max = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="search_profiles")


class JobListing(Base):
    __tablename__ = "job_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, unique=True, index=True)  # ID from the job site
    title = Column(String)
    company = Column(String)
    location = Column(String)
    job_type = Column(String)  # remote, hybrid, onsite
    salary_min = Column(Float)
    salary_max = Column(Float)
    salary_currency = Column(String, default="USD")
    description = Column(Text)
    requirements = Column(JSON)  # List of requirements
    skills = Column(JSON)  # List of skills
    experience_level = Column(String)
    application_url = Column(String)
    source_site = Column(String)  # linkedin, indeed, glassdoor, etc.
    posted_date = Column(DateTime)
    scraped_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Additional metadata
    job_metadata = Column(JSON)  # Store additional site-specific data


class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    job_listing_id = Column(Integer, ForeignKey("job_listings.id"))
    search_profile_id = Column(Integer, ForeignKey("search_profiles.id"))
    sent_at = Column(DateTime, default=datetime.utcnow)
    notification_type = Column(String)  # email, webhook, etc.
    status = Column(String)  # sent, failed, pending
    
    # Relationships
    user = relationship("User", back_populates="notifications")


class ScrapingLog(Base):
    __tablename__ = "scraping_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    source_site = Column(String)
    search_terms = Column(JSON)
    jobs_found = Column(Integer)
    jobs_new = Column(Integer)
    jobs_updated = Column(Integer)
    errors = Column(Text)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


# Create all tables
def create_tables():
    Base.metadata.create_all(bind=engine)


# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 