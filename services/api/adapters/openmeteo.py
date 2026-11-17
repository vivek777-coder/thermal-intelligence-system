"""
Open-Meteo API Client

Handles fetching historical and near-real-time weather and air quality data.
"""

import logging
from datetime import datetime
from typing import Any, Dict

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class OpenMeteoError(Exception):
    """Raised when Open-Meteo API is unreachable or returns an error."""
    pass


class OpenMeteoClient:
    """Client for Open-Meteo Weather and Air Quality APIs."""

    WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"
    AQ_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

    def __init__(self):
        self.timeout = httpx.Timeout(15.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True,
    )
    def fetch_weather(self, lat: float, lon: float, dt: datetime) -> Dict[str, Any]:
        """
        Fetch historical weather data for a specific location and hour.
        """
        # Open-Meteo archive API requires dates in YYYY-MM-DD
        date_str = dt.strftime("%Y-%m-%d")
        # Find the hour index (0-23)
        hour_index = dt.hour

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,cloud_cover,visibility,wind_speed_10m,wind_direction_10m",
            "timezone": "UTC"
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(self.WEATHER_URL, params=params)
                response.raise_for_status()
                data = response.json()

            hourly = data.get("hourly", {})
            if not hourly:
                return {}

            # Extract data for the specific hour
            return {
                "temperature_c": hourly.get("temperature_2m", [])[hour_index],
                "humidity_pct": hourly.get("relative_humidity_2m", [])[hour_index],
                "precipitation_mm": hourly.get("precipitation", [])[hour_index],
                "cloud_cover_pct": hourly.get("cloud_cover", [])[hour_index],
                "visibility_m": hourly.get("visibility", [])[hour_index],
                "wind_speed_kmh": hourly.get("wind_speed_10m", [])[hour_index],
                "wind_direction_deg": hourly.get("wind_direction_10m", [])[hour_index],
            }
        except IndexError:
            logger.warning(f"Weather data missing for hour {hour_index} at {date_str}.")
            return {}
        except Exception as e:
            logger.error(f"Error fetching weather from Open-Meteo: {e}")
            raise OpenMeteoError(f"Weather API error: {e}")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True,
    )
    def fetch_air_quality(self, lat: float, lon: float, dt: datetime) -> Dict[str, Any]:
        """
        Fetch historical air quality data for a specific location and hour.
        """
        date_str = dt.strftime("%Y-%m-%d")
        hour_index = dt.hour

        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "hourly": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,aerosol_optical_depth",
            "timezone": "UTC"
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(self.AQ_URL, params=params)
                response.raise_for_status()
                data = response.json()

            hourly = data.get("hourly", {})
            if not hourly:
                return {}

            return {
                "pm10": hourly.get("pm10", [])[hour_index],
                "pm2_5": hourly.get("pm2_5", [])[hour_index],
                "co": hourly.get("carbon_monoxide", [])[hour_index],
                "no2": hourly.get("nitrogen_dioxide", [])[hour_index],
                "so2": hourly.get("sulphur_dioxide", [])[hour_index],
                "aod": hourly.get("aerosol_optical_depth", [])[hour_index],
            }
        except IndexError:
            logger.warning(f"Air quality data missing for hour {hour_index} at {date_str}.")
            return {}
        except Exception as e:
            logger.error(f"Error fetching air quality from Open-Meteo: {e}")
            raise OpenMeteoError(f"Air Quality API error: {e}")
