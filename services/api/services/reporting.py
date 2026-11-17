import logging
from typing import Any, Dict, List
import math

logger = logging.getLogger(__name__)

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371e3
    phi1 = lat1 * math.pi / 180
    phi2 = lat2 * math.pi / 180
    delta_phi = (lat2 - lat1) * math.pi / 180
    delta_lambda = (lon2 - lon1) * math.pi / 180
    a = math.sin(delta_phi / 2) * math.sin(delta_phi / 2) + \
        math.cos(phi1) * math.cos(phi2) * \
        math.sin(delta_lambda / 2) * math.sin(delta_lambda / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class PublicReportingService:
    """
    Computes a deterministic reliability score for public reports based on location proximity,
    corroboration with FIRMS, and recency.
    """
    def evaluate_report_reliability(self, report: Dict[str, Any], firms_data: Dict[str, Any]) -> Dict[str, Any]:
        reliability_score = 0.0
        reason_codes = []
        
        # Distance check
        dist = haversine_distance(
            report["location"]["latitude"], report["location"]["longitude"],
            firms_data["latitude"], firms_data["longitude"]
        )
        
        if dist < 1000: # Within 1km
            reliability_score += 40.0
            reason_codes.append("LOCATION_MATCH_HIGH")
        elif dist < 5000: # Within 5km
            reliability_score += 20.0
            reason_codes.append("LOCATION_MATCH_MEDIUM")
        else:
            reason_codes.append("LOCATION_MISMATCH")
            
        # Corroboration check
        if report.get("fire_visible") and firms_data.get("frp", 0) > 0:
            reliability_score += 40.0
            reason_codes.append("THERMAL_CORROBORATION")
            
        if report.get("smoke_visible"):
            reliability_score += 20.0
            reason_codes.append("SMOKE_CORROBORATION")
            
        return {
            "score": min(reliability_score, 100.0),
            "reasons": reason_codes
        }
