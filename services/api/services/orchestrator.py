import logging
from typing import Any, Dict

from adapters.notifications import get_notification_provider
from services.generative import GenerativeService
from services.templates import AUTHORITY_ALERT_TEMPLATE, PUBLIC_ALERT_TEMPLATE, SAFETY_GUIDANCE

logger = logging.getLogger(__name__)


class NotificationOrchestrator:
    """
    Wires the EmergencyDecisionEngine output to the correct templates,
    handles localization via the GenerativeService, and dispatches via the active Provider.
    """
    def __init__(self, generative_service: GenerativeService):
        self.provider = get_notification_provider()
        self.generative_service = generative_service

    def dispatch_incident_alerts(
        self,
        incident_id: str,
        decision_data: Dict[str, Any],
        fusion_data: Dict[str, Any],
        risk_data: Dict[str, Any],
        temporal_data: Dict[str, Any],
        firms_data: Dict[str, Any],
        osm_facility: Dict[str, Any],
        reliability_data: Dict[str, Any],
        probable_cause: str,
        hazard_type: str = "unknown_industrial"
    ) -> Dict[str, bool]:
        """
        Main entry point for formatting and dispatching alerts based on the state machine output.
        """
        state = decision_data.get("state", "NO_ACTION")
        results = {"authority": False, "public": False}

        # Determine if authority alert is needed
        if state in (
            "AUTHORITY_ALERT",
            "HIGH_PRIORITY_AUTHORITY_ALERT",
            "PUBLIC_WARNING_RECOMMENDED",
            "PUBLIC_EMERGENCY_ALERT_RECOMMENDED"
        ):
            # Format Authority Template
            authority_payload = AUTHORITY_ALERT_TEMPLATE.format(
                incident_id=incident_id,
                alert_state=state,
                facility_name=osm_facility.get("name", "Unknown Facility"),
                facility_type=osm_facility.get("feature_type", "Unknown Type"),
                latitude=firms_data.get("latitude", "N/A"),
                longitude=firms_data.get("longitude", "N/A"),
                exposure_distance=100.0, # Mocked for payload mapping
                temporal_classification=temporal_data.get("classification", "N/A"),
                incident_probability=fusion_data.get("incidentProbability", 0),
                confidence=fusion_data.get("confidence", "N/A"),
                frp=firms_data.get("frp", "N/A"),
                baseline_frp=120.0, # Mocked for payload mapping
                frp_deviation=temporal_data.get("frpDeviation", 0),
                obs_quality=reliability_data.get("observationQuality", "N/A"),
                weather_summary=" | ".join(reliability_data.get("reasonCodes", [])),
                severity=risk_data.get("severity", "N/A"),
                risk_score=risk_data.get("riskScore", 0),
                hazard=risk_data.get("components", {}).get("hazard", 0),
                exposure=risk_data.get("components", {}).get("exposure", 0),
                consequence=risk_data.get("components", {}).get("consequence", 0),
                probable_cause=probable_cause,
                recommended_action=decision_data.get("reasoning", "Review required.")
            )

            # Dispatch to authorities (e.g. predefined list of responder numbers)
            logger.info("Dispatching Authority Alert...")
            results["authority"] = self.provider.send_authority_alert(authority_payload, ["+1234567890"])

        # Determine if public alert is needed
        if state in ("PUBLIC_WARNING_RECOMMENDED", "PUBLIC_EMERGENCY_ALERT_RECOMMENDED"):
            # Format Public Template
            safety_profile = SAFETY_GUIDANCE.get(hazard_type, SAFETY_GUIDANCE["unknown_industrial"])
            english_public_payload = PUBLIC_ALERT_TEMPLATE.format(
                facility_name=osm_facility.get("name", "an industrial zone"),
                safety_guidance=safety_profile["text"]
            )

            # ---------------------------------------------------------
            # Robust LLM Fallback Mechanism for Translation
            # ---------------------------------------------------------
            public_payload_hi = english_public_payload
            public_payload_hinglish = english_public_payload

            logger.info("Attempting Generative Translation for Public Alerts...")
            try:
                public_payload_hi = self.generative_service.translate_safety_message(
                    incident_id=incident_id,
                    original_message=english_public_payload,
                    target_language="Hindi",
                    allowed_directives=safety_profile["allowed_directives"]
                )
            except Exception as e:
                logger.warning(f"Translation to Hindi failed: {e}. FALLING BACK TO ENGLISH.")

            try:
                public_payload_hinglish = self.generative_service.translate_safety_message(
                    incident_id=incident_id,
                    original_message=english_public_payload,
                    target_language="Hinglish",
                    allowed_directives=safety_profile["allowed_directives"]
                )
            except Exception as e:
                logger.warning(f"Translation to Hinglish failed: {e}. FALLING BACK TO ENGLISH.")

            # Dispatch Public Alerts (broadcasting)
            logger.info("Dispatching Public Alerts...")

            # For demonstration, we just log them together
            final_public_msg = (
                f"--- ENGLISH ---\n{english_public_payload}\n"
                f"--- HINDI ---\n{public_payload_hi}\n"
                f"--- HINGLISH ---\n{public_payload_hinglish}"
            )

            results["public"] = self.provider.send_public_alert(final_public_msg, ["PUBLIC_BROADCAST"])

        return results
