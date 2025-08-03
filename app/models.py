from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class JobType(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    ANY = "any"


class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    ANY = "any"


class NotificationType(str, Enum):
    EMAIL = "email"
    WEBHOOK = "webhook"


class UserCreate(BaseModel):
    email: EmailStr
    name: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


class SearchProfileCreate(BaseModel):
    name: str
    keywords: List[str]
    location: Optional[str] = None
    job_type: JobType = JobType.ANY
    experience_level: ExperienceLevel = ExperienceLevel.ANY
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    
    @validator('keywords')
    def validate_keywords(cls, v):
        if not v:
            raise ValueError('At least one keyword is required')
        return v


class SearchProfileUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[List[str]] = None
    location: Optional[str] = None
    job_type: Optional[JobType] = None
    experience_level: Optional[ExperienceLevel] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    is_active: Optional[bool] = None


class SearchProfileResponse(BaseModel):
    id: int
    user_id: int
    name: str
    keywords: List[str]
    location: Optional[str]
    job_type: str
    experience_level: str
    salary_min: Optional[float]
    salary_max: Optional[float]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobListingResponse(BaseModel):
    id: int
    external_id: str
    title: str
    company: str
    location: str
    job_type: Optional[str]
    salary_min: Optional[float]
    salary_max: Optional[float]
    salary_currency: str
    description: str
    requirements: List[str]
    skills: List[str]
    experience_level: Optional[str]
    application_url: str
    source_site: str
    posted_date: Optional[datetime]
    scraped_at: datetime
    is_active: bool
    job_metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    job_listing_id: int
    search_profile_id: int
    sent_at: datetime
    notification_type: str
    status: str
    
    class Config:
        from_attributes = True


class ScrapingLogResponse(BaseModel):
    id: int
    source_site: str
    search_terms: Dict[str, Any]
    jobs_found: int
    jobs_new: int
    jobs_updated: int
    errors: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class JobSearchRequest(BaseModel):
    keywords: List[str]
    location: Optional[str] = None
    job_type: JobType = JobType.ANY
    experience_level: ExperienceLevel = ExperienceLevel.ANY
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    limit: int = 50
    offset: int = 0


class NotificationCreate(BaseModel):
    user_id: int
    job_listing_id: int
    search_profile_id: int
    notification_type: NotificationType 