import streamlit as st
import requests
from datetime import date, timedelta, datetime
import json
import time
from utils.api import get_api_url, fetch_from_api
from utils.session import get_auth_token, set_page

def show_planner_page():
    """Display the trip planner page."""
    
    st.header("✈️ Trip Planner")
    st.markdown("Tell us about your dream trip, and let our AI create a personalized itinerary for you.")
    
    # Create the trip planning form
    with st.form(key="trip_planner_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            origin = st.text_input(
                "Origin City", 
                value=st.session_state.get('origin', 'Singapore'),
                help="Where will you be traveling from?"
            )
            
            destination = st.text_input(
                "Destination", 
                value=st.session_state.get('selected_destination', ''),
                help="Where do you want to go?"
            )
            
            # Date inputs
            today = date.today()
            default_start = today + timedelta(days=30)  # Default to 1 month from now
            session_start = st.session_state.get('start_date', default_start)  # Default to 1 week trip
            
            start_date = st.date_input(
            "Start Date",
            value=session_start,
            min_value=today
)
            default_end = start_date + timedelta(days=7)
            session_end = st.session_state.get('end_date', default_end)
            end_date = st.date_input(
                "End Date",
             value=session_end if session_end >= start_date + timedelta(days=1) else default_end,
            min_value=start_date + timedelta(days=1)
)
            
            # Calculate duration
            duration = (end_date - start_date).days
            st.caption(f"Trip duration: {duration} days")
        
        with col2:
            # Budget input
            budget = st.number_input(
                "Budget (SGD)", 
                min_value=500, 
                max_value=50000, 
                value=st.session_state.get('budget', 2000),
                step=500,
                help="What's your total budget for this trip?"
            )
            
            # Travel preferences
            preferences = st.multiselect(
                "Travel Preferences",
                options=[
                    "Adventure", "Relaxation", "Culture", "Nightlife",
                    "Nature", "Food", "Luxury", "Budget", "Family",
                    "Shopping", "Beach", "Mountain"
                ],
                default=st.session_state.get('preferences', ["Culture", "Food"]),
                help="Select your travel interests to personalize your itinerary"
            )
            
            # Additional notes
            notes = st.text_area(
                "Additional Notes (Optional)",
                value=st.session_state.get('notes', ''),
                help="Any specific requirements or interests? (e.g., dietary restrictions, accessibility needs)"
            )
        
        # Save preferences checkbox
        save_prefs = False
        if get_auth_token():
            save_prefs = st.checkbox(
                "Save these preferences to my profile", 
                value=False,
                help="We'll remember these preferences for your future trips"
            )
        
        # Submit button
        submit_button = st.form_submit_button("Generate Itinerary", type="primary", use_container_width=True)
    
    # Handle form submission
    if submit_button:
        # Validate inputs
        if not origin or not destination:
            st.error("Please fill in both origin and destination.")
            return
        
        if start_date >= end_date:
            st.error("End date must be after start date.")
            return
        
        # Store form values in session state
        st.session_state.origin = origin
        st.session_state.selected_destination = destination
        st.session_state.start_date = start_date
        st.session_state.end_date = end_date
        st.session_state.budget = budget
        st.session_state.preferences = preferences
        st.session_state.notes = notes
        
        # If user is logged in and wants to save preferences
        if get_auth_token() and save_prefs:
            try:
                # Update user preferences
                response = requests.post(
                    f"{get_api_url()}/users/me/preferences",
                    headers={"Authorization": f"Bearer {get_auth_token()}"},
                    json=preferences
                )
                
                if response.status_code == 200:
                    st.success("Preferences saved to your profile.")
                else:
                    st.warning("Could not save preferences to your profile.")
            except Exception as e:
                st.warning(f"Error saving preferences: {str(e)}")
        
        # Generate the itinerary
        with st.spinner("Creating your personalized itinerary... This may take a minute."):
            try:
                # Prepare the request data
                travel_request = {
                    "origin": origin,
                    "destination": destination,
                    "depart_date": start_date.isoformat(),
                    "return_date": end_date.isoformat(),
                    "budget": float(budget),
                    "preferences": preferences
                }
                
                # Add authorization header if user is logged in
                headers = {}
                if get_auth_token():
                    headers["Authorization"] = f"Bearer {get_auth_token()}"
                
                # Make API request
                response = requests.post(
                    f"{get_api_url()}/travel/itinerary",
                    json=travel_request,
                    headers=headers
                )
                
                if response.status_code == 200:
                    # Store the itinerary in session state
                    st.session_state.itinerary = response.json()
                    #st.session_state.chat_history = []
                    # Show success message
                    st.success("Itinerary created successfully!")
                    
                    # Navigate to itinerary view
                    set_page('itineraries')
                    st.rerun()
                else:
                    error_detail = "Unknown error"
                    try:
                        error_detail = response.json().get("detail", error_detail)
                    except:
                        pass
                    st.error(f"Failed to create itinerary: {error_detail}")
            
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    # Display some inspiration and tips
    st.divider()
    
    # Trending destinations
    st.subheader("Trending Destinations")
    trending_cols = st.columns(4)
    trending_destinations = [
        {"name": "Tokyo", "img": "https://via.placeholder.com/200x150?text=Tokyo", "desc": "Blend of tradition and futuristic innovation"},
        {"name": "Bali", "img": "https://via.placeholder.com/200x150?text=Bali", "desc": "Tropical paradise with rich culture"},
        {"name": "Paris", "img": "https://via.placeholder.com/200x150?text=Paris", "desc": "City of lights, art, and romance"},
        {"name": "New York", "img": "https://via.placeholder.com/200x150?text=New+York", "desc": "The city that never sleeps"}
    ]
    
    for i, dest in enumerate(trending_destinations):
        with trending_cols[i]:
            st.image(dest["img"], caption=dest["name"])
            st.caption(dest["desc"])
            if st.button(f"Plan trip to {dest['name']}", key=f"trend_{dest['name']}"):
                st.session_state.selected_destination = dest["name"]
                st.rerun()
    
    # Travel tips
    st.subheader("Travel Planning Tips")
    st.info("""
    💡 **Pro Tips**:
    
    - Book flights 2-3 months in advance for best rates
    - Consider shoulder seasons for fewer crowds
    - Include some flexibility in your itinerary for spontaneous discoveries
    - Check visa requirements well before your trip
    """)