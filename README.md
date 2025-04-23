# NomadAI - Your Intelligent Travel Companion

NomadAI is an AI-powered travel planning platform that creates personalized travel itineraries based on user preferences and budget constraints. This project was developed as part of the BT5153 - Applied Machine Learning for Business Analytics course at the National University of Singapore.

## Features

- **Personalized Itineraries**: Generate detailed travel plans tailored to user interests and budget
- **Real-time Data**: Integration with travel APIs for up-to-date flight, hotel, and attraction information
- **AI-Powered Recommendations**: Utilizes LLMs to create coherent, customized travel plans
- **User Profiles**: Save preferences and favorite destinations for faster planning
- **Interactive Interface**: Easy-to-use web interface for planning and viewing itineraries

## Architecture

The project is built with a modern tech stack:

- **Backend**: FastAPI, SQLAlchemy, OpenAI API
- **Frontend**: Streamlit
- **External APIs**: Amadeus Travel API, Google Places API
- **Database**: PostgreSQL
- **Containerization**: Docker & Docker Compose

## Getting Started

### Prerequisites

- Docker and Docker Compose
- API keys for:
  - OpenAI
  - Amadeus Travel API
  - Google Places API

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/nomadai.git
   cd nomadai
   ```

2. Create an environment file from the example:
   ```
   cp .env.example .env
   ```

3. Edit the `.env` file to add your API keys and other configuration.

4. Start the application using Docker Compose:
   ```
   docker-compose -f docker/docker-compose.yml up -d
   ```

5. Access the application:
   - Frontend: http://localhost:8501
   - Backend API: http://localhost:8000/docs

### Running Without Docker

#### Backend

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements-backend.txt
   ```

3. Run the backend:
   ```
   cd backend
   uvicorn app:app --reload
   ```

#### Frontend

1. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```
   pip install -r requirements-frontend.txt
   ```

3. Run the frontend:
   ```
   cd frontend
   streamlit run app.py
   ```

## Project Structure

```
nomadai/
│
├── backend/                      # FastAPI backend
│   ├── app.py                    # Main application entry point
│   ├── config.py                 # Configuration
│   ├── models/                   # Data models
│   ├── services/                 # Business logic and external API integrations
│   ├── routers/                  # API routes
│   └── utils/                    # Utility functions
│
├── frontend/                     # Streamlit frontend
│   ├── app.py                    # Main application
│   ├── pages/                    # UI pages
│   ├── components/               # Reusable UI components
│   ├── utils/                    # Utility functions
│   └── static/                   # Static assets
│
├── docker/                       # Docker configuration
│   ├── Dockerfile.backend        # Backend Dockerfile
│   ├── Dockerfile.frontend       # Frontend Dockerfile
│   └── docker-compose.yml        # Docker Compose configuration
│
├── .env.example                  # Example environment variables
├── requirements-backend.txt      # Backend dependencies
├── requirements-frontend.txt     # Frontend dependencies
└── README.md                     # Project documentation
```

## Team

- Harsh Sharma (A0295906N)
- Gudur Venkata Rajeshwari (A0297977W)
- Shivika Mathur (A0298106Y)
- Soumya Haridas (A0296635N)
- Vijit Daroch (A0296998R)

## License

This project is licensed under the MIT License - see the LICENSE file for details.