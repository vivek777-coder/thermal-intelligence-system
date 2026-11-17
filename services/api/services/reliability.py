"""
Observation Reliability Engine

Applies deterministic rules to evaluate the quality of a thermal observation
(or the absence of one) based on concurrent environmental conditions (weather & AQ).
"""

import logging
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class QualityLevel(Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReasonCode(Enum):
    CLEAR_CONDITIONS = "CLEAR_CONDITIONS"
    HIGH_CLOUD_COVER = "HIGH_CLOUD_COVER"
    HEAVY_RAIN = "HEAVY_RAIN"
    POOR_VISIBILITY = "POOR_VISIBILITY"
    HIGH_AEROSOLS = "HIGH_AEROSOLS"
    MISSING_WEATHER_DATA = "MISSING_WEATHER_DATA"


class ObservationReliabilityEngine:
    """
    Engine for determining the reliability of a thermal event observation based
    on weather and air quality thresholds.
    """

    # Deterministic Thresholds
    CLOUD_COVER_LOW_QUALITY_THRESHOLD = 90.0
    CLOUD_COVER_MED_QUALITY_THRESHOLD = 70.0

    RAINFALL_LOW_QUALITY_THRESHOLD = 2.0  # mm/hr

    VISIBILITY_LOW_QUALITY_THRESHOLD = 1000.0  # meters
    VISIBILITY_MED_QUALITY_THRESHOLD = 5000.0  # meters

    # AOD (Aerosol Optical Depth): > 1.0 is generally very hazy/smoky
    AEROSOL_MED_QUALITY_THRESHOLD = 1.0

    @classmethod
    def evaluate(
        cls,
        has_thermal_hotspot: bool,
        weather_data: Dict[str, Any],
        aq_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Evaluate conditions and return a reliability assessment.
        
        Args:
            has_thermal_hotspot: True if FIRMS (or another source) reported a hotspot.
            weather_data: Dictionary of weather metrics from Open-Meteo.
            aq_data: Dictionary of air quality metrics.
            
        Returns:
            Dictionary containing observationQuality, reasonCodes, and textual evaluation.
        """
        if not weather_data:
            # If we have no weather data to verify against, we must downgrade reliability
            # to be safe, but we don't invalidate the hotspot entirely.
            return {
                "observationQuality": QualityLevel.MEDIUM.value,
                "reasonCodes": [ReasonCode.MISSING_WEATHER_DATA.value],
                "evaluation_message": "Missing weather data for verification." if has_thermal_hotspot else "No reliable thermal evidence"
            }

        aq_data = aq_data or {}
        reasons: List[ReasonCode] = []
        quality = QualityLevel.HIGH

        # 1. Cloud Cover Check
        cloud_cover = weather_data.get("cloud_cover_pct")
        if cloud_cover is not None:
            if cloud_cover > cls.CLOUD_COVER_LOW_QUALITY_THRESHOLD:
                quality = QualityLevel.LOW
                reasons.append(ReasonCode.HIGH_CLOUD_COVER)
            elif cloud_cover > cls.CLOUD_COVER_MED_QUALITY_THRESHOLD and quality != QualityLevel.LOW:
                quality = QualityLevel.MEDIUM
                reasons.append(ReasonCode.HIGH_CLOUD_COVER)

        # 2. Rainfall Check (heavy rain obscures infrared signatures)
        rainfall = weather_data.get("precipitation_mm")
        if rainfall is not None and rainfall > cls.RAINFALL_LOW_QUALITY_THRESHOLD:
            quality = QualityLevel.LOW
            reasons.append(ReasonCode.HEAVY_RAIN)

        # 3. Visibility Check (fog/smog blocks thermal signatures)
        visibility = weather_data.get("visibility_m")
        if visibility is not None:
            if visibility < cls.VISIBILITY_LOW_QUALITY_THRESHOLD:
                quality = QualityLevel.LOW
                reasons.append(ReasonCode.POOR_VISIBILITY)
            elif visibility < cls.VISIBILITY_MED_QUALITY_THRESHOLD and quality != QualityLevel.LOW:
                quality = QualityLevel.MEDIUM
                reasons.append(ReasonCode.POOR_VISIBILITY)

        # 4. Air Quality (Aerosols) Check
        aod = aq_data.get("aod")
        if aod is not None and aod > cls.AEROSOL_MED_QUALITY_THRESHOLD and quality != QualityLevel.LOW:
            quality = QualityLevel.MEDIUM
            reasons.append(ReasonCode.HIGH_AEROSOLS)

        if not reasons:
            reasons.append(ReasonCode.CLEAR_CONDITIONS)

        # 5. Critical Rule Enforcement
        # If observation quality is poor and FIRMS shows no hotspot, the output must be
        # "no reliable thermal evidence" — never "no fire".

        evaluation_message = ""

        if not has_thermal_hotspot:
            if quality in (QualityLevel.LOW, QualityLevel.MEDIUM):
                evaluation_message = "no reliable thermal evidence"
            else:
                evaluation_message = "no fire detected under clear conditions"
        else:
            if quality == QualityLevel.LOW:
                evaluation_message = "hotspot detected, but environmental reliability is LOW"
            elif quality == QualityLevel.MEDIUM:
                evaluation_message = "hotspot detected, with MEDIUM environmental reliability"
            else:
                evaluation_message = "hotspot detected with HIGH environmental reliability"

        return {
            "observationQuality": quality.value,
            "reasonCodes": [r.value for r in reasons],
            "evaluation_message": evaluation_message,
            "source_reliability_scores": {
                "environmental_interference": round(cloud_cover or 0, 1)  # Just an example score factor
            }
        }
