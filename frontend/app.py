import streamlit as st
import os
from datetime import date, timedelta
import requests
import json

# Import pages
from pages.home import show_home_page
from pages.planner import show_planner_page
from pages.itinerary import show_itinerary_page
from pages.profile import show_profile_page
from pages.about import show_about_page

# Import utils
from utils.session import get_auth_token, get_user_info, logout_user
from utils.api import get_api_url

# App configuration
st.set_page_config(
    page_title="NomadAI - Your Travel Planning Assistant",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
def load_css():
    with open(os.path.join(os.path.dirname(__file__), "static/css/style.css")) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Initialize session state if needed
if 'page' not in st.session_state:
    st.session_state.page = 'home'

if 'itinerary' not in st.session_state:
    st.session_state.itinerary = None

# App Header
def show_header():
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        st.image(os.path.join(os.path.dirname(__file__), "static/images/logo.png"), width=100)
    
    with col2:
        st.title("NomadAI - Your Intelligent Travel Companion")
    
    with col3:
        user_info = get_user_info()
        if user_info:
            st.write(f"Welcome, {user_info.get('username', 'User')}!")
            if st.button("Logout"):
                logout_user()
                st.experimental_rerun()
        else:
            st.button("Login", on_click=lambda: set_page('login'))

# Navigation sidebar
def show_sidebar():
    with st.sidebar:
        st.header("Navigation")
        
        if st.button("🏠 Home", key="nav_home", use_container_width=True):
            st.session_state.page = 'home'
            st.experimental_rerun()
        
        if st.button("🗺️ Plan a Trip", key="nav_planner", use_container_width=True):
            st.session_state.page = 'planner'
            st.experimental_rerun()
        
        if get_auth_token():
            if st.button("📋 My Itineraries", key="nav_itineraries", use_container_width=True):
                st.session_state.page = 'itineraries'
                st.experimental_rerun()
            
            if st.button("👤 My Profile", key="nav_profile", use_container_width=True):
                st.session_state.page = 'profile'
                st.experimental_rerun()
        
        if st.button("ℹ️ About", key="nav_about", use_container_width=True):
            st.session_state.page = 'about'
            st.experimental_rerun()
        
        st.divider()
        
        # Quick travel tips
        st.subheader("Travel Tips")
        tips = [
            "Pack light and smart!",
            "Research local customs before you go.",
            "Always have a backup of important documents.",
            "Learn a few phrases in the local language.",
            "Try the local cuisine!",
        ]
        tip_idx = date.today().day % len(tips)
        st.info(f"💡 **Tip of the day**: {tips[tip_idx]}")
        
        # Footer
        st.divider()
        st.caption("NomadAI © 2025")
        st.caption("Powered by AI & Travel Experts")

# Login/Registration page
def show_login_page():
    st.header("Login")
    
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                try:
                    response = requests.post(
                        f"{get_api_url()}/auth/token",
                        data={"username": username, "password": password}
                    )
                    
                    if response.status_code == 200:
                        token_data = response.json()
                        st.session_state.auth_token = token_data["access_token"]
                        st.success("Login successful!")
                        st.session_state.page = 'home'
                        st.experimental_rerun()
                    else:
                        st.error("Invalid username or password")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
    
    with tab2:
        with st.form("register_form"):
            new_username = st.text_input("Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Register")
            
            if submitted:
                if new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    try:
                        response = requests.post(
                            f"{get_api_url()}/auth/register",
                            data={"username": new_username, "password": new_password}
                        )
                        
                        if response.status_code == 200:
                            st.success("Registration successful! Please login.")
                        else:
                            st.error(f"Registration failed: {response.json().get('detail', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")

# Set current page
def set_page(page_name):
    st.session_state.page = page_name

# Main app layout
def main():
    show_header()
    show_sidebar()
    
    # Display the selected page
    if st.session_state.page == 'home':
        show_home_page()
    elif st.session_state.page == 'planner':
        show_planner_page()
    elif st.session_state.page == 'itineraries':
        show_itinerary_page()
    elif st.session_state.page == 'profile':
        show_profile_page()
    elif st.session_state.page == 'about':
        show_about_page()
    elif st.session_state.page == 'login':
        show_login_page()

if __name__ == "__main__":
    main()