"""
NASA FIRMS API Client

Handles fetching near-real-time and historical thermal anomaly data.
"""

import csv
import logging
from io import StringIO
from typing import Any, Dict, List, Optional

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class FIRMSUnavailableError(Exception):
    """Raised when the FIRMS API is unreachable after retries."""

    pass


class FIRMSClient:
    """Client for the NASA FIRMS Area API."""

    BASE_URL = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"

    def __init__(self, map_key: str, default_source: str = "VIIRS_SNPP_NRT"):
        """
        Initialize the FIRMS API client.
        
        Args:
            map_key: NASA FIRMS Map Key (required).
            default_source: Satellite source (e.g., VIIRS_SNPP_NRT, MODIS_NRT).
        """
        if not map_key or map_key.startswith("<"):
            raise ValueError("A valid FIRMS_MAP_KEY is required to initialize the client.")
        self.map_key = map_key
        self.default_source = default_source

        # We use a custom timeout because NASA servers can occasionally be slow
        self.timeout = httpx.Timeout(30.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True,
    )
    async def _fetch_csv(self, url: str) -> str:
        """Fetch CSV data with exponential backoff on transient network errors."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.text
            except (httpx.RequestError, httpx.TimeoutException) as e:
                logger.warning(f"Network error accessing FIRMS API: {e}")
                raise
            except httpx.HTTPStatusError as e:
                # 4xx or 5xx error
                logger.error(f"FIRMS API HTTP {e.response.status_code}: {e.response.text}")
                # Don't retry on 400 Bad Request, 401 Unauthorized, etc.
                if 400 <= e.response.status_code < 500:
                    raise FIRMSUnavailableError(f"FIRMS API client error: {e.response.status_code}")
                raise

    def _parse_csv_to_dicts(self, csv_text: str, source: str) -> List[Dict[str, Any]]:
        """Parse the NASA FIRMS CSV response into a list of dictionaries for ingestion."""
        # The API can return an error message instead of a CSV if the key is invalid
        if not csv_text.strip():
            return []

        if csv_text.startswith("Error") or "Invalid mapkey" in csv_text:
            raise FIRMSUnavailableError(f"FIRMS API returned error: {csv_text.strip()}")

        reader = csv.DictReader(StringIO(csv_text))
        observations = []

        for row in reader:
            # Map FIRMS CSV row to our ThermalObservation schema fields
            try:
                obs = {
                    "source": "firms",
                    "satellite": source,
                    "latitude": float(row.get("latitude", 0)),
                    "longitude": float(row.get("longitude", 0)),
                    "brightness": float(row.get("brightness", 0)) if row.get("brightness") else None,
                    "bright_ti4": float(row.get("bright_ti4", 0)) if row.get("bright_ti4") else None,
                    "bright_ti5": float(row.get("bright_ti5", 0)) if row.get("bright_ti5") else None,
                    "frp": float(row.get("frp", 0)) if row.get("frp") else None,
                    "confidence": row.get("confidence"),
                    "acq_date": row.get("acq_date"),
                    "acq_time": row.get("acq_time"),
                    "daynight": row.get("daynight"),
                    "version": row.get("version"),
                    "raw_data": dict(row),
                }

                # Convert confidence string to a percentage for the database schema constraint
                conf_val = row.get("confidence", "").lower()
                if conf_val in ("low", "nominal", "high"):
                    # nominal -> 50, high -> 100, low -> 10. (VIIRS format)
                    mapping = {"low": 10, "nominal": 50, "high": 99}
                    obs["confidence_pct"] = mapping.get(conf_val, 0)
                elif conf_val.isdigit():
                    # MODIS format (0-100)
                    pct = int(conf_val)
                    # Project rule: confidence_pct must be <= 99
                    obs["confidence_pct"] = min(pct, 99)
                else:
                    obs["confidence_pct"] = None

                observations.append(obs)
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse FIRMS CSV row: {row}. Error: {e}")
                continue

        return observations

    async def fetch_recent_hotspots(
        self,
        bbox: str,
        days: int = 1,
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch near-real-time hotspots for the given area and day range.
        
        Args:
            bbox: Bounding box string (west,south,east,north).
            days: Number of days (1-5).
            source: Satellite source (defaults to client default).
        """
        if days < 1 or days > 5:
            raise ValueError("FIRMS API only supports a DAY_RANGE between 1 and 5.")

        src = source or self.default_source
        url = f"{self.BASE_URL}/{self.map_key}/{src}/{bbox}/{days}"

        try:
            csv_text = await self._fetch_csv(url)
            return self._parse_csv_to_dicts(csv_text, src)
        except Exception as e:
            raise FIRMSUnavailableError(f"Failed to fetch recent hotspots: {e}") from e

    async def fetch_historical_hotspots(
        self,
        bbox: str,
        date: str,
        days: int = 1,
        source: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical hotspots for a specific date range (backfill).
        
        Args:
            bbox: Bounding box string (west,south,east,north).
            date: Start date (YYYY-MM-DD).
            days: Number of days to fetch starting from `date` (1-5).
            source: Satellite source (defaults to client default).
        """
        if days < 1 or days > 5:
            raise ValueError("FIRMS API only supports a DAY_RANGE between 1 and 5.")

        src = source or self.default_source
        url = f"{self.BASE_URL}/{self.map_key}/{src}/{bbox}/{days}/{date}"

        try:
            csv_text = await self._fetch_csv(url)
            return self._parse_csv_to_dicts(csv_text, src)
        except Exception as e:
            raise FIRMSUnavailableError(f"Failed to fetch historical hotspots: {e}") from e
