import logging
import os
import sys

from dotenv import load_dotenv

# Ensure we can import from adapters and services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adapters.llm import GroqProvider
from services.generative import GenerativeService
from services.orchestrator import NotificationOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("evaluate_notifications")


def main():
    logger.info("--- Notification Orchestrator End-to-End Test ---")

    # Force ConsoleProvider for the test
    os.environ["NOTIFICATION_PROVIDER"] = "console"
    load_dotenv()

    # ---------------------------------------------------------
    # Setup LLM Provider (Will fail gracefully if no key)
    # ---------------------------------------------------------
    try:
        llm_provider = GroqProvider()
        generative_service = GenerativeService(provider=llm_provider)
    except ValueError as e:
        logger.warning(f"Groq Provider failed to initialize: {e}")
        logger.warning("Notification Orchestrator will use the robust LLM fallback mechanism to send English templates.")
        # Create a mock generative service that simply raises exceptions to trigger the fallback
        class MockGenerativeService:
            def translate_safety_message(self, *args, **kwargs):
                raise Exception("LLM Provider unavailable (No API Key)")
        generative_service = MockGenerativeService()

    orchestrator = NotificationOrchestrator(generative_service=generative_service)

    # ---------------------------------------------------------
    # Structured Mock Pipeline Output (Scenario A: Public Emergency)
    # ---------------------------------------------------------
    incident_id = "INC-2026-991"

    fusion_data = {
        "incidentProbability": 95.0,
        "confidence": "HIGH"
    }

    risk_data = {
        "severity": "CRITICAL",
        "riskScore": 195.0,
        "components": {"hazard": 9.75, "exposure": 10.0, "consequence": 2.0}
    }

    temporal_data = {
        "classification": "abnormal spike",
        "frpDeviation": 4.5
    }

    firms_data = {
        "frp": 850.0,
        "latitude": 22.345,
        "longitude": 69.876
    }

    osm_facility = {
        "feature_type": "industrial_zone",
        "name": "Jamnagar Mega Refinery"
    }

    reliability_data = {
        "observationQuality": "HIGH",
        "reasonCodes": ["CLEAR_CONDITIONS"]
    }

    decision_data = {
        "state": "PUBLIC_EMERGENCY_ALERT_RECOMMENDED",
        "human_approval_required": True,
        "reasoning": "Critical risk and high probability warrant a public emergency alert."
    }

    probable_cause = "Probable cause with confidence: Massive thermal deviation detected at the industrial zone, likely due to an uncontrolled catastrophic flare or facility fire."
    hazard_type = "gas_fuel"

    # ---------------------------------------------------------
    # Dispatch
    # ---------------------------------------------------------
    logger.info("Triggering Notification Orchestrator with structured decision payload...")
    results = orchestrator.dispatch_incident_alerts(
        incident_id=incident_id,
        decision_data=decision_data,
        fusion_data=fusion_data,
        risk_data=risk_data,
        temporal_data=temporal_data,
        firms_data=firms_data,
        osm_facility=osm_facility,
        reliability_data=reliability_data,
        probable_cause=probable_cause,
        hazard_type=hazard_type
    )

    logger.info(f"Dispatch Results: {results}")

if __name__ == "__main__":
    main()
