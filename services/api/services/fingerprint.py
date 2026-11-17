"""
Thermal Fingerprint Service

Computes statistical baselines for facilities and classifies anomalous thermal behavior.
"""

import logging
import statistics
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ThermalFingerprintService:
    """
    Service for calculating facility baselines and classifying anomalies.
    """

    MIN_HISTORY_OBSERVATIONS = 5

    @staticmethod
    def _get_time_of_day_bucket(dt: datetime) -> str:
        hour = dt.hour
        if 5 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"

    @classmethod
    def compute_baseline(cls, observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compute the baseline characteristics for a facility based on historical observations.
        
        Args:
            observations: A list of dicts representing past ThermalObservations.
                          Must contain 'frp' (float) and 'observed_at' (datetime).
                          
        Returns:
            Dictionary containing the baseline, or "insufficient history".
        """
        if len(observations) < cls.MIN_HISTORY_OBSERVATIONS:
            return {"status": "insufficient history"}

        # Extract FRP values (filter out missing/None)
        frp_values = [obs["frp"] for obs in observations if obs.get("frp") is not None]
        if not frp_values:
            return {"status": "insufficient history"}

        mean_frp = statistics.mean(frp_values)
        std_frp = statistics.stdev(frp_values) if len(frp_values) > 1 else 0.0
        max_frp = max(frp_values)
        min_frp = min(frp_values)

        # Temporal patterns
        times = [obs["observed_at"] for obs in observations if "observed_at" in obs]
        if not times:
            return {"status": "insufficient history"}

        times.sort()
        time_span_days = (times[-1] - times[0]).days or 1

        # Average detections per week
        frequency_weekly = (len(times) / time_span_days) * 7.0

        # Day of week pattern
        dow_counter = Counter(t.weekday() for t in times)
        # Time of day pattern
        tod_counter = Counter(cls._get_time_of_day_bucket(t) for t in times)

        return {
            "status": "success",
            "mean_frp": mean_frp,
            "std_frp": std_frp,
            "max_frp": max_frp,
            "min_frp": min_frp,
            "frequency_weekly": frequency_weekly,
            "day_of_week_pattern": dict(dow_counter),
            "time_of_day_pattern": dict(tod_counter),
            "total_observations": len(observations),
            "time_span_days": time_span_days
        }

    @classmethod
    def evaluate_observation(cls, baseline: Dict[str, Any], recent_observations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare recent observations against the baseline.
        """
        if baseline.get("status") == "insufficient history":
            return {
                "frpDeviation": 0.0,
                "frequencyDeviation": 0.0,
                "overallThermalAnomaly": False,
                "classification": "insufficient history"
            }

        if not recent_observations:
            return {
                "frpDeviation": 0.0,
                "frequencyDeviation": 0.0,
                "overallThermalAnomaly": False,
                "classification": "normal"
            }

        # Analyze recent FRP
        recent_frps = [obs["frp"] for obs in recent_observations if obs.get("frp") is not None]
        recent_mean_frp = statistics.mean(recent_frps) if recent_frps else 0.0

        b_mean = baseline["mean_frp"]
        b_std = baseline["std_frp"]

        # Calculate FRP Deviation (Z-score equivalent)
        if b_std > 0:
            frp_deviation = (recent_mean_frp - b_mean) / b_std
        else:
            frp_deviation = (recent_mean_frp - b_mean) / (b_mean if b_mean > 0 else 1.0)

        # Frequency Deviation
        # Calculate recent frequency (if spanning more than 1 day, else estimate daily rate * 7)
        times = [obs["observed_at"] for obs in recent_observations if "observed_at" in obs]
        if len(times) > 1:
            times.sort()
            recent_span = (times[-1] - times[0]).days or 1
            recent_freq_weekly = (len(times) / recent_span) * 7.0
        else:
            recent_freq_weekly = len(times) * 7.0

        frequency_deviation = recent_freq_weekly - baseline["frequency_weekly"]

        classification = cls.classify_temporal_behavior(baseline, recent_observations, frp_deviation, frequency_deviation)

        # Anomalous if FRP is > 2 std dev or frequency is highly elevated
        is_anomaly = frp_deviation > 2.0 or frequency_deviation > (baseline["frequency_weekly"] * 2)

        return {
            "frpDeviation": round(frp_deviation, 2),
            "frequencyDeviation": round(frequency_deviation, 2),
            "overallThermalAnomaly": is_anomaly,
            "classification": classification
        }

    @classmethod
    def classify_temporal_behavior(
        cls,
        baseline: Dict[str, Any],
        recent_observations: List[Dict[str, Any]],
        frp_deviation: float,
        freq_deviation: float
    ) -> str:
        """
        Classify the temporal behavior pattern based on deviations.
        """
        # Abnormal Spike / Sudden
        if frp_deviation >= 3.0:
            return "abnormal spike"

        b_freq = baseline["frequency_weekly"]

        # Escalating
        # (Could be defined as consistent high positive dev, but simplified here)
        if 1.0 <= frp_deviation < 3.0 and freq_deviation > b_freq:
            return "escalating"

        # Decaying
        if frp_deviation < -1.0 and freq_deviation < 0:
            return "decaying"

        # Persistent (High frequency overall)
        if b_freq > 14 and abs(freq_deviation) < b_freq * 0.5:
            return "persistent"

        # Recurring (Checks if it perfectly aligns with top TOD/DOW)
        # For simplicity, if it's moderate frequency and stable FRP:
        if 2 <= b_freq <= 14 and abs(frp_deviation) < 1.0:
            return "recurring"

        # Intermittent
        if b_freq < 2:
            return "intermittent"

        return "normal"
