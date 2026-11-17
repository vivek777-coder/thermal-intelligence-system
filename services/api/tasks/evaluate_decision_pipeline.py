import json
import logging
import os
import sys

# Ensure we can import from services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.decision import EmergencyDecisionEngine
from services.fusion import EvidenceFusionEngine
from services.risk import RiskAssessmentEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("evaluate_pipeline")


def run_pipeline_test(scenario_name: str, firms_data: dict, reliability_data: dict, temporal_data: dict, osm_facility: dict, distance_m: float):
    logger.info(f"\n{'='*50}")
    logger.info(f"SCENARIO: {scenario_name}")
    logger.info(f"{'='*50}")

    # 1. Evidence Fusion
    logger.info("--- 1. Evidence Fusion Engine ---")
    fusion_output = EvidenceFusionEngine.fuse(firms_data, reliability_data, temporal_data)
    logger.info(json.dumps(fusion_output, indent=2))

    # 2. Risk Assessment
    logger.info("\n--- 2. Risk Assessment Engine ---")
    risk_output = RiskAssessmentEngine.assess(fusion_output, firms_data, osm_facility, distance_m)
    logger.info(json.dumps(risk_output, indent=2))

    # 3. Emergency Decision
    logger.info("\n--- 3. Emergency Decision Engine ---")
    decision_output = EmergencyDecisionEngine.decide(fusion_output, risk_output, temporal_data)
    logger.info(json.dumps(decision_output, indent=2))

    return decision_output


def main():
    logger.info("Starting Offline Pipeline Integration Test")
    logger.info("Testing the deterministic rule engines using structured offline payloads.")

    # Base OSM Facility (e.g., Oil Refinery)
    base_osm = {
        "feature_type": "industrial_zone",
        "name": "Jamnagar Refinery"
    }

    # ---------------------------------------------------------
    # Scenario A: Massive Sudden Spike next to Refinery in Clear Weather
    # Expectation: PUBLIC_EMERGENCY_ALERT_RECOMMENDED with human approval required.
    # ---------------------------------------------------------
    run_pipeline_test(
        "A. Sudden Massive Spike (Clear Weather)",
        firms_data={"frp": 850.0, "confidence_pct": 100},
        reliability_data={"observationQuality": "HIGH", "reasonCodes": ["CLEAR_CONDITIONS"]},
        temporal_data={"classification": "abnormal spike", "overallThermalAnomaly": True},
        osm_facility=base_osm,
        distance_m=100.0  # Right on top of the facility
    )

    # ---------------------------------------------------------
    # Scenario B: Massive Sudden Spike, but LOW Confidence (e.g., poor weather)
    # Expectation: DOWNGRADE due to Low Confidence rule. No Evacuation.
    # ---------------------------------------------------------
    run_pipeline_test(
        "B. Sudden Massive Spike (Poor Weather / Low Confidence)",
        firms_data={"frp": 850.0, "confidence_pct": 100},
        reliability_data={"observationQuality": "LOW", "reasonCodes": ["HIGH_CLOUD_COVER", "HEAVY_RAIN"]},
        temporal_data={"classification": "abnormal spike", "overallThermalAnomaly": True},
        osm_facility=base_osm,
        distance_m=100.0
    )

    # ---------------------------------------------------------
    # Scenario C: Persistent Flare Stack (Normal operations)
    # Expectation: DOWNGRADE due to Persistent rule. No Public Alert.
    # ---------------------------------------------------------
    run_pipeline_test(
        "C. Persistent Flare Stack (Normal Operations)",
        firms_data={"frp": 120.0, "confidence_pct": 95},
        reliability_data={"observationQuality": "HIGH", "reasonCodes": ["CLEAR_CONDITIONS"]},
        temporal_data={"classification": "persistent", "overallThermalAnomaly": False},
        osm_facility=base_osm,
        distance_m=100.0
    )

    # ---------------------------------------------------------
    # Scenario D: Insufficient Evidence / Contradictions
    # Expectation: MONITOR.
    # ---------------------------------------------------------
    run_pipeline_test(
        "D. Cloud Cover with No Hotspot (Insufficient Evidence)",
        firms_data={}, # No hotspot
        reliability_data={"observationQuality": "LOW", "reasonCodes": ["HIGH_CLOUD_COVER"]},
        temporal_data={"classification": "normal", "overallThermalAnomaly": False},
        osm_facility=base_osm,
        distance_m=100.0
    )


if __name__ == "__main__":
    main()
