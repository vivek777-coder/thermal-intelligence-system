"""
Emergency Decision Engine

Deterministic state machine for producing final alerting states.
Enforces strict rules to prevent false public panics.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class EmergencyDecisionEngine:

    @classmethod
    def decide(
        cls,
        fusion_data: Dict[str, Any],
        risk_data: Dict[str, Any],
        temporal_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate inputs and determine the final emergency state.
        """
        probability = fusion_data.get("incidentProbability", 0.0)
        confidence = fusion_data.get("confidence", "LOW")
        severity = risk_data.get("severity", "LOW")
        classification = temporal_data.get("classification", "normal")

        state = "NO_ACTION"
        human_approval_required = False
        reasoning = []

        # ---------------------------------------------------------
        # State Machine Rules
        # ---------------------------------------------------------

        # Base mapping by Severity and Probability
        if severity == "CRITICAL" and probability >= 80:
            state = "PUBLIC_EMERGENCY_ALERT_RECOMMENDED"
            human_approval_required = True
            reasoning.append("Critical risk and high probability warrant a public emergency alert.")

        elif severity in ("HIGH", "CRITICAL") and probability >= 60:
            state = "PUBLIC_WARNING_RECOMMENDED"
            human_approval_required = True
            reasoning.append("High risk and moderate probability warrant a public warning.")

        elif severity == "HIGH" or (severity == "MEDIUM" and probability >= 50):
            state = "HIGH_PRIORITY_AUTHORITY_ALERT"
            reasoning.append("Significant risk detected; notifying authorities urgently.")

        elif severity == "MEDIUM" or probability >= 30:
            state = "AUTHORITY_ALERT"
            reasoning.append("Moderate risk detected; logging for authority review.")

        elif severity == "LOW" and probability >= 10:
            state = "MONITOR"
            reasoning.append("Low risk incident; monitoring for escalation.")

        else:
            state = "NO_ACTION"
            reasoning.append("Negligible risk or probability. No action required.")


        # ---------------------------------------------------------
        # Constraint Enforcement (Overrides)
        # ---------------------------------------------------------

        # Constraint 1: Persistent anomalies never trigger public alerts
        if classification == "persistent" and state in (
            "PUBLIC_WARNING_RECOMMENDED", "PUBLIC_EMERGENCY_ALERT_RECOMMENDED", "HIGH_PRIORITY_AUTHORITY_ALERT"
        ):
            state = "AUTHORITY_ALERT"
            human_approval_required = False
            reasoning.append("DOWNGRADE: Persistent thermal behavior alone cannot trigger public/high-priority alerts.")

        # Constraint 2: Low confidence never triggers evacuation-level states
        if confidence == "LOW" and state == "PUBLIC_EMERGENCY_ALERT_RECOMMENDED":
            state = "AUTHORITY_ALERT"
            human_approval_required = False
            reasoning.append("DOWNGRADE: Low confidence evidence prevents evacuation-level public alerts.")

        # Constraint 3: Medium confidence prevents highest public alert
        if confidence == "MEDIUM" and state == "PUBLIC_EMERGENCY_ALERT_RECOMMENDED":
            state = "PUBLIC_WARNING_RECOMMENDED"
            reasoning.append("DOWNGRADE: Medium confidence limits maximum alert to a warning, not a full emergency.")

        # Constraint 4: Insufficient evidence forces NO_ACTION or MONITOR
        if fusion_data.get("evidenceSummary") == "insufficient reliable evidence":
            if state not in ("NO_ACTION", "MONITOR"):
                state = "MONITOR"
                human_approval_required = False
                reasoning.append("DOWNGRADE: Insufficient reliable evidence prevents action beyond monitoring.")

        return {
            "state": state,
            "human_approval_required": human_approval_required,
            "reasoning": " ".join(reasoning)
        }
