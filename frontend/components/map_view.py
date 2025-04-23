import logging
from typing import List, Dict, Any, Optional
import requests
import json
import urllib.parse

from config import settings
from models.travel import Itinerary, PointOfInterest

logger = logging.getLogger(__name__)

class MapService:
    """
    Service for generating maps and location data for itineraries.
    Uses Google Maps Static API to generate map images with POIs.
    """
    
    def __init__(self):
        self.api_key = settings.GOOGLE_MAPS_API_KEY
        self.static_maps_url = "https://maps.googleapis.com/maps/api/staticmap"
    
    def generate_itinerary_map(self, itinerary: Itinerary) -> str:
        """
        Generate a static map URL for the itinerary with all points of interest marked.
        
        Args:
            itinerary: The complete itinerary with points of interest
            
        Returns:
            A URL to a static map image showing all POIs
        """
        try:
            # Get the destination city for centering the map
            destination = itinerary.travel_request.destination
            
            # Start building the map URL
            params = {
                "center": destination,
                "zoom": 13,  # City level zoom
                "size": "600x400",
                "maptype": "roadmap",
                "key": self.api_key
            }
            
            # Add POI markers
            markers = []
            
            # Different colors for different days or categories
            colors = ["red", "blue", "green", "purple", "orange", "yellow", "gray"]
            
            # Group POIs by category
            pois_by_category = {}
            for poi in itinerary.points_of_interest:
                category = poi.category
                if category not in pois_by_category:
                    pois_by_category[category] = []
                pois_by_category[category].append(poi)
            
            # Add markers by category with different colors
            for i, (category, pois) in enumerate(pois_by_category.items()):
                color = colors[i % len(colors)]
                label_prefix = chr(65)  # Start with 'A'
                
                category_markers = []
                for j, poi in enumerate(pois):
                    label = f"{label_prefix}{j+1}"
                    location = self._get_location_string(poi)
                    if location:
                        category_markers.append(f"label:{label}|{location}")
                
                if category_markers:
                    markers.append(f"color:{color}|" + "|".join(category_markers))
            
            # Add hotel marker (special icon)
            if itinerary.selected_hotel:
                hotel_location = f"{itinerary.selected_hotel.name}, {destination}"
                markers.append(f"icon:https://maps.google.com/mapfiles/kml/paddle/H.png|{hotel_location}")
            
            # Add markers to URL
            map_url = f"{self.static_maps_url}?{urllib.parse.urlencode(params)}"
            for marker_group in markers:
                map_url += f"&markers={urllib.parse.quote(marker_group)}"
            
            return map_url
            
        except Exception as e:
            logger.error(f"Error generating map: {str(e)}")
            # Return a basic map of the destination as fallback
            fallback_url = f"{self.static_maps_url}?center={urllib.parse.quote(destination)}&zoom=12&size=600x400&key={self.api_key}"
            return fallback_url
    
    def generate_day_map(self, itinerary: Itinerary, day: int) -> str:
        """
        Generate a static map URL for a specific day of the itinerary.
        
        Args:
            itinerary: The complete itinerary
            day: The day number (1-based) to create a map for
            
        Returns:
            A URL to a static map image for the specified day
        """
        try:
            # Get the destination city for fallback
            destination = itinerary.travel_request.destination
            
            # Find day's activities
            day_activity = None
            for activity in itinerary.daily_plan:
                if activity.day == day:
                    day_activity = activity
                    break
            
            if not day_activity:
                # Return map of destination if day not found
                return f"{self.static_maps_url}?center={urllib.parse.quote(destination)}&zoom=12&size=600x400&key={self.api_key}"
            
            # Start building the map URL
            params = {
                "center": destination,
                "zoom": 14,  # Slightly closer zoom for daily activities
                "size": "600x400",
                "maptype": "roadmap",
                "key": self.api_key
            }
            
            # Try to extract POI names from the day's activities
            poi_names = []
            
            for field in [day_activity.morning, day_activity.afternoon, day_activity.evening]:
                if not field:
                    continue
                
                # Look for POIs in this activity
                for poi in itinerary.points_of_interest:
                    if poi.name in field:
                        poi_names.append(poi.name)
            
            # Get relevant POIs for this day
            day_pois = []
            for poi in itinerary.points_of_interest:
                if poi.name in poi_names:
                    day_pois.append(poi)
            
            # Add POI markers
            markers = []
            
            # Different markers for morning, afternoon, evening
            time_periods = ["morning", "afternoon", "evening"]
            colors = ["red", "blue", "green"]
            
            for i, period in enumerate(time_periods):
                period_text = getattr(day_activity, period)
                if not period_text:
                    continue
                
                period_pois = []
                for poi in day_pois:
                    if poi.name in period_text:
                        period_pois.append(poi)
                
                if period_pois:
                    color = colors[i]
                    period_markers = []
                    
                    for j, poi in enumerate(period_pois):
                        label = chr(65 + j)  # A, B, C, ...
                        location = self._get_location_string(poi)
                        if location:
                            period_markers.append(f"label:{label}|{location}")
                    
                    if period_markers:
                        markers.append(f"color:{color}|" + "|".join(period_markers))
            
            # Add hotel marker
            if itinerary.selected_hotel:
                hotel_location = f"{itinerary.selected_hotel.name}, {destination}"
                markers.append(f"icon:https://maps.google.com/mapfiles/kml/paddle/H.png|{hotel_location}")
            
            # Add markers to URL
            map_url = f"{self.static_maps_url}?{urllib.parse.urlencode(params)}"
            for marker_group in markers:
                map_url += f"&markers={urllib.parse.quote(marker_group)}"
            
            return map_url
            
        except Exception as e:
            logger.error(f"Error generating day map: {str(e)}")
            return f"{self.static_maps_url}?center={urllib.parse.quote(destination)}&zoom=12&size=600x400&key={self.api_key}"
    
    def _get_location_string(self, poi: PointOfInterest) -> Optional[str]:
        """Extract location string from POI for map marker."""
        # First try to use coordinates if available
        if hasattr(poi, 'latitude') and hasattr(poi, 'longitude') and poi.latitude and poi.longitude:
            return f"{poi.latitude},{poi.longitude}"
        
        # Otherwise use name and address
        if poi.address:
            return f"{poi.name}, {poi.address}"
        
        # Fallback to just the name
        return poi.name
    
    def enrich_pois_with_coordinates(self, pois: List[PointOfInterest], city: str) -> List[PointOfInterest]:
        """
        Add latitude and longitude to POIs using Google's Geocoding API.
        This is useful for creating more accurate maps.
        """
        geocoding_url = "https://maps.googleapis.com/maps/api/geocode/json"
        
        for poi in pois:
            if hasattr(poi, 'latitude') and poi.latitude and hasattr(poi, 'longitude') and poi.longitude:
                continue  # Skip if already has coordinates
                
            try:
                # Build a search query using POI name and address
                query = f"{poi.name}, {poi.address}" if poi.address else f"{poi.name}, {city}"
                
                response = requests.get(
                    geocoding_url,
                    params={"address": query, "key": self.api_key},
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("results") and len(data["results"]) > 0:
                        location = data["results"][0]["geometry"]["location"]
                        poi.latitude = location["lat"]
                        poi.longitude = location["lng"]
            
            except Exception as e:
                logger.warning(f"Error geocoding POI {poi.name}: {str(e)}")
                continue
                
        return pois