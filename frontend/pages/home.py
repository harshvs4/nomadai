import streamlit as st
import requests
from datetime import date, timedelta
import random

from utils.api import get_api_url
from utils.session import set_page

def show_home_page():
    """Display the home page content."""
    
    # Hero section
    st.header("Plan Your Perfect Trip with AI")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("""
        **NomadAI** helps you create personalized travel itineraries based on your preferences and budget.
        
        ✅ **Save time** researching and planning
        
        ✅ **Discover** hidden gems and local favorites
        
        ✅ **Stay within budget** with cost-optimized recommendations
        
        ✅ **Customize** every aspect of your journey
        """)
        
        # Quick start planning button
        if st.button("Start Planning Your Trip", type="primary", use_container_width=True):
            set_page('planner')
            st.experimental_rerun()
    
    with col2:
        # Display a sample itinerary preview or illustration
        st.image("https://via.placeholder.com/400x300?text=AI+Travel+Planning", 
                 caption="Your perfect itinerary awaits")
    
    # Featured destinations
    st.subheader("Popular Destinations")
    
    # Fetch popular cities from API or use fallback
    try:
        response = requests.get(f"{get_api_url()}/travel/popular-cities")
        if response.status_code == 200:
            popular_cities = response.json().get("cities", [])
        else:
            raise Exception("Failed to fetch popular cities")
    except Exception as e:
        # Fallback list if API fails
        popular_cities = [
            "Tokyo", "Paris", "New York", "Singapore", "London", 
            "Bangkok", "Dubai", "Sydney", "Barcelona", "Rome"
        ]
    
    # Display popular destinations as a grid
    cols = st.columns(5)
    for i, city in enumerate(popular_cities[:10]):
        with cols[i % 5]:
            st.button(
                city,
                key=f"city_{city}",
                on_click=lambda c=city: select_destination(c),
                use_container_width=True
            )
    
    # Testimonials section
    st.subheader("What Our Users Say")
    
    testimonials = [
        {
            "name": "Sarah L.",
            "text": "NomadAI planned my entire Tokyo trip in minutes! It found hidden gems I would have never discovered on my own.",
            "rating": "⭐⭐⭐⭐⭐",
        },
        {
            "name": "Michael T.",
            "text": "As a budget traveler, I was impressed by how well it optimized my trip to stay within my means while still having amazing experiences.",
            "rating": "⭐⭐⭐⭐",
        },
        {
            "name": "Elena R.",
            "text": "The recommendations were spot-on for our family vacation. The kids loved all the activities!",
            "rating": "⭐⭐⭐⭐⭐",
        }
    ]
    
    testimonial_cols = st.columns(3)
    for i, testimonial in enumerate(testimonials):
        with testimonial_cols[i]:
            st.markdown(f"""
            > "{testimonial['text']}"
            >
            > {testimonial['rating']} - {testimonial['name']}
            """)
    
    # How it works section
    st.subheader("How It Works")
    
    how_it_works_cols = st.columns(3)
    
    with how_it_works_cols[0]:
        st.markdown("### 1. Share Your Preferences")
        st.markdown("Tell us where you want to go, your budget, and what you enjoy.")
        
    with how_it_works_cols[1]:
        st.markdown("### 2. AI Creates Your Plan")
        st.markdown("Our AI analyzes thousands of options to craft your perfect itinerary.")
        
    with how_it_works_cols[2]:
        st.markdown("### 3. Customize & Enjoy")
        st.markdown("Fine-tune your plan if needed, then embark on your dream trip!")
    
    # Call to action
    st.divider()
    cta_col1, cta_col2, cta_col3 = st.columns([2, 3, 2])
    
    with cta_col2:
        st.markdown("### Ready for your next adventure?")
        st.button("Plan My Trip Now", type="primary", key="cta_button", 
                  on_click=lambda: set_page('planner'), use_container_width=True)

def select_destination(city):
    """Handle selection of a featured destination."""
    st.session_state.selected_destination = city
    set_page('planner')