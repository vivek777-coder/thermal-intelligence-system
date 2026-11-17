import argparse
import logging
import os
import sys

from dotenv import load_dotenv
from geopy.distance import geodesic

# Ensure we can import from adapters and db
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adapters.osm import OSMClient, OSMUnavailableError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ingest_osm")


def calculate_local_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two points using geopy (local fallback)."""
    return geodesic((lat1, lon1), (lat2, lon2)).meters


def run_ingestion_and_demo(bbox: str):
    """
    Run OSM ingestion for the bbox and demonstrate nearest-facility query.
    """
    client = OSMClient()
    logger.info(f"Starting OSM feature ingestion for bbox: {bbox}")

    try:
        # 1. Fetch real features from Overpass
        features = client.fetch_features(bbox=bbox)
        logger.info(f"Successfully fetched {len(features)} infrastructure features from Overpass.")

        if not features:
            logger.warning("No industrial or critical infrastructure features found in this bbox.")
            return

        # Let's categorize what we found
        categories = {}
        for f in features:
            ftype = f["feature_type"]
            categories[ftype] = categories.get(ftype, 0) + 1

        logger.info("Found features by type:")
        for ftype, count in categories.items():
            logger.info(f"  - {ftype}: {count}")

        # In production, we would instantiate OSMFeature models and save to DB:
        # session.add_all([OSMFeature(**f) for f in features])
        # session.commit()

        # 2. Demonstrate spatial query fallback (since PostGIS is unavailable)
        # We'll simulate a thermal anomaly in the center of the bounding box.
        try:
            w, s, e, n = map(float, bbox.split(","))
            mock_lat = (s + n) / 2
            mock_lon = (w + e) / 2
        except ValueError:
            mock_lat, mock_lon = 0, 0

        logger.info("\n--- Demonstrating Nearest-Facility Query ---")
        logger.info(f"Simulated Thermal Anomaly at ({mock_lat}, {mock_lon})")

        # Calculate distances locally
        features_with_distance = []
        for feat in features:
            dist = calculate_local_distance(mock_lat, mock_lon, feat["latitude"], feat["longitude"])
            # Only consider features within 50km for this demo
            if dist <= 50000:
                features_with_distance.append((feat, dist))

        # Sort by proximity
        features_with_distance.sort(key=lambda x: x[1])

        if not features_with_distance:
            logger.info("No facilities found within 50km of the simulated anomaly.")
        else:
            logger.info("Top 5 nearest facilities:")
            for feat, dist in features_with_distance[:5]:
                name = feat["name"] or "<Unnamed>"
                logger.info(f"  [{dist:,.1f}m] {feat['feature_type'].upper()}: {name}")

                # Demonstrate Nominatim Reverse Geocoding for the closest facility
                if feat == features_with_distance[0][0]:
                    logger.info(f"\nReverse geocoding the nearest facility ({name})...")
                    address_data = client.reverse_geocode(feat["latitude"], feat["longitude"])
                    if address_data:
                        logger.info(f"Address: {address_data['address']}")
                    else:
                        logger.info("Address could not be resolved.")

    except OSMUnavailableError as e:
        logger.error(f"Failed to access OSM API. Details: {e}")
        sys.exit(1)
    except Exception:
        logger.exception("Unexpected error during ingestion:")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="OSM Feature Ingestion CLI")
    parser.add_argument("--bbox", type=str, help="Bounding box (west,south,east,north)")

    args = parser.parse_args()

    # Load defaults from env if not provided
    load_dotenv()
    bbox = args.bbox or os.getenv("DEFAULT_REGION_BBOX")

    if not bbox:
        # Defaulting to Jamnagar Refinery region as discussed in the implementation plan
        bbox = "69.8,22.3,70.0,22.5"
        logger.info(f"No bbox provided. Using default Jamnagar, India bounding box: {bbox}")

    run_ingestion_and_demo(bbox=bbox)


if __name__ == "__main__":
    main()
