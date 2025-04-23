import streamlit as st
import os
from datetime import date, datetime
import json
import markdown
import re
from typing import Dict, List, Any, Optional

from utils.session import get_auth_token, get_user_info
from utils.api import get_api_url
from config import settings
from models.travel import Itinerary, TravelRequest, ItineraryDayActivity

def show_itinerary_page():
    """Display the user's current itinerary or saved itineraries."""
    
    st.header("🗺️ Your Travel Itineraries")
    
    # Create tabs for current and saved itineraries
    tab1, tab2 = st.tabs(["Current Itinerary", "Saved Itineraries"])
    
    with tab1:
        # Check if we have a current itinerary
        if 'itinerary' in st.session_state and st.session_state.itinerary:
            _display_current_itinerary(st.session_state.itinerary)
        else:
            st.info("You don't have a current itinerary. Go to 'Plan a Trip' to create one.")
            if st.button("Create New Itinerary"):
                st.session_state.page = 'planner'
                st.experimental_rerun()
    
    with tab2:
        # Load saved itineraries from API or local storage
        saved_itineraries = _load_saved_itineraries()
        
        if saved_itineraries:
            selected_itinerary = st.selectbox(
                "Select a saved itinerary",
                options=saved_itineraries,
                format_func=lambda x: f"{x['destination']} ({x['depart_date']} to {x['return_date']})"
            )
            
            if selected_itinerary:
                # Display the selected saved itinerary
                _display_saved_itinerary(selected_itinerary)
                
                # Option to clone this itinerary
                if st.button("Edit This Itinerary"):
                    st.session_state.itinerary = selected_itinerary
                    st.experimental_rerun()
        else:
            st.info("You don't have any saved itineraries yet.")

def _display_current_itinerary(itinerary: Dict[str, Any]):
    """Display the current itinerary with enhanced formatting."""
    
    # Trip overview section
    st.subheader(f"Trip to {itinerary['destination']}")
    
    # Create three columns for origin/destination, dates, and budget information
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("**Origin**")
        st.write(itinerary['origin'])
        st.markdown("**Destination**")
        st.write(itinerary['destination'])
    
    with col2:
        st.markdown("**Dates**")
        st.write(f"{itinerary['depart_date']} - {itinerary['return_date']} ({itinerary['duration']} days)")
    
    with col3:
        st.markdown("**Budget**")
        st.write(f"SGD {itinerary['budget']:,.2f}")
        st.markdown("**Total Cost**")
        st.write(f"SGD {itinerary['total_cost']:,.2f}")
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Itinerary"):
            _save_itinerary(itinerary)
            st.success("Itinerary saved successfully!")
    
    with col2:
        if st.button("Modify Itinerary"):
            st.session_state.page = 'planner'
            st.experimental_rerun()
    
    # Display map if available
    if 'map_url' in itinerary and itinerary['map_url']:
        st.subheader("Trip Map")
        st.image(itinerary['map_url'], caption="Interactive map of your trip")
    
    # Flight information
    if 'flight' in itinerary and itinerary['flight']:
        st.subheader("✈️ Flight")
        flight = itinerary['flight']
        
        # Format flight details
        flight_info = f"""
        **Airline**: {flight['airline']}  
        **Price**: SGD {flight['price']:,.2f}  
        **Outbound**: {flight['origin']} → {flight['destination']} ({flight['depart_date']})  
        **Return**: {flight['destination']} → {flight['origin']} ({flight['return_date']})
        """
        
        if 'flight_number' in flight and flight['flight_number']:
            flight_info += f"\n**Flight Number**: {flight['flight_number']}"
        
        if 'departure_time' in flight and flight['departure_time']:
            flight_info += f"\n**Departure Time**: {flight['departure_time']}"
        
        if 'arrival_time' in flight and flight['arrival_time']:
            flight_info += f"\n**Arrival Time**: {flight['arrival_time']}"
        
        st.markdown(flight_info)
    
    # Accommodation information
    if 'hotel' in itinerary and itinerary['hotel']:
        st.subheader("🏨 Accommodation")
        hotel = itinerary['hotel']
        
        # Format hotel details
        hotel_info = f"""
        **Hotel**: {hotel['name']}  
        **Price**: SGD {hotel['price_per_night']:,.2f} per night  
        **Rating**: {hotel['stars']} ★  
        """
        
        if 'address' in hotel and hotel['address']:
            hotel_info += f"**Address**: {hotel['address']}  "
        
        if 'amenities' in hotel and hotel['amenities']:
            hotel_info += f"\n**Amenities**: {', '.join(hotel['amenities'])}"
        
        st.markdown(hotel_info)
        
        # Alternative hotel options if available
        if 'alternative_hotels' in itinerary and itinerary['alternative_hotels']:
            with st.expander("Alternative Hotel Options"):
                for alt_hotel in itinerary['alternative_hotels']:
                    st.markdown(f"**{alt_hotel['name']}** ({alt_hotel['stars']} ★) - SGD {alt_hotel['price_per_night']:,.2f} per night")
                    if 'description' in alt_hotel and alt_hotel['description']:
                        st.markdown(alt_hotel['description'])
                    st.divider()
    
    # Day-by-day itinerary with tabs
    st.subheader("📅 Day-by-Day Itinerary")
    
    if 'daily_plan' in itinerary and itinerary['daily_plan']:
        # Create tabs for each day
        day_tabs = st.tabs([f"Day {day['day']}" for day in itinerary['daily_plan']])
        
        for i, day in enumerate(itinerary['daily_plan']):
            with day_tabs[i]:
                # Show day header with date
                st.markdown(f"### Day {day['day']} - {day['date']}")
                
                # Format day activities in a structured way
                col1, col2 = st.columns([1, 3])
                
                with col1:
                    st.markdown("**Morning**")
                    st.markdown("**Afternoon**")
                    st.markdown("**Evening**")
                    st.markdown("**Accommodation**")
                
                with col2:
                    st.markdown(day['morning'] if day['morning'] else "No specific activities planned")
                    st.markdown(day['afternoon'] if day['afternoon'] else "No specific activities planned")
                    st.markdown(day['evening'] if day['evening'] else "No specific activities planned")
                    st.markdown(day['accommodation'] if day['accommodation'] else "Not specified")
                
                # Show map for this specific day if available
                if 'day_maps' in itinerary and str(day['day']) in itinerary['day_maps']:
                    st.image(itinerary['day_maps'][str(day['day'])], caption=f"Map for Day {day['day']}")
    
    # Points of interest
    if 'points_of_interest' in itinerary and itinerary['points_of_interest']:
        st.subheader("🎯 Points of Interest")
        
        # Group POIs by category
        poi_categories = {}
        for poi in itinerary['points_of_interest']:
            category = poi['category']
            if category not in poi_categories:
                poi_categories[category] = []
            poi_categories[category].append(poi)
        
        # Create expandable sections for each category
        for category, pois in poi_categories.items():
            with st.expander(f"{category} ({len(pois)} places)"):
                for poi in pois:
                    st.markdown(f"**{poi['name']}** ({poi['rating']} ★)")
                    st.markdown(f"Address: {poi['address']}")
                    if 'description' in poi and poi['description']:
                        st.markdown(poi['description'])
                    st.divider()
    
    # Export options
    st.subheader("Export Options")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export as PDF"):
            st.info("PDF export functionality will be available soon.")
    
    with col2:
        if st.button("Share Itinerary"):
            st.info("Sharing functionality will be available soon.")

def _display_saved_itinerary(itinerary: Dict[str, Any]):
    """Display a saved itinerary with basic formatting."""
    # Re-use the current itinerary display function for consistency
    _display_current_itinerary(itinerary)

def _load_saved_itineraries() -> List[Dict[str, Any]]:
    """Load saved itineraries from the API or local storage."""
    try:
        # If user is authenticated, try to load from API
        auth_token = get_auth_token()
        if auth_token:
            # In a real implementation, this would call an API endpoint
            # For now, we'll use mock data
            return _get_mock_saved_itineraries()
        else:
            # For non-authenticated users, check local storage
            return _get_mock_saved_itineraries()
    except Exception as e:
        st.error(f"Error loading saved itineraries: {str(e)}")
        return []

def _get_mock_saved_itineraries() -> List[Dict[str, Any]]:
    """Return mock saved itineraries for demonstration."""
    return [
        {
            "request_id": "mock-123",
            "origin": "Singapore",
            "destination": "Tokyo",
            "depart_date": "2025-05-15",
            "return_date": "2025-05-22",
            "duration": 7,
            "budget": 2500.00,
            "total_cost": 2100.00,
            "flight": {
                "airline": "SQ",
                "price": 650.00,
                "origin": "Singapore",
                "destination": "Tokyo",
                "depart_date": "2025-05-15",
                "return_date": "2025-05-22",
                "flight_number": "SQ634"
            },
            "hotel": {
                "name": "THE TOKYO STATION HOTEL",
                "price_per_night": 177.42,
                "stars": 4.5,
                "city": "Tokyo",
                "address": "JP"
            },
            "daily_plan": [
                {
                    "day": 1,
                    "date": "2025-05-15",
                    "description": "Arrival and check-in day",
                    "morning": "Arrive at Narita Airport. Take the Narita Express to Tokyo (SGD 30).",
                    "afternoon": "Check-in at THE TOKYO STATION HOTEL. Rest and freshen up.",
                    "evening": "Dinner at Downtown B's Indian Kitchen (SGD 20). Explore the nearby area.",
                    "accommodation": "THE TOKYO STATION HOTEL"
                },
                {
                    "day": 2,
                    "date": "2025-05-16",
                    "description": "Cultural exploration day",
                    "morning": "Visit Tokyo National Museum (SGD 10). Explore exhibits of Japanese art and history.",
                    "afternoon": "Lunch at local restaurant. Visit teamLab Borderless digital art museum (SGD 30).",
                    "evening": "Dinner in Asakusa area. Evening light show at Tokyo Skytree.",
                    "accommodation": "THE TOKYO STATION HOTEL"
                }
            ]
        },
        {
            "request_id": "mock-456",
            "origin": "Singapore",
            "destination": "Paris",
            "depart_date": "2025-06-10",
            "return_date": "2025-06-20",
            "duration": 10,
            "budget": 3500.00,
            "total_cost": 3200.00,
            "flight": {
                "airline": "AF",
                "price": 1200.00,
                "origin": "Singapore",
                "destination": "Paris",
                "depart_date": "2025-06-10",
                "return_date": "2025-06-20"
            },
            "hotel": {
                "name": "Hôtel Plaza Athénée",
                "price_per_night": 180.00,
                "stars": 4.0,
                "city": "Paris"
            },
            "daily_plan": [
                {
                    "day": 1,
                    "date": "2025-06-10",
                    "description": "Arrival in Paris",
                    "morning": "Arrive at Charles de Gaulle Airport. Take airport shuttle to hotel.",
                    "afternoon": "Check-in at Hôtel Plaza Athénée. Brief walking tour around the neighborhood.",
                    "evening": "Welcome dinner at local Parisian bistro. Early night due to jet lag.",
                    "accommodation": "Hôtel Plaza Athénée"
                }
            ]
        }
    ]

def _save_itinerary(itinerary: Dict[str, Any]) -> bool:
    """Save the current itinerary to the API or local storage."""
    try:
        # If user is authenticated, save to API
        auth_token = get_auth_token()
        if auth_token:
            # In a real implementation, this would call an API endpoint
            # For now, just return success
            return True
        else:
            # For non-authenticated users, save to local storage or show login prompt
            st.info("Please log in to save itineraries.")
            return False
    except Exception as e:
        st.error(f"Error saving itinerary: {str(e)}")
        return False