from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db, User, SearchProfile, Notification
from app.models import (
    UserCreate, UserResponse, SearchProfileCreate, SearchProfileUpdate,
    SearchProfileResponse, NotificationResponse
)
from app.services.notification_service import NotificationService

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Create a new user"""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create new user
    user = User(
        email=user_data.email,
        name=user_data.name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return UserResponse.from_orm(user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific user"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(user)


@router.get("/{user_id}/profiles", response_model=List[SearchProfileResponse])
async def get_user_profiles(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get all search profiles for a user"""
    profiles = db.query(SearchProfile).filter(
        SearchProfile.user_id == user_id
    ).all()
    return [SearchProfileResponse.from_orm(profile) for profile in profiles]


@router.post("/{user_id}/profiles", response_model=SearchProfileResponse)
async def create_search_profile(
    user_id: int,
    profile_data: SearchProfileCreate,
    db: Session = Depends(get_db)
):
    """Create a new search profile for a user"""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create new profile
    profile = SearchProfile(
        user_id=user_id,
        name=profile_data.name,
        keywords=profile_data.keywords,
        location=profile_data.location,
        job_type=profile_data.job_type.value,
        experience_level=profile_data.experience_level.value,
        salary_min=profile_data.salary_min,
        salary_max=profile_data.salary_max
    )
    db.add(profile)
    db.commit()
    db.refresh(profile)
    
    return SearchProfileResponse.from_orm(profile)


@router.put("/profiles/{profile_id}", response_model=SearchProfileResponse)
async def update_search_profile(
    profile_id: int,
    profile_data: SearchProfileUpdate,
    db: Session = Depends(get_db)
):
    """Update a search profile"""
    profile = db.query(SearchProfile).filter(SearchProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    
    # Update fields if provided
    if profile_data.name is not None:
        profile.name = profile_data.name
    if profile_data.keywords is not None:
        profile.keywords = profile_data.keywords
    if profile_data.location is not None:
        profile.location = profile_data.location
    if profile_data.job_type is not None:
        profile.job_type = profile_data.job_type.value
    if profile_data.experience_level is not None:
        profile.experience_level = profile_data.experience_level.value
    if profile_data.salary_min is not None:
        profile.salary_min = profile_data.salary_min
    if profile_data.salary_max is not None:
        profile.salary_max = profile_data.salary_max
    if profile_data.is_active is not None:
        profile.is_active = profile_data.is_active
    
    db.commit()
    db.refresh(profile)
    
    return SearchProfileResponse.from_orm(profile)


@router.delete("/profiles/{profile_id}")
async def delete_search_profile(
    profile_id: int,
    db: Session = Depends(get_db)
):
    """Delete a search profile"""
    profile = db.query(SearchProfile).filter(SearchProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    
    db.delete(profile)
    db.commit()
    
    return {"message": "Search profile deleted successfully"}


@router.get("/{user_id}/notifications", response_model=List[NotificationResponse])
async def get_user_notifications(
    user_id: int,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get notifications for a user"""
    notification_service = NotificationService()
    notifications = notification_service.get_user_notifications(db, user_id, limit)
    return notifications


@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db)
):
    """Mark a notification as read"""
    notification_service = NotificationService()
    success = notification_service.mark_notification_read(db, notification_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}


@router.get("/{user_id}/profiles/{profile_id}")
async def get_search_profile(
    user_id: int,
    profile_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific search profile"""
    profile = db.query(SearchProfile).filter(
        SearchProfile.id == profile_id,
        SearchProfile.user_id == user_id
    ).first()
    
    if not profile:
        raise HTTPException(status_code=404, detail="Search profile not found")
    
    return SearchProfileResponse.from_orm(profile) 