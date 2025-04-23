from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from models.user import User, UserUpdate, UserProfile
from utils.auth import get_current_active_user

router = APIRouter()

# Mock user profiles - in a real app, this would be in a database
fake_user_profiles = {
    "testuser": UserProfile(
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        avatar_url=None,
        bio="Travel enthusiast",
        location="Singapore",
        travel_preferences=["Adventure", "Nature", "Culture"],
        favorite_destinations=["Tokyo", "Paris", "Bali"]
    )
}

@router.get("/me", response_model=User)
async def get_current_user(current_user: User = Depends(get_current_active_user)):
    """Get the current user's basic information."""
    return current_user

@router.get("/me/profile", response_model=UserProfile)
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """Get the current user's full profile."""
    username = current_user.username
    if username not in fake_user_profiles:
        # Create a default profile if one doesn't exist
        fake_user_profiles[username] = UserProfile(
            username=username,
            email=current_user.email,
            full_name=current_user.full_name
        )
    
    return fake_user_profiles[username]

@router.put("/me/profile", response_model=UserProfile)
async def update_user_profile(
    profile_update: UserUpdate,
    current_user: User = Depends(get_current_active_user)
):
    """Update the current user's profile."""
    username = current_user.username
    
    # Get existing profile or create new one
    if username not in fake_user_profiles:
        profile = UserProfile(
            username=username,
            email=current_user.email,
            full_name=current_user.full_name
        )
    else:
        profile = fake_user_profiles[username]
    
    # Update fields if provided
    if profile_update.email:
        profile.email = profile_update.email
    
    if profile_update.full_name:
        profile.full_name = profile_update.full_name
    
    # Update the stored profile
    fake_user_profiles[username] = profile
    
    return profile

@router.post("/me/preferences", response_model=List[str])
async def update_travel_preferences(
    preferences: List[str],
    current_user: User = Depends(get_current_active_user)
):
    """Update the current user's travel preferences."""
    username = current_user.username
    
    # Ensure profile exists
    if username not in fake_user_profiles:
        fake_user_profiles[username] = UserProfile(
            username=username,
            email=current_user.email,
            full_name=current_user.full_name
        )
    
    # Update preferences
    fake_user_profiles[username].travel_preferences = preferences
    
    return preferences

@router.post("/me/favorites", response_model=List[str])
async def update_favorite_destinations(
    destinations: List[str],
    current_user: User = Depends(get_current_active_user)
):
    """Update the current user's favorite destinations."""
    username = current_user.username
    
    # Ensure profile exists
    if username not in fake_user_profiles:
        fake_user_profiles[username] = UserProfile(
            username=username,
            email=current_user.email,
            full_name=current_user.full_name
        )
    
    # Update favorite destinations
    fake_user_profiles[username].favorite_destinations = destinations
    
    return destinations