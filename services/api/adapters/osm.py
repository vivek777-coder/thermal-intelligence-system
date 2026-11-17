"""
OpenStreetMap (OSM) API Client

Handles fetching facilities and critical infrastructure via Overpass API,
and reverse geocoding via Nominatim.
"""

import logging
from typing import Any, Dict, List, Optional

import httpx
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class OSMUnavailableError(Exception):
    """Raised when OSM APIs are unreachable after retries."""
    pass


class OSMClient:
    """Client for OpenStreetMap Overpass API and Nominatim."""

    def __init__(self, user_agent: str = "thermal-intel-platform/1.0"):
        """
        Initialize the OSM client.
        
        Args:
            user_agent: A custom User-Agent string required by Nominatim usage policy.
        """
        self.user_agent = user_agent
        # Initialize Nominatim geocoder
        # Note: Nominatim usage policy restricts to 1 request per second.
        # Geopy handles basic rate limiting if configured with RateLimiter,
        # but for simple usage, we just use the default geolocator.
        self.geolocator = Nominatim(user_agent=self.user_agent)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True,
    )
    def fetch_features(self, bbox: str) -> List[Dict[str, Any]]:
        """
        Fetch industrial facilities, critical infrastructure, and settlements
        for a given bounding box using the Overpass QL via httpx.
        
        Args:
            bbox: Bounding box string as "west,south,east,north". Note: Overpass expects "south,west,north,east"
                  so we will parse and reformat it.
        """
        import httpx
        
        try:
            w, s, e, n = map(float, bbox.split(","))
        except ValueError:
            raise ValueError("Invalid bounding box format. Expected 'west,south,east,north'.")

        # Overpass expects (south, west, north, east)
        overpass_bbox = f"{s},{w},{n},{e}"

        # Overpass QL Query
        # We look for industrial landuse, works, power plants, hospitals, schools, and major settlements.
        query = f"""
        [out:json][timeout:25];
        (
          node["landuse"="industrial"]({overpass_bbox});
          way["landuse"="industrial"]({overpass_bbox});
          relation["landuse"="industrial"]({overpass_bbox});
          
          node["man_made"="works"]({overpass_bbox});
          way["man_made"="works"]({overpass_bbox});
          
          node["power"="plant"]({overpass_bbox});
          way["power"="plant"]({overpass_bbox});
          
          node["amenity"="hospital"]({overpass_bbox});
          way["amenity"="hospital"]({overpass_bbox});
          
          node["amenity"="school"]({overpass_bbox});
          way["amenity"="school"]({overpass_bbox});
          
          node["place"~"city|town|village"]({overpass_bbox});
        );
        out center;
        """
        
        try:
            logger.info(f"Querying Overpass API for bbox {overpass_bbox}...")
            # We use httpx explicitly with a user agent
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    "https://overpass-api.de/api/interpreter",
                    data={"data": query},
                    headers={"User-Agent": self.user_agent}
                )
                response.raise_for_status()
                result = response.json()
        except Exception as e:
            logger.error(f"Error querying Overpass API: {e}")
            raise OSMUnavailableError(f"Overpass API error: {e}")

        features = []
        
        for el in result.get("elements", []):
            tags = el.get("tags", {})
            el_type = el.get("type", "node")
            
            # with 'out center;', ways and relations have 'center' object
            if el_type == "node":
                lat, lon = el.get("lat"), el.get("lon")
            else:
                center = el.get("center", {})
                lat, lon = center.get("lat"), center.get("lon")
                
            if lat is None or lon is None:
                continue
                
            # Determine feature type
            feature_type = "unknown"
            if "landuse" in tags and tags["landuse"] == "industrial":
                feature_type = "industrial_zone"
            elif "man_made" in tags and tags["man_made"] == "works":
                feature_type = "factory"
            elif "power" in tags and tags["power"] == "plant":
                feature_type = "power_plant"
            elif "amenity" in tags and tags["amenity"] == "hospital":
                feature_type = "hospital"
            elif "amenity" in tags and tags["amenity"] == "school":
                feature_type = "school"
            elif "place" in tags:
                feature_type = f"settlement_{tags['place']}"

            features.append({
                "osm_id": el.get("id"),
                "osm_type": el_type,
                "feature_type": feature_type,
                "name": tags.get("name", ""),
                "latitude": float(lat),
                "longitude": float(lon),
                "tags": tags,
            })
            
        return features

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True,
    )
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Reverse geocode coordinates using Nominatim via httpx.
        """
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=jsonv2"
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    url,
                    headers={"User-Agent": self.user_agent}
                )
                response.raise_for_status()
                data = response.json()
                
            if data and "address" in data:
                # Construct a formatted address string
                addr_parts = [v for k, v in data["address"].items()]
                formatted = ", ".join(addr_parts)
                return {
                    "address": formatted,
                    "raw": data
                }
            return None
        except Exception as e:
            logger.error(f"Reverse geocoding failed: {e}")
            raise OSMUnavailableError(f"Nominatim error: {e}")
