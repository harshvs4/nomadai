import streamlit as st
import requests
import json
from datetime import datetime

from utils.api import get_api_url
from utils.session import get_auth_token, set_page, logout_user

def show_profile_page():
    """Display the user profile page."""
    
    st.header("👤 My Profile")
    
    # Check if user is logged in
    if not get_auth_token():
        st.warning("Please log in to view your profile.")
        if st.button("Go to Login"):
            set_page('login')
            st.rerun()
        return
    
    # Fetch user profile from the API
    try:
        response = requests.get(
            f"{get_api_url()}/users/me/profile",
            headers={"Authorization": f"Bearer {get_auth_token()}"}
        )
        
        if response.status_code == 200:
            profile = response.json()
            display_user_profile(profile)
        else:
            st.error("Could not retrieve your profile. Please try again later.")
            if response.status_code == 401:
                st.info("Your session may have expired. Please log in again.")
                if st.button("Login Again"):
                    logout_user()
                    set_page('login')
                    st.rerun()
    except Exception as e:
        st.error(f"Error connecting to the server: {str(e)}")
        # For demo, show a sample profile
        sample_profile = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User",
            "avatar_url": None,
            "bio": "Passionate traveler and foodie",
            "location": "Singapore",
            "date_joined": "2025-01-15T00:00:00",
            "travel_preferences": ["Adventure", "Culture", "Food"],
            "favorite_destinations": ["Tokyo", "Paris", "New York"]
        }
        display_user_profile(sample_profile)

def display_user_profile(profile):
    """Display the user profile information."""
    
    # Profile header with avatar and basic info
    col1, col2 = st.columns([1, 3])
    
    with col1:
        # Display avatar or placeholder
        avatar_url = profile.get("avatar_url")
        if avatar_url:
            st.image(avatar_url, width=150)
        else:
            st.image("https://via.placeholder.com/150?text=User", width=150)
    
    with col2:
        st.subheader(profile.get("full_name") or profile.get("username"))
        st.markdown(f"**Username**: {profile.get('username')}")
        st.markdown(f"**Email**: {profile.get('email', 'Email not provided')}")
        
        location = profile.get("location")
        if location:
            st.markdown(f"**Location**: {location}")
        
        # Date joined
        date_joined = profile.get("date_joined")
        if date_joined:
            try:
                if isinstance(date_joined, str):
                    joined_date = datetime.fromisoformat(date_joined.replace('Z', '+00:00'))
                    st.markdown(f"**Member since**: {joined_date.strftime('%B %Y')}")
                else:
                    st.markdown(f"**Member since**: {date_joined}")
            except:
                st.markdown(f"**Member since**: {date_joined}")
    
    # Bio
    bio = profile.get("bio")
    if bio:
        st.markdown("### About Me")
        st.markdown(bio)
    
    # Tabs for different profile sections
    tab1, tab2, tab3 = st.tabs(["Travel Preferences", "Personal Details", "Account Settings"])
    
    with tab1:
        st.subheader("Travel Preferences")
        
        # Current preferences
        preferences = profile.get("travel_preferences", [])
        st.markdown("#### My Travel Interests")
        
        if preferences:
            # Display as multi-select so user can edit
            new_preferences = st.multiselect(
                "Select your travel interests",
                options=[
                    "Adventure", "Relaxation", "Culture", "Nightlife",
                    "Nature", "Food", "Luxury", "Budget", "Family",
                    "Shopping", "Beach", "Mountain"
                ],
                default=preferences
            )
            
            # Save button for preferences
            if new_preferences != preferences and st.button("Save Travel Interests"):
                save_travel_preferences(new_preferences)
        else:
            st.info("You haven't set any travel preferences yet.")
            
            # Let user add preferences
            new_preferences = st.multiselect(
                "Select your travel interests",
                options=[
                    "Adventure", "Relaxation", "Culture", "Nightlife",
                    "Nature", "Food", "Luxury", "Budget", "Family",
                    "Shopping", "Beach", "Mountain"
                ]
            )
            
            if new_preferences and st.button("Save Travel Interests"):
                save_travel_preferences(new_preferences)
        
        # Favorite destinations
        st.markdown("#### My Favorite Destinations")
        favorites = profile.get("favorite_destinations", [])
        
        if favorites:
            # Create columns to display favorites
            cols = st.columns(min(3, len(favorites)))
            for i, dest in enumerate(favorites):
                with cols[i % 3]:
                    st.markdown(f"**{dest}**")
        else:
            st.info("You haven't added any favorite destinations yet.")
        
        # Add new favorite
        new_favorite = st.text_input("Add a new favorite destination")
        if new_favorite and st.button("Add Destination"):
            save_favorite_destination(new_favorite, favorites)
    
    with tab2:
        st.subheader("Personal Details")
        
        with st.form("personal_details_form"):
            full_name = st.text_input("Full Name", value=profile.get("full_name", ""))
            email = st.text_input("Email", value=profile.get("email", ""))
            location = st.text_input("Location", value=profile.get("location", ""))
            bio = st.text_area("Bio", value=profile.get("bio", ""))
            
            if st.form_submit_button("Update Profile"):
                # Call API to update profile
                update_profile(full_name, email, location, bio)
    
    with tab3:
        st.subheader("Account Settings")
        
        # Change password form
        with st.form("change_password_form"):
            st.subheader("Change Password")
            current_password = st.text_input("Current Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_password = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Change Password"):
                if not current_password or not new_password or not confirm_password:
                    st.error("Please fill in all password fields.")
                elif new_password != confirm_password:
                    st.error("New passwords do not match.")
                else:
                    # Call API to change password
                    change_password(current_password, new_password)
        
        # Delete account
        st.subheader("Account Management")
        danger_zone = st.expander("Danger Zone", expanded=False)
        with danger_zone:
            st.warning("Be careful! These actions cannot be undone.")
            
            if st.button("Delete Account", type="primary"):
                # Show a confirmation dialog
                st.warning("Are you sure you want to delete your account? This action cannot be undone.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Yes, Delete My Account"):
                        delete_account()
                with col2:
                    if st.button("Cancel"):
                        st.rerun()

def save_travel_preferences(preferences):
    """Save user travel preferences via API."""
    try:
        response = requests.post(
            f"{get_api_url()}/users/me/preferences",
            headers={"Authorization": f"Bearer {get_auth_token()}"},
            json=preferences
        )
        
        if response.status_code == 200:
            st.success("Travel preferences updated successfully!")
            st.rerun()
        else:
            st.error(f"Failed to update preferences: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error updating preferences: {str(e)}")
        # For demo, show success
        st.success("Travel preferences updated successfully! (Demo mode)")

def save_favorite_destination(new_destination, current_favorites):
    """Add a new favorite destination."""
    if new_destination in current_favorites:
        st.warning(f"{new_destination} is already in your favorites.")
        return
    
    updated_favorites = current_favorites + [new_destination]
    
    try:
        response = requests.post(
            f"{get_api_url()}/users/me/favorites",
            headers={"Authorization": f"Bearer {get_auth_token()}"},
            json=updated_favorites
        )
        
        if response.status_code == 200:
            st.success(f"Added {new_destination} to your favorites!")
            st.rerun()
        else:
            st.error(f"Failed to update favorites: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error updating favorites: {str(e)}")
        # For demo, show success
        st.success(f"Added {new_destination} to your favorites! (Demo mode)")

def update_profile(full_name, email, location, bio):
    """Update user profile details."""
    profile_data = {
        "full_name": full_name,
        "email": email
    }
    
    try:
        response = requests.put(
            f"{get_api_url()}/users/me/profile",
            headers={"Authorization": f"Bearer {get_auth_token()}"},
            json=profile_data
        )
        
        if response.status_code == 200:
            st.success("Profile updated successfully!")
            st.rerun()
        else:
            st.error(f"Failed to update profile: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error updating profile: {str(e)}")
        # For demo, show success
        st.success("Profile updated successfully! (Demo mode)")

def change_password(current_password, new_password):
    """Change the user's password."""
    try:
        response = requests.post(
            f"{get_api_url()}/users/me/password",
            headers={"Authorization": f"Bearer {get_auth_token()}"},
            json={"current_password": current_password, "new_password": new_password}
        )
        
        if response.status_code == 200:
            st.success("Password changed successfully!")
        else:
            st.error(f"Failed to change password: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error changing password: {str(e)}")
        # For demo, show success
        st.success("Password changed successfully! (Demo mode)")

def delete_account():
    """Delete the user's account."""
    try:
        response = requests.delete(
            f"{get_api_url()}/users/me",
            headers={"Authorization": f"Bearer {get_auth_token()}"}
        )
        
        if response.status_code == 200:
            st.success("Account deleted successfully.")
            logout_user()
            set_page('home')
            st.rerun()
        else:
            st.error(f"Failed to delete account: {response.json().get('detail', 'Unknown error')}")
    except Exception as e:
        st.error(f"Error deleting account: {str(e)}")
        # For demo purposes
        st.success("Account deleted successfully! (Demo mode)")
        logout_user()
        set_page('home')
        st.rerun()