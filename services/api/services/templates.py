"""
Alert Templates

Static, pre-approved text templates for Authority and Public messaging.
"""

from typing import Any, Dict

# ---------------------------------------------------------
# Static Safety Guidance (Pre-approved, not freely generated)
# ---------------------------------------------------------

SAFETY_GUIDANCE: Dict[str, Dict[str, Any]] = {
    "electrical": {
        "text": "Stay clear of power lines. Do not use water on electrical equipment.",
        "allowed_directives": ["stay clear", "do not use water"]
    },
    "gas_fuel": {
        "text": "Evacuate immediately upwind. Do not start vehicles or use electronics.",
        "allowed_directives": ["evacuate", "do not start vehicles", "do not use electronics"]
    },
    "chemical": {
        "text": "Shelter in place. Close all windows and turn off HVAC systems.",
        "allowed_directives": ["shelter in place", "close windows", "turn off hvac"]
    },
    "unknown_industrial": {
        "text": "Avoid the area. Follow local authority instructions.",
        "allowed_directives": ["avoid the area", "follow instructions"]
    },
    "natural": {
        "text": "Monitor local news and prepare for potential evacuation.",
        "allowed_directives": ["monitor local news", "prepare for evacuation"]
    },
    "agricultural": {
        "text": "Avoid smoke inhalation. Keep roads clear for emergency vehicles.",
        "allowed_directives": ["avoid smoke", "keep roads clear"]
    }
}


# ---------------------------------------------------------
# Authority Alert Template (Highly detailed, technical)
# ---------------------------------------------------------

AUTHORITY_ALERT_TEMPLATE = """
🚨 INCIDENT ID: {incident_id} 🚨
STATUS: {alert_state}

📍 LOCATION:
Facility: {facility_name} ({facility_type})
Coordinates: {latitude}, {longitude}
Proximity to Critical Assets: {exposure_distance}m

🔥 INCIDENT DETAILS:
Classification: {temporal_classification}
Incident Probability: {incident_probability}%
Evidence Confidence: {confidence}
FRP: {frp} MW (Baseline: {baseline_frp} MW | Deviation: {frp_deviation}σ)
Observation Quality: {obs_quality}
Weather Conditions: {weather_summary}

⚠️ RISK ASSESSMENT:
Severity: {severity}
Risk Score: {risk_score} (Hazard: {hazard} x Exposure: {exposure} x Consequence: {consequence})

🤖 PROBABLE CAUSE NARRATIVE:
{probable_cause}

📋 RECOMMENDED ACTION:
{recommended_action}
"""

# ---------------------------------------------------------
# Public Alert Template (Simple, actionable, no AI details)
# ---------------------------------------------------------

PUBLIC_ALERT_TEMPLATE = """
⚠️ EMERGENCY ALERT ⚠️

An industrial incident has been detected near {facility_name}.

{safety_guidance}

Please stay safe and await further instructions from local authorities.
"""
