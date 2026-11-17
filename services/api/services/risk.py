"""
Risk Assessment Engine

Determines the overall risk and severity based on Hazard, Exposure, and Consequence.
Formula: Risk Score = Hazard * Exposure * Consequence
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class RiskAssessmentEngine:

    # Pre-defined multipliers based on OSM feature types
    CONSEQUENCE_MULTIPLIERS = {
        "industrial_zone": 2.0,
        "factory": 2.5,
        "power_plant": 3.0,
        "hospital": 3.0,
        "school": 2.5,
        "settlement_town": 2.0,
        "settlement_village": 1.5,
        "unknown": 1.0
    }

    @classmethod
    def assess(
        cls,
        fusion_data: Dict[str, Any],
        firms_data: Dict[str, Any],
        osm_facility: Dict[str, Any],
        distance_to_facility: float
    ) -> Dict[str, Any]:
        """
        Calculate risk score and severity.
        """
        probability = fusion_data.get("incidentProbability", 0.0)

        # If there's no incident, risk is zero
        if probability < 5.0:
            return {
                "riskScore": 0.0,
                "severity": "LOW"
            }

        # 1. Hazard (0 - 10)
        # Based on Incident Probability and FRP magnitude
        frp = firms_data.get("frp")
        if frp is None:
            frp = 0.0
        frp_factor = min(frp / 100.0, 5.0)  # Cap at 5.0
        prob_factor = probability / 20.0    # 0 to 5.0

        hazard = min(frp_factor + prob_factor, 10.0)

        # 2. Exposure (0 - 10)
        # Based on how close the hotspot is to the facility
        if distance_to_facility <= 500:
            exposure = 10.0
        elif distance_to_facility <= 1000:
            exposure = 8.0
        elif distance_to_facility <= 2000:
            exposure = 5.0
        elif distance_to_facility <= 5000:
            exposure = 2.0
        else:
            exposure = 1.0

        # 3. Consequence (1.0 - 3.0)
        # Based on the facility type
        feature_type = osm_facility.get("feature_type", "unknown")
        consequence = cls.CONSEQUENCE_MULTIPLIERS.get(feature_type, 1.0)

        # 4. Calculate Risk Score
        # Max theoretical score: 10 * 10 * 3.0 = 300
        risk_score = hazard * exposure * consequence

        # 5. Determine Severity
        if risk_score >= 150:
            severity = "CRITICAL"
        elif risk_score >= 80:
            severity = "HIGH"
        elif risk_score >= 30:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return {
            "riskScore": round(risk_score, 1),
            "severity": severity,
            "components": {
                "hazard": round(hazard, 2),
                "exposure": round(exposure, 2),
                "consequence": consequence
            }
        }
