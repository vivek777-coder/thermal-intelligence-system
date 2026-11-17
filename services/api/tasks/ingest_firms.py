import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv

# Ensure we can import from db and adapters
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adapters.firms import FIRMSClient, FIRMSUnavailableError
from db.models import ThermalObservation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ingest_firms")


def get_last_successful_fetch() -> str:
    """Read the last successful fetch timestamp from a local cache file."""
    cache_file = ".firms_last_fetch"
    if os.path.exists(cache_file):
        with open(cache_file, "r") as f:
            return f.read().strip()
    return "Never"


def set_last_successful_fetch():
    """Update the local cache file with the current UTC timestamp."""
    cache_file = ".firms_last_fetch"
    with open(cache_file, "w") as f:
        f.write(datetime.now(timezone.utc).isoformat())


async def run_ingestion(bbox: str, days: int = 1, is_backfill: bool = False, backfill_date: str = None):
    """
    Run the NASA FIRMS ingestion job.
    """
    load_dotenv()
    map_key = os.getenv("FIRMS_MAP_KEY")
    if not map_key or map_key.startswith("<"):
        logger.error("FIRMS_MAP_KEY is missing from environment. Cannot proceed.")
        sys.exit(1)

    client = FIRMSClient(map_key=map_key)
    logger.info(f"Starting FIRMS ingestion for bbox: {bbox}")

    try:
        if is_backfill and backfill_date:
            logger.info(f"Running historical backfill from {backfill_date} for {days} days")
            observations = await client.fetch_historical_hotspots(bbox=bbox, date=backfill_date, days=days)
        else:
            logger.info(f"Running near-real-time fetch for the last {days} days")
            observations = await client.fetch_recent_hotspots(bbox=bbox, days=days)

        logger.info(f"Successfully fetched {len(observations)} hotspot records from FIRMS.")

        # Instantiate SQLAlchemy models
        models = []
        for obs_dict in observations:
            # For geometries we construct the WKT explicitly for PostGIS
            lon = obs_dict["longitude"]
            lat = obs_dict["latitude"]
            geom_wkt = f"SRID=4326;POINT({lon} {lat})"

            # Remove keys that aren't in the model before passing as kwargs
            model_kwargs = obs_dict.copy()

            # Map observed_at from acq_date and acq_time
            # FIRMS format: acq_date "YYYY-MM-DD", acq_time "HHMM"
            try:
                date_str = model_kwargs.pop("acq_date")
                time_str = model_kwargs.pop("acq_time")
                dt_str = f"{date_str} {time_str[:2]}:{time_str[2:]}:00"
                observed_at = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            except Exception as e:
                logger.warning(f"Could not parse acq_date/acq_time: {e}")
                observed_at = datetime.now(timezone.utc)

            model = ThermalObservation(
                location=geom_wkt,
                observed_at=observed_at,
                **model_kwargs
            )
            models.append(model)

        if not models:
            logger.info("No hotspots found in this region for the specified time period.")
        else:
            logger.info("Printing first 3 parsed records (Dry Run mode):")
            for m in models[:3]:
                print(
                    f"ThermalObservation(lat={m.latitude}, lon={m.longitude}, "
                    f"frp={m.frp}, confidence={m.confidence_pct}%, acq={m.observed_at})"
                )

            # TODO: In production, insert models into DB via SQLAlchemy session
            # Since Docker/PostGIS is unavailable locally, we only print the models here.
            # session.add_all(models)
            # session.commit()

        set_last_successful_fetch()

    except FIRMSUnavailableError as e:
        last_fetch = get_last_successful_fetch()
        logger.error(f"FIRMS API unavailable. Last successful fetch at {last_fetch}.")
        logger.error(f"Details: {e}")
        # We never silently reuse stale data as live. We explicitly log the failure.
        sys.exit(1)
    except Exception:
        logger.exception("Unexpected error during ingestion:")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="NASA FIRMS Data Ingestion CLI")
    parser.add_argument("--bbox", type=str, help="Bounding box (west,south,east,north)")
    parser.add_argument("--days", type=int, default=1, help="Number of days to fetch (1-5)")
    parser.add_argument("--backfill", action="store_true", help="Run in historical backfill mode")
    parser.add_argument("--date", type=str, help="Start date for backfill (YYYY-MM-DD)")

    args = parser.parse_args()

    # Load defaults from env if not provided
    load_dotenv()
    bbox = args.bbox or os.getenv("DEFAULT_REGION_BBOX")
    if not bbox:
        logger.error("Bounding box must be provided via --bbox or DEFAULT_REGION_BBOX in .env")
        sys.exit(1)

    if args.backfill and not args.date:
        logger.error("--date is required when running in --backfill mode.")
        sys.exit(1)

    asyncio.run(run_ingestion(bbox=bbox, days=args.days, is_backfill=args.backfill, backfill_date=args.date))


if __name__ == "__main__":
    main()
