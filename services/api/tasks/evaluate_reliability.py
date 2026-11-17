import argparse
import logging
import os
import sys
from datetime import datetime, timezone

# Ensure we can import from adapters and services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adapters.openmeteo import OpenMeteoClient
from services.reliability import ObservationReliabilityEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("evaluate_reliability")


def evaluate_date(client: OpenMeteoClient, lat: float, lon: float, dt: datetime, has_hotspot: bool, description: str):
    logger.info(f"\n--- Evaluating Scenario: {description} ---")
    logger.info(f"Target: Lat {lat}, Lon {lon} | Time: {dt.strftime('%Y-%m-%d %H:%M UTC')}")
    logger.info(f"FIRMS Hotspot Detected: {has_hotspot}")

    try:
        # Fetch data
        weather = client.fetch_weather(lat, lon, dt)
        aq = client.fetch_air_quality(lat, lon, dt)

        logger.info("\nFetched Environmental Data:")
        logger.info(f"  Cloud Cover: {weather.get('cloud_cover_pct')}%")
        logger.info(f"  Rainfall:    {weather.get('precipitation_mm')} mm/hr")
        logger.info(f"  Visibility:  {weather.get('visibility_m')} m")
        logger.info(f"  AOD (Smog):  {aq.get('aod', 'N/A')}")

        # Evaluate reliability
        result = ObservationReliabilityEngine.evaluate(
            has_thermal_hotspot=has_hotspot,
            weather_data=weather,
            aq_data=aq
        )

        logger.info("\n--- Reliability Engine Output ---")
        logger.info(f"Observation Quality: {result['observationQuality']}")
        logger.info(f"Reason Codes:        {', '.join(result['reasonCodes'])}")
        logger.info(f"Evaluation Message:  {result['evaluation_message']}")

    except Exception as e:
        logger.error(f"Evaluation failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate Observation Reliability Engine")
    args = parser.parse_args()

    client = OpenMeteoClient()

    # We will use Jamnagar, India (same as OSM test)
    lat, lon = 22.4, 69.9

    # 1. Clear Winter Day (Likely HIGH reliability)
    # Using a date in December where skies are usually clear in Gujarat
    clear_dt = datetime(2023, 12, 15, 12, 0, 0, tzinfo=timezone.utc)

    # 2. Heavy Monsoon Day (Likely LOW reliability due to clouds/rain)
    # Using a date in July during Indian monsoon
    rainy_dt = datetime(2023, 7, 10, 12, 0, 0, tzinfo=timezone.utc)

    # Scenario A: Clear day with a hotspot
    evaluate_date(client, lat, lon, clear_dt, has_hotspot=True, description="Clear Day with Hotspot")

    # Scenario B: Rainy day with a hotspot
    evaluate_date(client, lat, lon, rainy_dt, has_hotspot=True, description="Rainy/Cloudy Day with Hotspot")

    # Scenario C: Rainy day WITHOUT a hotspot (Triggering the Critical Rule)
    evaluate_date(client, lat, lon, rainy_dt, has_hotspot=False, description="Rainy/Cloudy Day WITHOUT Hotspot (Critical Rule Check)")


if __name__ == "__main__":
    main()
