import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
print(env_path)
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    # API Settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "NomadAI"
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./nomadai.db")
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"  # Added missing algorithm for JWT
    
    # External APIs
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    
    AMADEUS_API_KEY: str = os.getenv("AMADEUS_API_KEY", "")
    AMADEUS_API_SECRET: str = os.getenv("AMADEUS_API_SECRET", "")
    AMADEUS_TEST_MODE: bool = os.getenv("AMADEUS_TEST_MODE", "True").lower() == "true"
    
    GOOGLE_PLACES_KEY: str = os.getenv("GOOGLE_PLACES_KEY", "")
    
    # Cache settings
    CACHE_EXPIRATION: int = 3600  # 1 hour in seconds
    
    # CORS
    BACKEND_CORS_ORIGINS: list = [
        "http://localhost:8501",  # Streamlit frontend
        "http://localhost:8000",  # FastAPI backend (for development)
        "https://nomadai.example.com",  # Production URL
    ]
    
    class Config:
        case_sensitive = True

# Create global settings object
settings = Settings()

def get_env(key: str) -> str:
    """Get environment variable or raise exception if not set."""
    value = os.getenv(key)
    if not value:
        raise ValueError(f"Environment variable '{key}' not set.")
    return value