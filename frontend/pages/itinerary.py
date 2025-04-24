import streamlit as st
import requests
import json
from datetime import datetime, date
import re
import pandas as pd

from utils.api import get_api_url, summarize_itinerary
from utils.session import get_auth_token, set_page
import os
import sys
from dotenv import load_dotenv
import openai
load_dotenv()
def show_itinerary_page():
    """Display the itinerary page with saved and current itineraries."""
    
    st.header("📋 Your Travel Itineraries")
    
    # Check if we have a current itinerary
    has_current_itinerary = st.session_state.get('itinerary') is not None
    
    # Create tabs for current and saved itineraries
    if has_current_itinerary:
        tab1, tab2 = st.tabs(["Current Itinerary", "Saved Itineraries"])
        
        with tab1:
            display_current_itinerary()
        
        with tab2:
            display_saved_itineraries()
    else:
        # Only saved itineraries tab if no current itinerary
        display_saved_itineraries()
        
        # Show a message and button to create a new itinerary
        st.info("No current itinerary. Create a new trip plan!")
        if st.button("Create New Itinerary", type="primary"):
            set_page('planner')
            st.rerun()

def display_current_itinerary():
    """Display the current itinerary from session state."""
    
    itinerary = st.session_state.itinerary
    if not itinerary:
        st.warning("No current itinerary found.")
        return
    
    # Display itinerary summary
    st.subheader(f"Trip to {itinerary.get('travel_request', {}).get('destination', 'Unknown')}")
    
    # Basic trip details
    travel_request = itinerary.get('travel_request', {})
    origin = travel_request.get('origin', 'Unknown')
    destination = travel_request.get('destination', 'Unknown')
    start_date = parse_date(travel_request.get('depart_date'))
    end_date = parse_date(travel_request.get('return_date'))
    budget = travel_request.get('budget', 0)
    
    # Display trip overview
    trip_col1, trip_col2, trip_col3 = st.columns(3)
    
    with trip_col1:
        st.metric("Origin", origin)
        st.metric("Duration", f"{(end_date - start_date).days} days")
    
    with trip_col2:
        st.metric("Destination", destination)
        st.metric("Budget", f"SGD {budget:,.2f}")
    
    with trip_col3:
        st.metric("Dates", f"{start_date.strftime('%d %b')} - {end_date.strftime('%d %b %Y')}")
        st.metric("Total Cost", f"SGD {itinerary.get('total_cost', 0):,.2f}")
    
    # Action buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Save Itinerary", type="primary"):
            save_current_itinerary()
    
    with col2:
        if st.button("Modify Itinerary"):
            set_page('planner')
            st.rerun()
    
    with col3:
        if st.button("Export as PDF", disabled=True):
            st.info("PDF export feature coming soon!")
    
    # Display flight details
    st.subheader("✈️ Flight")
    if 'selected_flight' in itinerary and itinerary['selected_flight']:
        flight = itinerary['selected_flight']
        
        flight_col1, flight_col2 = st.columns(2)
        
        with flight_col1:
            st.markdown(f"**Airline**: {flight.get('airline', 'Unknown')}")
            st.markdown(f"**Flight Number**: {flight.get('flight_number', 'Unknown')}")
            st.markdown(f"**Price**: SGD {flight.get('price', 0):,.2f}")
        
        with flight_col2:
            depart_time = flight.get('departure_time', '').split('T')[1].split('.')[0] if 'T' in flight.get('departure_time', '') else flight.get('departure_time', '')
            arrival_time = flight.get('arrival_time', '').split('T')[1].split('.')[0] if 'T' in flight.get('arrival_time', '') else flight.get('arrival_time', '')
            
            st.markdown(f"**{origin} → {destination}**: {start_date.strftime('%d %b')} {depart_time}")
            st.markdown(f"**{destination} → {origin}**: {end_date.strftime('%d %b')} {arrival_time}")
    else:
        st.info("No flight details available.")
    
    # Display hotel details
    st.subheader("🏨 Accommodation")
    if 'selected_hotel' in itinerary and itinerary['selected_hotel']:
        hotel = itinerary['selected_hotel']
        
        hotel_col1, hotel_col2 = st.columns(2)
        
        with hotel_col1:
            st.markdown(f"**Hotel**: {hotel.get('name', 'Unknown')}")
            st.markdown(f"**Rating**: {'⭐' * int(hotel.get('stars', 0))}")
            
        with hotel_col2:
            st.markdown(f"**Price per night**: SGD {hotel.get('price_per_night', 0):,.2f}")
            st.markdown(f"**Total ({(end_date - start_date).days} nights)**: SGD {hotel.get('price_per_night', 0) * (end_date - start_date).days:,.2f}")
            
        if hotel.get('address'):
            st.markdown(f"**Address**: {hotel.get('address')}")
        
        if hotel.get('amenities'):
            amenities = hotel.get('amenities')
            if isinstance(amenities, str):
                try:
                    amenities = json.loads(amenities)
                except:
                    amenities = amenities.split(',')
            
            if amenities:
                st.markdown(f"**Amenities**: {', '.join(amenities[:5])}" + (" and more..." if len(amenities) > 5 else ""))
    else:
        st.info("No hotel details available.")
    
    # Display day-by-day itinerary
    st.subheader("📅 Day-by-Day Itinerary")
    
    if 'daily_plan' in itinerary and itinerary['daily_plan']:
        # Create tabs for each day
        day_tabs = st.tabs([f"Day {day['day']}" for day in itinerary['daily_plan']])
        
        for i, day_data in enumerate(itinerary['daily_plan']):
            with day_tabs[i]:
                day_date = parse_date(day_data.get('date'))
                st.markdown(f"### Day {day_data.get('day')} - {day_date.strftime('%A, %d %B')}")
                
                # Morning, Afternoon, Evening schedule
                schedule_col1, schedule_col2, schedule_col3 = st.columns(3)
                
                with schedule_col1:
                    st.markdown("##### Morning")
                    st.markdown(day_data.get('morning', 'No specific activities planned'))
                
                with schedule_col2:
                    st.markdown("##### Afternoon")
                    st.markdown(day_data.get('afternoon', 'No specific activities planned'))
                
                with schedule_col3:
                    st.markdown("##### Evening")
                    st.markdown(day_data.get('evening', 'No specific activities planned'))
                
                # Full description
                if day_data.get('description'):
                    st.markdown("##### Details")
                    st.markdown(day_data.get('description'))
                
                # Accommodation
                if day_data.get('accommodation'):
                    st.markdown(f"**Accommodation**: {day_data.get('accommodation')}")
    else:
        st.info("No daily itinerary available.")
    
    # Display points of interest
    st.subheader("🎯 Points of Interest")
    
    if 'points_of_interest' in itinerary and itinerary['points_of_interest']:
        # Create a dataframe for the POIs
        poi_data = []
        for poi in itinerary['points_of_interest']:
            poi_data.append({
                "Name": poi.get('name', 'Unknown'),
                "Category": poi.get('category', 'Attraction'),
                "Rating": f"{'⭐' * min(5, int(poi.get('rating', 0)))} ({poi.get('rating', 0)})",
                "Address": poi.get('address', 'Address not available')
            })
        
        if poi_data:
            poi_df = pd.DataFrame(poi_data)
            st.dataframe(poi_df, use_container_width=True, hide_index=True)
    else:
        st.info("No points of interest available.")
    
    # Additional notes or summary
    if itinerary.get('summary'):
        st.subheader("📝 Trip Summary")
        st.markdown(itinerary.get('summary'))
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    st.subheader("💬 Chat with NomadAI")
    
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = [
        {
            "role": "system",
            "content": f"You are NomadAI, a smart travel assistant. Help the user modify this new itinerary:\n\n{summarize_itinerary(st.session_state.itinerary)}"
        }
    ]

    if user_input := st.chat_input("Ask NomadAI to modify your itinerary..."):
        st.session_state.chat_history.append({"role": "user", "content": user_input})

    # Compose full context
        messages = [
        {
            "role": "system",
            "content": f"You are NomadAI, a helpful travel planning assistant. Help the user modify this itinerary based on their requests:\n\n{json.dumps(st.session_state.itinerary, indent=2)}"
        }
    ] + st.session_state.chat_history

        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages
    )

        ai_reply = response.choices[0].message.content
        st.session_state.chat_history.append({"role": "assistant", "content": ai_reply})

        with st.chat_message("assistant"):
            st.markdown(ai_reply)


def display_saved_itineraries():
    """Display saved itineraries from the API or a placeholder if not available."""
    
    # If the user is not logged in, show a prompt to login
    if not get_auth_token():
        st.info("Please log in to view your saved itineraries.")
        if st.button("Login"):
            set_page('login')
            st.rerun()
        return
    
    # Try to fetch saved itineraries from the API
    try:
        response = requests.get(
            f"{get_api_url()}/travel/itineraries",
            headers={"Authorization": f"Bearer {get_auth_token()}"}
        )
        
        if response.status_code == 200:
            itineraries = response.json()
            
            if not itineraries:
                st.info("You have no saved itineraries yet.")
                return
            
            # Display itineraries in a grid or list
            for itinerary in itineraries:
                with st.expander(f"Trip to {itinerary.get('destination', 'Unknown')} - {itinerary.get('created_at', '').split('T')[0]}"):
                    display_saved_itinerary_summary(itinerary)
        else:
            # Show a message that there was an error or no saved itineraries
            st.warning("Could not retrieve saved itineraries. Please try again later.")
    
    except Exception as e:
        # If the API is not available, show mock data for demonstration
        st.warning("Could not connect to the server. Showing sample data.")
        
        # Mock data for demonstration
        mock_itineraries = [
            {
                "id": "1",
                "destination": "Tokyo",
                "start_date": "2025-05-15",
                "end_date": "2025-05-22",
                "budget": 3000,
                "created_at": "2025-04-01T12:00:00"
            },
            {
                "id": "2",
                "destination": "Paris",
                "start_date": "2025-07-10",
                "end_date": "2025-07-17",
                "budget": 4000,
                "created_at": "2025-03-15T09:30:00"
            }
        ]
        
        for itinerary in mock_itineraries:
            with st.expander(f"Trip to {itinerary.get('destination')} - {itinerary.get('created_at').split('T')[0]}"):
                display_saved_itinerary_summary(itinerary)

def display_saved_itinerary_summary(itinerary):
    """Display a summary of a saved itinerary."""
   
    # Extract and format dates
    start_date = parse_date(itinerary.get('start_date', None))
    end_date = parse_date(itinerary.get('end_date', None))
    
    if start_date and end_date:
        duration = (end_date - start_date).days
        date_range = f"{start_date.strftime('%d %b')} - {end_date.strftime('%d %b %Y')}"
    else:
        duration = "?"
        date_range = "Dates not available"
    
    # Display summary
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"**Destination**: {itinerary.get('destination', 'Unknown')}")
        st.markdown(f"**Duration**: {duration} days")
    
    with col2:
        st.markdown(f"**Dates**: {date_range}")
        st.markdown(f"**Budget**: SGD {itinerary.get('budget', 0):,.2f}")
    
    with col3:
        # Action buttons
        if st.button("View Details", key=f"view_{itinerary.get('id', '')}"):
            # In a real app, this would load the full itinerary
            st.info("Loading full itinerary details...")
        
        if st.button("Delete", key=f"delete_{itinerary.get('id', '')}"):
            st.warning("This would delete the itinerary in a real app.")

def save_current_itinerary():
    """Save the current itinerary to the user's account."""
    
    if not get_auth_token():
        st.warning("Please log in to save your itinerary.")
        return
    
    try:
        # Make API request to save the itinerary
        response = requests.post(
            f"{get_api_url()}/travel/itineraries",
            json=st.session_state.itinerary,
            headers={"Authorization": f"Bearer {get_auth_token()}"}
        )
        
        if response.status_code == 200:
            st.success("Itinerary saved successfully!")
        else:
            st.error(f"Failed to save itinerary: {response.json().get('detail', 'Unknown error')}")
    
    except Exception as e:
        st.error(f"Error saving itinerary: {str(e)}")
        # For demo purposes, pretend it was saved
        st.success("Itinerary saved successfully! (Demo mode)")

def parse_date(date_str):
    """Parse a date string into a date object, handling various formats."""
    if not date_str:
        return date.today()
    
    if isinstance(date_str, date):
        return date_str
    
    try:
        # Try ISO format (YYYY-MM-DD)
        return datetime.fromisoformat(date_str.split('T')[0]).date()
    except (ValueError, AttributeError):
        try:
            # Try other common formats
            date_patterns = [
                '%Y-%m-%d',
                '%d/%m/%Y',
                '%m/%d/%Y',
                '%d-%m-%Y',
                '%m-%d-%Y',
                '%d %b %Y',
                '%d %B %Y'
            ]
            
            for pattern in date_patterns:
                try:
                    return datetime.strptime(date_str, pattern).date()
                except ValueError:
                    continue
            
            # If all formats fail, return today's date
            return date.today()
        except:
            return date.today()