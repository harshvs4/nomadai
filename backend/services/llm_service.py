import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

import openai
from openai import OpenAI
from fastapi import HTTPException, status

from config import settings
from models.travel import (
    TravelRequest, FlightOption, HotelOption, 
    PointOfInterest, Itinerary, ItineraryDayActivity
)
from services.amadeus_service import AmadeusService
from services.google_places_service import GooglePlacesService

logger = logging.getLogger(__name__)

class LLMPlanningService:
    """
    Service for using LLMs to generate travel itineraries based on
    flight, hotel, and point of interest data.
    """
    
    SYSTEM_PROMPT = """
    You are NomadAI, an intelligent travel planning assistant that creates personalized travel itineraries.
    Your task is to create a detailed day-by-day travel plan based on the provided flight, hotel, and points of interest data.
    
    Guidelines:
    1. Create a practical, coherent, and well-structured itinerary that respects the user's budget and preferences
    2. Distribute points of interest across days in a logical way, considering location and opening times
    3. Include specific flight and hotel recommendations from the provided options
    4. Add practical details like transportation between attractions
    5. Make the itinerary realistic in terms of timing and distances
    6. Include estimated costs for activities when possible
    7. Format the output in clear, well-organized markdown
    8. Make sure the total cost (flight + hotel + activities) stays within the user's budget
    
    Your response should include:
    - A brief introduction summarizing the trip
    - A suggested flight and hotel with prices
    - A day-by-day breakdown of activities (morning, afternoon, evening)
    - An estimated total cost breakdown
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
    
    async def generate_itinerary(self, 
                               travel_request: TravelRequest,
                               amadeus_service: AmadeusService,
                               google_places_service: GooglePlacesService,
                               cache_service) -> Itinerary:
        """
        Generate a complete travel itinerary using the LLM.
        This is an async wrapper around the create_itinerary method.
        """
        # Get flight options
        flights = amadeus_service.get_flight_offers(
            travel_request.origin,
            travel_request.destination,
            travel_request.depart_date,
            travel_request.return_date
        )
        
        if not flights:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No flights found from {travel_request.origin} to {travel_request.destination}"
            )
        
        # Get hotel options using the correct method
        hotels_data = amadeus_service.search_hotels_by_city(travel_request.destination)
        if not hotels_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No hotels found in {travel_request.destination}"
            )
        
        # Convert hotel data to HotelOption objects
        hotels = []
        for hotel in hotels_data:
            hotels.append(HotelOption(
                name=hotel.get("name", "Unknown Hotel"),
                price_per_night=float(hotel.get("price", {}).get("total", 0)),
                stars=float(hotel.get("rating", 3)),
                address=hotel.get("address", {}).get("lines", [""])[0],
                amenities=hotel.get("amenities", []),
                city=travel_request.destination
            ))
        
        # Get points of interest
        pois = google_places_service.get_points_of_interest(
            travel_request.destination,
            travel_request.preferences
        )
        
        # Generate the itinerary
        return self.create_itinerary(travel_request, flights, hotels, pois)
    
    def create_itinerary(self, 
                         travel_request: TravelRequest,
                         flights: List[FlightOption],
                         hotels: List[HotelOption],
                         pois: List[PointOfInterest]) -> Itinerary:
        """
        Generate a complete travel itinerary using the LLM.
        """
        # Prepare the context for the LLM
        context = self._prepare_context(travel_request, flights, hotels, pois)
        
        # Generate the itinerary text using the LLM
        itinerary_text = self._generate_itinerary_text(travel_request, context)
        
        # Parse the generated text into structured data
        itinerary = self._parse_itinerary(travel_request, itinerary_text, flights, hotels, pois)
        
        return itinerary
    
    def _prepare_context(self, 
                        travel_request: TravelRequest,
                        flights: List[FlightOption],
                        hotels: List[HotelOption],
                        pois: List[PointOfInterest]) -> Dict[str, Any]:
        """
        Prepare a structured context dictionary for the LLM prompt.
        """
        # Clean and prepare the data for serialization
        flight_data = []
        for f in flights:
            flight_data.append({
                "airline": f.airline,
                "price": f.price,
                "departure_time": f.departure_time if hasattr(f, 'departure_time') else None,
                "arrival_time": f.arrival_time if hasattr(f, 'arrival_time') else None,
                "flight_number": f.flight_number if hasattr(f, 'flight_number') else None
            })
        
        hotel_data = []
        for h in hotels:
            hotel_data.append({
                "name": h.name,
                "price_per_night": h.price_per_night,
                "stars": h.stars,
                "address": h.address if hasattr(h, 'address') else None,
                "amenities": h.amenities if hasattr(h, 'amenities') else None
            })
        
        poi_data = []
        for p in pois:
            poi_data.append({
                "name": p.name,
                "category": p.category,
                "rating": p.rating,
                "address": p.address,
                "description": p.description if hasattr(p, 'description') else None,
                "price_level": p.price_level if hasattr(p, 'price_level') else None
            })
        
        # Create the context dictionary
        context = {
            "trip_details": {
                "origin": travel_request.origin,
                "destination": travel_request.destination,
                "duration_days": travel_request.duration,
                "start_date": travel_request.depart_date.isoformat(),
                "end_date": travel_request.return_date.isoformat(),
                "budget": travel_request.budget,
                "preferences": travel_request.preferences
            },
            "flights": flight_data,
            "hotels": hotel_data,
            "points_of_interest": poi_data
        }
        
        return context
    
    def _generate_itinerary_text(self, travel_request: TravelRequest, context: Dict[str, Any]) -> str:
        """
        Generate itinerary text using the OpenAI API.
        """
        try:
            # Create a user message with the planning request and context
            trip_desc = (f"Please plan a {travel_request.duration}-day trip from {travel_request.origin} "
                        f"to {travel_request.destination} with a budget of SGD {travel_request.budget}.")
            
            preferences = "no specific preferences"
            if travel_request.preferences:
                preferences = ", ".join(travel_request.preferences)
            
            user_message = f"{trip_desc}\n\nThe traveler has indicated the following preferences: {preferences}.\n\n"
            user_message += f"Data:\n{json.dumps(context, indent=2, default=str)}"
            
            # Call the OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ]
            )
            
            # Extract and return the generated text
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"Error generating itinerary with LLM: {str(e)}")
            # Provide a fallback simple itinerary
            return self._generate_fallback_itinerary(travel_request)
    
    def _generate_fallback_itinerary(self, travel_request: TravelRequest) -> str:
        """Generate a simple fallback itinerary if the LLM call fails."""
        duration = travel_request.duration
        destination = travel_request.destination
        
        fallback = f"# Trip to {destination}\n\n"
        fallback += f"## Overview\n"
        fallback += f"A {duration}-day trip to {destination} from {travel_request.origin}.\n\n"
        
        fallback += f"## Suggested Flight\n"
        fallback += f"Economy class flight from {travel_request.origin} to {destination}.\n\n"
        
        fallback += f"## Suggested Accommodation\n"
        fallback += f"Standard hotel in {destination} city center.\n\n"
        
        fallback += f"## Day-by-Day Itinerary\n"
        
        # Generate a simple day-by-day itinerary
        for day in range(1, duration + 1):
            fallback += f"### Day {day}\n"
            fallback += f"- Morning: Breakfast at hotel, explore local area\n"
            fallback += f"- Afternoon: Visit main tourist attractions\n"
            fallback += f"- Evening: Dinner at local restaurant\n\n"
        
        fallback += f"## Estimated Budget\n"
        fallback += f"Total estimated cost: SGD {travel_request.budget * 0.9:.2f}\n"
        
        return fallback
    
    def _parse_itinerary(self, 
                        travel_request: TravelRequest, 
                        itinerary_text: str,
                        flights: List[FlightOption],
                        hotels: List[HotelOption],
                        pois: List[PointOfInterest]) -> Itinerary:
        """
        Parse the generated itinerary text into a structured Itinerary object.
        This is a simplified parser that extracts basic information.
        """
        # First identify the selected flight and hotel, if mentioned
        selected_flight = None
        selected_hotel = None
        
        # Simple heuristic to identify the flight (first one if multiple available)
        if flights:
            selected_flight = flights[0]
        
        # Simple heuristic to identify the hotel (first one if multiple available)
        if hotels:
            selected_hotel = hotels[0]
        
        # Create a day-by-day plan from the markdown text
        daily_plan = []
        days = travel_request.duration
        
        # Simple heuristic: split by days and extract content
        # In a real system, this would use more sophisticated parsing or LLM extraction
        for day in range(1, days + 1):
            # Look for day headers in the markdown
            day_markers = [
                f"### Day {day}",
                f"## Day {day}",
                f"Day {day}:",
                f"Day {day} -"
            ]
            
            day_content = ""
            for marker in day_markers:
                if marker in itinerary_text:
                    parts = itinerary_text.split(marker, 1)
                    if len(parts) > 1:
                        next_day_idx = float('inf')
                        for next_day in range(day + 1, days + 1):
                            for next_marker in day_markers:
                                next_marker = next_marker.replace(str(day), str(next_day))
                                if next_marker in parts[1]:
                                    marker_idx = parts[1].find(next_marker)
                                    if marker_idx < next_day_idx:
                                        next_day_idx = marker_idx
                        
                        if next_day_idx < float('inf'):
                            day_content = parts[1][:next_day_idx]
                        else:
                            day_content = parts[1]
                        break
            
            # If we found content for this day
            if day_content:
                # Extract morning, afternoon, evening activities if possible
                morning = afternoon = evening = None
                
                if "Morning:" in day_content:
                    morning_parts = day_content.split("Morning:", 1)
                    morning = morning_parts[1].split("\n", 1)[0].strip()
                
                if "Afternoon:" in day_content:
                    afternoon_parts = day_content.split("Afternoon:", 1)
                    afternoon = afternoon_parts[1].split("\n", 1)[0].strip()
                
                if "Evening:" in day_content:
                    evening_parts = day_content.split("Evening:", 1)
                    evening = evening_parts[1].split("\n", 1)[0].strip()
                
                # Calculate the date for this day
                day_date = travel_request.depart_date
                if day > 1:
                    from datetime import timedelta
                    day_date = travel_request.depart_date + timedelta(days=day-1)
                
                daily_plan.append(ItineraryDayActivity(
                    day=day,
                    date=day_date,
                    description=day_content.strip(),
                    morning=morning,
                    afternoon=afternoon,
                    evening=evening,
                    accommodation=selected_hotel.name if selected_hotel else None
                ))
        
        # Extract or estimate the total cost
        total_cost = travel_request.budget * 0.9  # Default to 90% of budget
        
        if "Total cost:" in itinerary_text or "Total Cost:" in itinerary_text:
            cost_text = itinerary_text.split("Total cost:" if "Total cost:" in itinerary_text else "Total Cost:", 1)[1]
            import re
            cost_match = re.search(r'SGD\s*([\d,]+(\.\d+)?)', cost_text)
            if cost_match:
                try:
                    total_cost = float(cost_match.group(1).replace(',', ''))
                except ValueError:
                    pass
        
        # Extract a summary from the beginning of the itinerary
        summary = itinerary_text.split("\n\n", 1)[0] if "\n\n" in itinerary_text else itinerary_text[:200]
        
        # Create and return the Itinerary object
        return Itinerary(
            request_id=str(uuid.uuid4()),
            travel_request=travel_request,
            selected_flight=selected_flight,
            selected_hotel=selected_hotel,
            points_of_interest=pois,
            daily_plan=daily_plan,
            summary=summary,
            total_cost=total_cost
        )