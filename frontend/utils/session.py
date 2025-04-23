import streamlit as st
import requests
import json
from typing import Dict, Any, Optional

def initialize_session_state():
    """Initialize session state variables if they don't exist."""
    if 'auth_token' not in st.session_state:
        st.session_state.auth_token = None
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = None
    
    if 'page' not in st.session_state:
        st.session_state.page = 'home'
    
    if 'itinerary' not in st.session_state:
        st.session_state.itinerary = None

def get_auth_token() -> Optional[str]:
    """Get the authentication token from session state."""
    return st.session_state.get('auth_token')

def set_auth_token(token: str):
    """Set the authentication token in session state."""
    st.session_state.auth_token = token
    
    # When setting a token, also fetch and store user info
    fetch_user_info()

def logout_user():
    """Clear user authentication and related data."""
    st.session_state.auth_token = None
    st.session_state.user_info = None

def set_page(page: str):
    """Set the current page in session state."""
    st.session_state.page = page

def get_user_info() -> Optional[Dict[str, Any]]:
    """Get the cached user information."""
    # If we have a token but no user info, fetch it
    if st.session_state.get('auth_token') and not st.session_state.get('user_info'):
        fetch_user_info()
    
    return st.session_state.get('user_info')

def fetch_user_info():
    """Fetch user information from the API and store in session state."""
    token = st.session_state.get('auth_token')
    if not token:
        st.session_state.user_info = None
        return
    
    try:
        # Import here to avoid circular imports
        from .api import get_api_url
        
        response = requests.get(
            f"{get_api_url()}/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            st.session_state.user_info = response.json()
        else:
            # If token is invalid, clear it
            st.session_state.auth_token = None
            st.session_state.user_info = None
    except Exception as e:
        st.error(f"Error fetching user info: {str(e)}")
        # For demo, provide sample user info
        st.session_state.user_info = {
            "username": "testuser",
            "email": "test@example.com",
            "full_name": "Test User"
        }

def set_itinerary(itinerary: Dict[str, Any]):
    """Store the current itinerary in session state."""
    st.session_state.itinerary = itinerary

def get_itinerary() -> Optional[Dict[str, Any]]:
    """Get the current itinerary from session state."""
    return st.session_state.get('itinerary')

def clear_itinerary():
    """Clear the current itinerary from session state."""
    st.session_state.itinerary = None

def store_travel_preferences(preferences: Dict[str, Any]):
    """Store travel preferences in session state for future use."""
    if 'travel_preferences' not in st.session_state:
        st.session_state.travel_preferences = {}
    
    # Update with new preferences
    st.session_state.travel_preferences.update(preferences)

def get_travel_preferences() -> Dict[str, Any]:
    """Get stored travel preferences from session state."""
    if 'travel_preferences' not in st.session_state:
        st.session_state.travel_preferences = {}
    
    return st.session_state.travel_preferences

def clear_session():
    """Clear all session data (for logout or testing)."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    
    # Reinitialize essential state
    initialize_session_state()