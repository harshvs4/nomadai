import streamlit as st
import requests
import json
import time
import os
from typing import Dict, Any, Optional, List, Union

from .session import get_auth_token

# Default API base URL
DEFAULT_API_URL = "http://localhost:8000/api/v1"

def get_api_url() -> str:
    """
    Get the base URL for API calls.
    
    Returns:
        str: The base API URL
    """
    # Use environment variable if available, otherwise use default
    return os.environ.get("NOMADAI_API_URL", DEFAULT_API_URL)

def fetch_from_api(
    endpoint: str, 
    method: str = "GET", 
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    auth_required: bool = False,
    retry_count: int = 3,
    retry_delay: float = 1.0
) -> Dict[str, Any]:
    """
    Make an API request with retry logic and proper error handling.
    
    Args:
        endpoint (str): API endpoint path (without base URL)
        method (str): HTTP method (GET, POST, PUT, DELETE)
        data (Dict): JSON data for POST/PUT requests
        params (Dict): Query parameters
        headers (Dict): Additional headers
        auth_required (bool): Whether authentication is required
        retry_count (int): Number of retries on failure
        retry_delay (float): Delay between retries in seconds
        
    Returns:
        Dict: API response as dictionary
        
    Raises:
        Exception: If API call fails after retries
    """
    # Prepare headers
    if headers is None:
        headers = {}
    
    # Add auth token if required
    if auth_required:
        token = get_auth_token()
        if not token:
            raise ValueError("Authentication required but no token available.")
        headers["Authorization"] = f"Bearer {token}"
    
    # Add content type for JSON data
    if data is not None:
        headers["Content-Type"] = "application/json"
    
    # Prepare URL
    url = f"{get_api_url()}/{endpoint.lstrip('/')}"
    
    # Make request with retries
    last_exception = None
    for attempt in range(retry_count):
        try:
            response = None
            
            if method.upper() == "GET":
                response = requests.get(url, params=params, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, params=params, headers=headers)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, params=params, headers=headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, json=data, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Check response status
            response.raise_for_status()
            
            # Return JSON response
            return response.json()
            
        except Exception as e:
            last_exception = e
            
            # Handle different error types
            if response is not None:
                # Handle auth errors
                if response.status_code == 401:
                    st.error("Authentication error. Please log in again.")
                    # In a real app, you might want to redirect to login here
                    break
                
                # Handle rate limiting
                if response.status_code == 429:
                    retry_delay = float(response.headers.get("Retry-After", retry_delay * 2))
                
                # Try to get error details from response
                try:
                    error_detail = response.json().get("detail", str(e))
                    st.error(f"API Error: {error_detail}")
                except:
                    st.error(f"API Error: {str(e)}")
            else:
                st.error(f"Connection Error: {str(e)}")
            
            # Wait before retrying, with exponential backoff
            if attempt < retry_count - 1:
                time.sleep(retry_delay * (2 ** attempt))
    
    # If we got here, all retries failed
    raise last_exception or Exception("API request failed after retries")

def search_flights(origin: str, destination: str, depart_date: str, return_date: str) -> List[Dict[str, Any]]:
    """
    Search for flights between cities.
    
    Args:
        origin (str): Origin city name
        destination (str): Destination city name
        depart_date (str): Departure date (YYYY-MM-DD)
        return_date (str): Return date (YYYY-MM-DD)
        
    Returns:
        List[Dict]: List of flight options
    """
    try:
        params = {
            "origin": origin,
            "destination": destination,
            "depart_date": depart_date,
            "return_date": return_date
        }
        
        response = fetch_from_api(
            endpoint="/travel/flights",
            params=params
        )
        
        return response.get("flights", [])
    except Exception as e:
        st.error(f"Error searching flights: {str(e)}")
        return []

def search_hotels(city: str, checkin_date: str, checkout_date: str) -> List[Dict[str, Any]]:
    """
    Search for hotels in a city.
    
    Args:
        city (str): City name
        checkin_date (str): Check-in date (YYYY-MM-DD)
        checkout_date (str): Check-out date (YYYY-MM-DD)
        
    Returns:
        List[Dict]: List of hotel options
    """
    try:
        params = {
            "city": city,
            "checkin_date": checkin_date,
            "checkout_date": checkout_date
        }
        
        response = fetch_from_api(
            endpoint="/travel/hotels",
            params=params
        )
        
        return response.get("hotels", [])
    except Exception as e:
        st.error(f"Error searching hotels: {str(e)}")
        return []

def search_points_of_interest(city: str, preferences: List[str] = None) -> List[Dict[str, Any]]:
    """
    Search for points of interest in a city.
    
    Args:
        city (str): City name
        preferences (List[str], optional): List of travel preferences
        
    Returns:
        List[Dict]: List of points of interest
    """
    try:
        params = {
            "city": city
        }
        
        if preferences:
            params["preferences"] = preferences
        
        response = fetch_from_api(
            endpoint="/travel/points-of-interest",
            params=params
        )
        
        return response.get("points_of_interest", [])
    except Exception as e:
        st.error(f"Error searching points of interest: {str(e)}")
        return []

def create_itinerary(travel_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Create a new travel itinerary.
    
    Args:
        travel_request (Dict): Travel request details
        
    Returns:
        Optional[Dict]: Created itinerary or None if failed
    """
    try:
        return fetch_from_api(
            endpoint="/travel/itinerary",
            method="POST",
            data=travel_request,
            auth_required=True
        )
    except Exception as e:
        st.error(f"Error creating itinerary: {str(e)}")
        return None

def get_saved_itineraries() -> List[Dict[str, Any]]:
    """
    Get the user's saved itineraries.
    
    Returns:
        List[Dict]: List of saved itineraries
    """
    try:
        response = fetch_from_api(
            endpoint="/travel/itineraries",
            auth_required=True
        )
        
        return response
    except Exception as e:
        st.error(f"Error fetching saved itineraries: {str(e)}")
        return []

def save_itinerary(itinerary: Dict[str, Any]) -> bool:
    """
    Save an itinerary to the user's account.
    
    Args:
        itinerary (Dict): Itinerary data
        
    Returns:
        bool: Success status
    """
    try:
        fetch_from_api(
            endpoint="/travel/itineraries",
            method="POST",
            data=itinerary,
            auth_required=True
        )
        return True
    except Exception as e:
        st.error(f"Error saving itinerary: {str(e)}")
        return False

def delete_itinerary(itinerary_id: str) -> bool:
    """
    Delete a saved itinerary.
    
    Args:
        itinerary_id (str): ID of the itinerary to delete
        
    Returns:
        bool: Success status
    """
    try:
        fetch_from_api(
            endpoint=f"/travel/itineraries/{itinerary_id}",
            method="DELETE",
            auth_required=True
        )
        return True
    except Exception as e:
        st.error(f"Error deleting itinerary: {str(e)}")
        return False