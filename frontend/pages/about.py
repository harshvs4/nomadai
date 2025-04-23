import streamlit as st
from utils.session import set_page

def show_about_page():
    """Display the about page with information about NomadAI."""
    
    st.header("About NomadAI")
    
    st.markdown("""
    ## Your Intelligent Travel Companion
    
    **NomadAI** is an innovative travel planning platform that combines artificial intelligence with comprehensive travel data to create personalized travel experiences.
    
    ### Our Mission
    
    We believe that planning a trip should be as enjoyable as the journey itself. Our mission is to simplify travel planning while preserving the joy of discovery.
    
    ### How NomadAI Works
    
    NomadAI uses advanced machine learning and natural language processing to understand your travel preferences, budget constraints, and personal interests. Then, it searches through thousands of travel options to create a customized itinerary just for you.
    
    1. **Personalized Recommendations**: Our AI analyzes your preferences to suggest destinations, activities, and accommodations that match your unique travel style.
    
    2. **Real-Time Data**: We integrate with travel APIs to provide up-to-date information on flights, hotels, and attractions.
    
    3. **Budget Optimization**: NomadAI helps you make the most of your travel budget by balancing costs across transportation, accommodation, and activities.
    
    4. **Continuous Learning**: The more you use NomadAI, the better it gets at understanding your preferences and making recommendations you'll love.
    """)
    
    # Team section
    st.subheader("Our Team")
    
    team_col1, team_col2 = st.columns(2)
    
    with team_col1:
        st.markdown("""
        **Group 1 - NUS Business Analytics**
        
        - Harsh Sharma (A0295906N)
        - Gudur Venkata Rajeshwari (A0297977W)
        - Shivika Mathur (A0298106Y)
        - Soumya Haridas (A0296635N)
        - Vijit Daroch (A0296998R)
        """)
    
    with team_col2:
        st.markdown("""
        This project was developed as part of:
        
        **BT5153 - Applied Machine Learning for Business Analytics**  
        National University of Singapore  
        AY 2024/25 SEMESTER 2
        """)
    
    # Technology stack
    st.subheader("Technology Stack")
    
    tech_col1, tech_col2, tech_col3 = st.columns(3)
    
    with tech_col1:
        st.markdown("#### Backend")
        st.markdown("""
        - FastAPI
        - SQLAlchemy
        - OpenAI GPT models
        - JWT Authentication
        """)
    
    with tech_col2:
        st.markdown("#### Frontend")
        st.markdown("""
        - Streamlit
        - Pandas
        - Matplotlib/Plotly
        - Streamlit Components
        """)
    
    with tech_col3:
        st.markdown("#### Data Sources")
        st.markdown("""
        - Amadeus Travel API
        - Google Places API
        - Custom travel datasets
        """)
    
    # Legal & Privacy
    st.subheader("Legal & Privacy")
    
    with st.expander("Terms of Service"):
        st.markdown("""
        **Terms of Service**
        
        By using NomadAI, you agree to the following terms:
        
        1. **User Content**: You are responsible for the content you provide to our platform.
        
        2. **Service Usage**: You agree to use our service for lawful purposes only.
        
        3. **Account Security**: You are responsible for maintaining the security of your account.
        
        4. **Service Changes**: We reserve the right to modify or discontinue the service at any time.
        
        5. **Third-Party Services**: We integrate with third-party services that have their own terms.
        
        These terms are subject to change. Please check regularly for updates.
        """)
    
    with st.expander("Privacy Policy"):
        st.markdown("""
        **Privacy Policy**
        
        At NomadAI, we take your privacy seriously:
        
        1. **Data Collection**: We collect information you provide and data about your usage of our service.
        
        2. **Data Usage**: We use your data to personalize your experience and improve our service.
        
        3. **Data Sharing**: We do not sell your personal data. We share data with third-party services only as necessary to provide our service.
        
        4. **Data Security**: We implement reasonable measures to protect your data.
        
        5. **Your Rights**: You have the right to access, correct, and delete your data.
        
        For more details, contact us at privacy@nomadai-example.com.
        """)
    
    # Contact and Feedback
    st.subheader("Contact & Feedback")
    
    st.markdown("""
    We'd love to hear from you! Whether you have a question, suggestion, or just want to share your experience, please reach out to us.
    
    - **Email**: support@nomadai-example.com
    - **GitHub**: [NomadAI Project](https://github.com/example/nomadai)
    """)
    
    # Call to action
    st.divider()
    cta_col1, cta_col2, cta_col3 = st.columns([2, 3, 2])
    
    with cta_col2:
        st.markdown("### Ready to plan your next adventure?")
        st.button("Start Planning Now", type="primary", key="about_cta_button", 
                  on_click=lambda: set_page('planner'), use_container_width=True)