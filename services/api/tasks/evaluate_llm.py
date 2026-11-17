import logging
import os
import sys

from dotenv import load_dotenv

# Ensure we can import from adapters and services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from adapters.llm import GroqProvider
from services.generative import GenerativeService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("evaluate_llm")


def main():
    logger.info("--- LLM Provider & Generative Capabilities Test ---")

    load_dotenv()

    try:
        provider = GroqProvider()
    except ValueError as e:
        logger.error(f"CRITICAL ERROR: {e}")
        logger.error("Project rules mandate 'Never use mock/fake/hard-coded sample data'.")
        logger.error("Cannot proceed with LLM verification without a valid GROQ_API_KEY.")
        sys.exit(1)

    generative_service = GenerativeService(provider=provider)
    incident_id = "TEST-INCIDENT-001"

    # ---------------------------------------------------------
    # Structured Mock Pipeline Output (From Step 7 Verification)
    # ---------------------------------------------------------
    evidence_payload = {
        "fusion": {
            "incidentProbability": 95.0,
            "confidence": "HIGH"
        },
        "risk": {
            "severity": "CRITICAL",
            "riskScore": 195.0,
            "components": {"hazard": 9.75, "exposure": 10.0, "consequence": 2.0}
        },
        "temporal": {
            "classification": "abnormal spike"
        },
        "osm": {
            "feature_type": "industrial_zone",
            "name": "Jamnagar Refinery"
        }
    }

    decision_payload = {
        "state": "PUBLIC_EMERGENCY_ALERT_RECOMMENDED",
        "human_approval_required": True,
        "reasoning": "Critical risk and high probability warrant a public emergency alert."
    }

    # ---------------------------------------------------------
    # 1. Cause Narrative Generation
    # ---------------------------------------------------------
    logger.info("\n--- 1. Generating Probable Cause Narrative ---")
    try:
        narrative = generative_service.generate_cause_narrative(incident_id, evidence_payload)
        logger.info(f"NARRATIVE:\n{narrative}")
    except Exception as e:
        logger.error(f"Failed to generate narrative: {e}")

    # ---------------------------------------------------------
    # 2. Audit Summary Generation
    # ---------------------------------------------------------
    logger.info("\n--- 2. Generating Audit Summary ---")
    try:
        summary = generative_service.generate_audit_summary(incident_id, evidence_payload, decision_payload)
        logger.info(f"AUDIT SUMMARY:\n{summary}")
    except Exception as e:
        logger.error(f"Failed to generate summary: {e}")

    # ---------------------------------------------------------
    # 3. Safe Translation
    # ---------------------------------------------------------
    logger.info("\n--- 3. Translating Safety Message (with Allowlist Check) ---")

    original_message = "CRITICAL: Industrial thermal incident detected nearby. Please monitor local news."
    allowed_directives = ["monitor local news"]
    target_lang = "Hindi"

    logger.info(f"Original: {original_message}")
    logger.info(f"Allowed Directives: {allowed_directives}")
    logger.info("Executing safe translation...")

    try:
        translation = generative_service.translate_safety_message(
            incident_id=incident_id,
            original_message=original_message,
            target_language=target_lang,
            allowed_directives=allowed_directives
        )
        logger.info(f"TRANSLATION ({target_lang}):\n{translation}")
    except Exception as e:
        logger.error(f"Failed to translate safely: {e}")


if __name__ == "__main__":
    main()
