import logging
from typing import List, Optional, Dict
from datetime import date
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from services.amadeus_service import AmadeusService
from services.google_places_service import GooglePlacesService
from services.llm_service import LLMPlanningService
from services.cache_service import get_cache_service
from models.travel import (
    TravelRequest, TravelRequestCreate, FlightOption, 
    HotelOption, PointOfInterest, Itinerary
)
from utils.auth import get_current_user
from models.user import User

router = APIRouter()
logger = logging.getLogger(__name__)

# Response models
class CityListResponse(BaseModel):
    cities: List[str]

class FlightSearchResponse(BaseModel):
    flights: List[FlightOption]

class HotelSearchResponse(BaseModel):
    hotels: List[HotelOption]

class PoiSearchResponse(BaseModel):
    points_of_interest: List[PointOfInterest]

# Service dependencies
def get_amadeus_service():
    return AmadeusService()

def get_google_places_service():
    return GooglePlacesService()

def get_llm_service():
    return LLMPlanningService()

# In-memory storage for itineraries (key: user_email, value: list of itineraries)
user_itineraries: Dict[str, List[Itinerary]] = {}

# Routes
@router.post("/itinerary", response_model=Itinerary)
async def create_itinerary(
    travel_req: TravelRequestCreate,
    amadeus_service: AmadeusService = Depends(get_amadeus_service),
    google_places_service: GooglePlacesService = Depends(get_google_places_service),
    llm_service: LLMPlanningService = Depends(get_llm_service),
    current_user: User = Depends(get_current_user),
    cache_service = Depends(get_cache_service),
):
    """
    Create a complete travel itinerary based on user input.
    """
    try:
        logger.info(f"Creating itinerary: {travel_req.origin} to {travel_req.destination}")
        
        # Calculate duration
        from datetime import datetime
        depart = datetime.strptime(str(travel_req.depart_date), "%Y-%m-%d")
        return_date = datetime.strptime(str(travel_req.return_date), "%Y-%m-%d")
        duration = (return_date - depart).days + 1
        
        # Convert TravelRequestCreate to TravelRequest
        travel_request = TravelRequest(
            origin=travel_req.origin,
            destination=travel_req.destination,
            depart_date=travel_req.depart_date,
            return_date=travel_req.return_date,
            budget=travel_req.budget,
            preferences=travel_req.preferences,
            duration=duration  # Set the calculated duration
        )
        
        # Generate itinerary using LLM
        itinerary = await llm_service.generate_itinerary(
            travel_request,
            amadeus_service,
            google_places_service,
            cache_service
        )
        
        # Save the itinerary
        if current_user.email not in user_itineraries:
            user_itineraries[current_user.email] = []
        user_itineraries[current_user.email].append(itinerary)
        
        return itinerary
        
    except Exception as e:
        logger.error(f"Error creating itinerary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create itinerary: {str(e)}"
        )

@router.get("/flights", response_model=FlightSearchResponse)
async def search_flights(
    origin: str = Query(..., description="Origin city"),
    destination: str = Query(..., description="Destination city"),
    depart_date: date = Query(..., description="Departure date"),
    return_date: date = Query(..., description="Return date"),
    amadeus_service: AmadeusService = Depends(get_amadeus_service),
    cache_service = Depends(get_cache_service),
):
    """Search for flight options between cities."""
    cache_key = f"flights:{origin}:{destination}:{depart_date}:{return_date}"
    cached_result = await cache_service.get(cache_key)
    
    if cached_result:
        return FlightSearchResponse(flights=cached_result)
    
    try:
        flights = amadeus_service.get_flight_offers(
            origin, destination, depart_date, return_date
        )
        
        # Cache the result
        await cache_service.set(cache_key, flights, expiry=3600)  # 1 hour
        
        return FlightSearchResponse(flights=flights)
        
    except Exception as e:
        logger.error(f"Error searching flights: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching flights: {str(e)}"
        )

@router.get("/hotels", response_model=HotelSearchResponse)
async def search_hotels(
    city: str = Query(..., description="City name"),
    checkin_date: date = Query(..., description="Check-in date"),
    checkout_date: date = Query(..., description="Check-out date"),
    amadeus_service: AmadeusService = Depends(get_amadeus_service),
    cache_service = Depends(get_cache_service),
):
    """Search for hotel options in a city."""
    cache_key = f"hotels:{city}:{checkin_date}:{checkout_date}"
    cached_result = await cache_service.get(cache_key)
    
    if cached_result:
        return HotelSearchResponse(hotels=cached_result)
    
    try:
        hotels = amadeus_service.get_hotel_offers(
            city, checkin_date, checkout_date
        )
        
        # Cache the result
        await cache_service.set(cache_key, hotels, expiry=3600)  # 1 hour
        
        return HotelSearchResponse(hotels=hotels)
        
    except Exception as e:
        logger.error(f"Error searching hotels: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching hotels: {str(e)}"
        )

@router.get("/points-of-interest", response_model=PoiSearchResponse)
async def search_points_of_interest(
    city: str = Query(..., description="City name"),
    preferences: List[str] = Query([], description="Travel preferences"),
    google_places_service: GooglePlacesService = Depends(get_google_places_service),
    cache_service = Depends(get_cache_service),
):
    """Search for points of interest in a city based on preferences."""
    preferences_str = ",".join(sorted(preferences))
    cache_key = f"pois:{city}:{preferences_str}"
    cached_result = await cache_service.get(cache_key)
    
    if cached_result:
        return PoiSearchResponse(points_of_interest=cached_result)
    
    try:
        pois = google_places_service.get_points_of_interest(city, preferences)
        
        # Cache the result
        await cache_service.set(cache_key, pois, expiry=3600 * 24)  # 24 hours
        
        return PoiSearchResponse(points_of_interest=pois)
        
    except Exception as e:
        logger.error(f"Error searching points of interest: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching points of interest: {str(e)}"
        )

@router.get("/popular-cities", response_model=CityListResponse)
async def get_popular_cities():
    """Get a list of popular cities for travel."""
    # This would typically come from a database or analytics
    popular_cities = [
        "Singapore", "Tokyo", "Paris", "London", "New York",
        "Bangkok", "Dubai", "Sydney", "San Francisco", "Los Angeles",
        "Barcelona", "Rome", "Hong Kong", "Seoul", "Bali"
    ]
    
    return CityListResponse(cities=popular_cities)

@router.get("/itineraries", response_model=List[Itinerary])
async def get_itineraries(
    current_user: User = Depends(get_current_user),
    cache_service = Depends(get_cache_service),
):
    """
    Get all itineraries for the current user.
    """
    try:
        # Return the user's itineraries or an empty list if none exist
        return user_itineraries.get(current_user.email, [])
        
    except Exception as e:
        logger.error(f"Error fetching itineraries: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch itineraries"
        )

@router.post("/itineraries", response_model=Itinerary)
async def save_itinerary(
    itinerary: Itinerary,
    current_user: User = Depends(get_current_user),
    cache_service = Depends(get_cache_service),
):
    """
    Save a new itinerary for the current user.
    """
    try:
        # Validate the itinerary data
        if not itinerary.travel_request or not itinerary.travel_request.destination:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid itinerary data: missing destination"
            )
            
        # Calculate duration if not set
        if not itinerary.travel_request.duration:
            from datetime import datetime
            depart = datetime.strptime(str(itinerary.travel_request.depart_date), "%Y-%m-%d")
            return_date = datetime.strptime(str(itinerary.travel_request.return_date), "%Y-%m-%d")
            duration = (return_date - depart).days + 1
            itinerary.travel_request.duration = duration

        # Initialize the user's itinerary list if it doesn't exist
        if current_user.email not in user_itineraries:
            user_itineraries[current_user.email] = []
        
        # Add the new itinerary to the user's list
        user_itineraries[current_user.email].append(itinerary)
        
        return itinerary
        
    except Exception as e:
        logger.error(f"Error saving itinerary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save itinerary: {str(e)}"
        )