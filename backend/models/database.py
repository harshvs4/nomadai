import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import os

from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Table, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from config import settings

logger = logging.getLogger(__name__)

# Base SQLAlchemy model
Base = declarative_base()

# Define SQLAlchemy models
class DBUser(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    profile = relationship("DBUserProfile", back_populates="user", uselist=False)
    itineraries = relationship("DBItinerary", back_populates="user")

class DBUserProfile(Base):
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    avatar_url = Column(String)
    bio = Column(String)
    location = Column(String)
    travel_preferences = Column(String)  # JSON list as string
    favorite_destinations = Column(String)  # JSON list as string
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("DBUser", back_populates="profile")

class DBItinerary(Base):
    __tablename__ = "itineraries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String)
    origin = Column(String)
    destination = Column(String)
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    budget = Column(Float)
    preferences = Column(String)  # JSON list as string
    summary = Column(String)
    total_cost = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("DBUser", back_populates="itineraries")
    flight = relationship("DBFlight", back_populates="itinerary", uselist=False)
    hotel = relationship("DBHotel", back_populates="itinerary", uselist=False)
    days = relationship("DBItineraryDay", back_populates="itinerary")
    pois = relationship("DBPointOfInterest", back_populates="itinerary")

class DBFlight(Base):
    __tablename__ = "flights"
    
    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"))
    airline = Column(String)
    price = Column(Float)
    origin = Column(String)
    destination = Column(String)
    depart_date = Column(DateTime)
    return_date = Column(DateTime)
    flight_number = Column(String)
    departure_time = Column(String)
    arrival_time = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    itinerary = relationship("DBItinerary", back_populates="flight")

class DBHotel(Base):
    __tablename__ = "hotels"
    
    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"))
    name = Column(String)
    price_per_night = Column(Float)
    stars = Column(Float)
    city = Column(String)
    address = Column(String)
    amenities = Column(String)  # JSON list as string
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    itinerary = relationship("DBItinerary", back_populates="hotel")

class DBPointOfInterest(Base):
    __tablename__ = "points_of_interest"
    
    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"))
    name = Column(String)
    category = Column(String)
    rating = Column(Float)
    address = Column(String)
    description = Column(String)
    image_url = Column(String)
    price_level = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    itinerary = relationship("DBItinerary", back_populates="pois")

class DBItineraryDay(Base):
    __tablename__ = "itinerary_days"
    
    id = Column(Integer, primary_key=True, index=True)
    itinerary_id = Column(Integer, ForeignKey("itineraries.id"))
    day = Column(Integer)
    date = Column(DateTime)
    description = Column(String)
    morning = Column(String)
    afternoon = Column(String)
    evening = Column(String)
    accommodation = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    itinerary = relationship("DBItinerary", back_populates="days")

# Database setup
async def init_db():
    """Initialize the database and create tables."""
    try:
        # For all database types, use synchronous approach for simplicity
        sync_engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith('sqlite') else {}
        )
        Base.metadata.create_all(bind=sync_engine)
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise

# Database session dependency
async def get_db_session():
    """Get a database session."""
    # Use synchronous connections for all database types
    engine = create_engine(
        settings.DATABASE_URL,
        # Only add this parameter for SQLite
        connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith('sqlite') else {}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()