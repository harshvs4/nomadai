from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import date, datetime
from pydantic import BaseModel, Field

class TravelPreference(str, Enum):
    CULTURE = "Culture"
    RELAXATION = "Relaxation"
    ADVENTURE = "Adventure"
    FOOD = "Food"
    NATURE = "Nature"
    NIGHTLIFE = "Nightlife"
    LUXURY = "Luxury"
    BUDGET = "Budget"
    FAMILY = "Family"
    SHOPPING = "Shopping"
    BEACH = "Beach"
    MOUNTAIN = "Mountain"

class FlightOption(BaseModel):
    airline: str
    price: float
    origin: str
    destination: str
    depart_date: date
    return_date: date
    flight_number: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None

class TravelRequestCreate(BaseModel):
    origin: str
    destination: str
    depart_date: date
    return_date: date
    budget: float
    preferences: List[str] = []

class HotelOption(BaseModel):
    name: str
    price_per_night: float
    stars: float
    city: str
    address: Optional[str] = None
    hotel_id: Optional[str] = None
    chain_code: Optional[str] = None
    distance: Optional[float] = None
    amenities: Optional[List[str]] = None
    description: Optional[str] = None
    image_url: Optional[str] = None

class PointOfInterest(BaseModel):
    name: str
    category: str
    rating: float
    address: str
    description: Optional[str] = None
    price_level: Optional[int] = None
    image_url: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
class TravelRequest(BaseModel):
    origin: str
    destination: str
    depart_date: date
    return_date: date
    budget: float
    preferences: List[str] = []
    
    @property
    def duration(self) -> int:
        """Calculate the trip duration in days."""
        return max(1, (self.return_date - self.depart_date).days + 1)

class ItineraryDayActivity(BaseModel):
    day: int
    date: date
    description: str
    morning: Optional[str] = None
    afternoon: Optional[str] = None
    evening: Optional[str] = None
    accommodation: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "day": self.day,
            "date": self.date.isoformat(),
            "description": self.description,
            "morning": self.morning,
            "afternoon": self.afternoon,
            "evening": self.evening,
            "accommodation": self.accommodation
        }

class AlternativeHotel(BaseModel):
    name: str
    price_per_night: float
    stars: float
    description: Optional[str] = None

class Itinerary(BaseModel):
    request_id: str
    travel_request: TravelRequest
    selected_flight: Optional[FlightOption] = None
    selected_hotel: Optional[HotelOption] = None
    alternative_hotels: List[AlternativeHotel] = []
    points_of_interest: List[PointOfInterest] = []
    daily_plan: List[ItineraryDayActivity] = []
    summary: str
    total_cost: float
    raw_itinerary: Optional[str] = None
    map_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "origin": self.travel_request.origin,
            "destination": self.travel_request.destination,
            "depart_date": self.travel_request.depart_date.isoformat(),
            "return_date": self.travel_request.return_date.isoformat(),
            "duration": self.travel_request.duration,
            "budget": self.travel_request.budget,
            "flight": self.selected_flight.dict() if self.selected_flight else None,
            "hotel": self.selected_hotel.dict() if self.selected_hotel else None,
            "alternative_hotels": [h.dict() for h in self.alternative_hotels],
            "daily_plan": [day.to_dict() for day in self.daily_plan],
            "summary": self.summary,
            "total_cost": self.total_cost,
            "map_url": self.map_url
        }