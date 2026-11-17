"""
Spatial Services

Handles PostGIS spatial queries (nearest neighbor, distance, overlaps)
between thermal events and infrastructure.
"""

import logging
from typing import List, Tuple

from geoalchemy2.functions import ST_DistanceSphere
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from db.models import OSMFeature

logger = logging.getLogger(__name__)


def find_nearest_infrastructure(
    session: Session,
    lat: float,
    lon: float,
    radius_meters: int = 5000,
    limit: int = 10
) -> List[Tuple[OSMFeature, float]]:
    """
    Find infrastructure (OSM features) near a specific latitude/longitude.
    
    This function performs a PostGIS ST_DWithin query to quickly filter features
    within a bounding box, then calculates the exact ST_DistanceSphere, sorting
    the results by proximity.
    
    Args:
        session: SQLAlchemy DB session.
        lat: Latitude of the point of interest (e.g., thermal anomaly).
        lon: Longitude of the point of interest.
        radius_meters: Search radius in meters (default 5000m / 5km).
        limit: Maximum number of results to return.
        
    Returns:
        A list of tuples containing (OSMFeature, distance_in_meters).
    """
    # Create the PostGIS point geometry
    # Note: ST_MakePoint takes (lon, lat)
    target_point = func.ST_SetSRID(func.ST_MakePoint(lon, lat), 4326)

    # Calculate distance in meters using ST_DistanceSphere
    distance_col = ST_DistanceSphere(OSMFeature.geometry, target_point).label("distance_m")

    try:
        # Note: ST_DWithin against geography/geometry in 4326 might behave differently
        # depending on PostGIS version. We cast to geography to ensure meter-based DWithin.
        query = (
            session.query(OSMFeature, distance_col)
            .filter(
                func.ST_DWithin(
                    func.cast(OSMFeature.geometry, getattr(func, "geography")),
                    func.cast(target_point, getattr(func, "geography")),
                    radius_meters
                )
            )
            .order_by(distance_col)
            .limit(limit)
        )

        results = query.all()
        return results

    except Exception as e:
        logger.error(f"Failed to query nearest infrastructure: {e}")
        raise
