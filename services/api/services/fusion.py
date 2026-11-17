"""
Evidence Fusion Engine

Combines multiple streams of evidence (FIRMS, weather, OSM context, temporal behavior)
to calculate an overall incident probability and determine confidence levels.
Now includes Public Reports for two-way verification.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class EvidenceFusionEngine:

    @classmethod
    def fuse(
        cls,
        firms_data: Dict[str, Any],
        reliability_data: Dict[str, Any],
        temporal_data: Dict[str, Any],
        public_reports: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Fuse evidence into a coherent incident probability and confidence score.
        
        Args:
            firms_data: Thermal observation payload (FRP, base confidence).
            reliability_data: Output from ObservationReliabilityEngine.
            temporal_data: Output from ThermalFingerprintService.
            public_reports: Output from PublicReportingService with deterministic reliability scores.
            
        Returns:
            Dictionary with fused metrics.
        """
        public_reports = public_reports or []
        
        # Base confidence from FIRMS (0-100)
        base_confidence = firms_data.get("confidence_pct")
        if base_confidence is None:
            base_confidence = 50.0
        obs_quality = reliability_data.get("observationQuality", "MEDIUM")
        behavior = temporal_data.get("classification", "normal")
        overall_anomaly = temporal_data.get("overallThermalAnomaly", False)

        # 1. Base Probability driven by thermal deviation
        probability = 50.0

        if behavior == "abnormal spike":
            probability = 95.0
        elif behavior == "escalating":
            probability = 85.0
        elif behavior == "sudden":
            probability = 80.0
        elif behavior == "persistent":
            probability = 20.0  # Persistent industrial heat is NOT an incident
        elif behavior == "recurring":
            probability = 15.0
        elif behavior == "normal":
            probability = 5.0

        # Adjust probability by thermal confidence
        probability = probability * (base_confidence / 100.0)

        # 2. Public Reports Corroboration
        has_reliable_report = False
        report_boost = 0.0
        
        for report in public_reports:
            rel_score = report.get("reliability", {}).get("score", 0.0)
            if rel_score >= 60.0:
                has_reliable_report = True
                report_boost = max(report_boost, 25.0)
                
        # Boost probability if the public actively reports a fire/smoke
        probability = min(probability + report_boost, 100.0)

        # 3. Calculate Final Confidence Score
        confidence_score = base_confidence

        if obs_quality == "LOW":
            confidence_score *= 0.5  # Heavy penalty for poor weather
        elif obs_quality == "MEDIUM":
            confidence_score *= 0.8
            
        # Boost confidence if we have reliable eyewitnesses
        if has_reliable_report:
            confidence_score = min(confidence_score + 30.0, 100.0)

        if confidence_score >= 80:
            final_confidence = "HIGH"
        elif confidence_score >= 50:
            final_confidence = "MEDIUM"
        else:
            final_confidence = "LOW"

        # 4. Check for Conflicts
        conflicts = []
        if base_confidence > 90 and obs_quality == "LOW" and not has_reliable_report:
            conflicts.append("High FIRMS confidence contradicts poor environmental quality without eyewitness corroboration.")

        if behavior == "persistent" and overall_anomaly:
            conflicts.append("Behavior is persistent but flagged as an anomaly.")

        if not firms_data and obs_quality in ("LOW", "MEDIUM") and not has_reliable_report:
            # Enforce the critical rule: "no reliable thermal evidence"
            return {
                "incidentProbability": 0.0,
                "evidenceSummary": "insufficient reliable evidence",
                "evidenceConflicts": conflicts,
                "confidence": "LOW",
                "raw_confidence_score": 0.0
            }

        summary = f"Fused observation: {behavior} behavior with {final_confidence} confidence."
        
        if len(conflicts) >= 2:
            return {
                "incidentProbability": 0.0,
                "evidenceSummary": "evidence is conflicting",
                "evidenceConflicts": conflicts,
                "confidence": "LOW",
                "raw_confidence_score": confidence_score
            }

        return {
            "incidentProbability": round(probability, 1),
            "evidenceSummary": summary,
            "evidenceConflicts": conflicts,
            "confidence": final_confidence,
            "raw_confidence_score": round(confidence_score, 1)
        }
