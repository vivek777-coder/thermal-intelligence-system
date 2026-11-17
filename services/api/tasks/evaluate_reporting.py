import json
import logging
import os
import sys

# Ensure we can import from services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.reporting import PublicReportingService
from services.fusion import EvidenceFusionEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("evaluate_reporting")

def main():
    logger.info("--- Public Reporting & Fusion Engine Verification ---")
    
    # Mock thermal event
    firms_data = {
        "frp": 25.0,
        "latitude": 22.345,
        "longitude": 69.876,
        "confidence_pct": 60 # Medium confidence initially
    }
    
    weather_data = {"observationQuality": "MEDIUM"}
    temporal_data = {"classification": "sudden"}
    
    logger.info("\n1. Running Base Fusion (No Public Reports)")
    fused_base = EvidenceFusionEngine.fuse(
        firms_data=firms_data,
        reliability_data=weather_data,
        temporal_data=temporal_data
    )
    logger.info(json.dumps(fused_base, indent=2))
    
    # Mock Public Report
    public_report = {
        "location": {
            "latitude": 22.346, # 100m away (Within 1km = Highly reliable)
            "longitude": 69.876
        },
        "fire_visible": True,
        "smoke_visible": True,
        "description": "I can see massive flames and black smoke coming from the refinery."
    }
    
    logger.info("\n2. Evaluating Public Report Reliability")
    reporting_service = PublicReportingService()
    reliability = reporting_service.evaluate_report_reliability(public_report, firms_data)
    public_report["reliability"] = reliability
    
    logger.info(f"Report Reliability Score: {reliability['score']}")
    logger.info(f"Reasons: {reliability['reasons']}")
    
    logger.info("\n3. Running Enhanced Fusion (With Public Report)")
    fused_enhanced = EvidenceFusionEngine.fuse(
        firms_data=firms_data,
        reliability_data=weather_data,
        temporal_data=temporal_data,
        public_reports=[public_report]
    )
    logger.info(json.dumps(fused_enhanced, indent=2))
    
    logger.info("\n--- Conclusion ---")
    prob_diff = fused_enhanced['incidentProbability'] - fused_base['incidentProbability']
    logger.info(f"The public report boosted the incident probability by {prob_diff}%.")
    if fused_enhanced['confidence'] != fused_base['confidence']:
        logger.info(f"Confidence upgraded from {fused_base['confidence']} to {fused_enhanced['confidence']} due to eyewitness corroboration.")

if __name__ == "__main__":
    main()
