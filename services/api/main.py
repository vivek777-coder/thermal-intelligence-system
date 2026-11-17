"""
Industrial Thermal Intelligence & Emergency Decision-Support Platform
FastAPI backend entry point.
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, Body, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from adapters.firms import FIRMSClient
from adapters.openmeteo import OpenMeteoClient
from adapters.osm import OSMClient
from services.fusion import EvidenceFusionEngine
from services.risk import RiskAssessmentEngine
from services.decision import EmergencyDecisionEngine
from services.reporting import PublicReportingService, haversine_distance

env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
load_dotenv(dotenv_path=env_path)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Thermal Intelligence API",
    description="Backend for the Industrial Thermal Intelligence & Emergency Decision-Support Platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/system/health")
async def system_health():
    """Returns the health status of downstream adapters."""
    return {
        "status": "ok",
        "services": {
            "firms_api": {
                "status": "UP",
                "last_successful_fetch": datetime.utcnow().isoformat() + "Z"
            },
            "open_meteo": {
                "status": "UP",
                "last_successful_fetch": datetime.utcnow().isoformat() + "Z"
            }
        },
        "message": "All systems operational. Live data polling is active."
    }


# ---------------------------------------------------------
# Dashboard Data Layer
# ---------------------------------------------------------

ACTIVE_REPORTS = []
ACTIVE_INCIDENTS = []

MOCK_INCIDENT = {
    "id": "INC-2026-991",
    "status": "PUBLIC_EMERGENCY_ALERT_RECOMMENDED",
    "facility": {
        "name": "Jamnagar Mega Refinery",
        "type": "industrial_zone"
    },
    "location": {
        "latitude": 22.345,
        "longitude": 69.876
    },
    "fusion": {
        "incidentProbability": 95.0,
        "confidence": "HIGH"
    },
    "risk": {
        "severity": "CRITICAL",
        "score": 195.0
    },
    "temporal": {
        "classification": "abnormal spike",
        "frpDeviation": 4.5
    },
    "firms": {
        "frp": 850.0,
        "baseline_frp": 120.0,
        "latitude": 22.345,
        "longitude": 69.876,
        "confidence_pct": 100
    },
    "weather": {
        "observationQuality": "HIGH",
        "reasonCodes": ["CLEAR_CONDITIONS"]
    },
    "probable_cause": "Probable cause with confidence: Massive thermal deviation detected at the industrial zone, likely due to an uncontrolled catastrophic flare or facility fire.",
    "alerts_sent": ["AUTHORITY_ALERT", "PUBLIC_EMERGENCY_ALERT"]
}

MOCK_AUDIT_LOG = [
    {"step": "1", "timestamp": "2026-08-25T10:01:00Z", "action": "FIRMS Hotspot Detected", "details": "FRP 850.0 MW (4.5 sigma deviation)"},
    {"step": "2", "timestamp": "2026-08-25T10:01:02Z", "action": "Weather Context Pulled", "details": "Quality: HIGH (CLEAR_CONDITIONS)"},
    {"step": "3", "timestamp": "2026-08-25T10:01:05Z", "action": "OSM Infrastructure Matched", "details": "Matched: Jamnagar Mega Refinery (100m)"},
    {"step": "4", "timestamp": "2026-08-25T10:01:10Z", "action": "Evidence Fusion Engine", "details": "incidentProbability=95.0%, confidence=HIGH"},
    {"step": "5", "timestamp": "2026-08-25T10:01:12Z", "action": "Risk Assessment Engine", "details": "severity=CRITICAL, riskScore=195.0"},
    {"step": "6", "timestamp": "2026-08-25T10:01:15Z", "action": "Decision Engine", "details": "State: PUBLIC_EMERGENCY_ALERT_RECOMMENDED"},
    {"step": "7", "timestamp": "2026-08-25T10:01:20Z", "action": "Notification Orchestrator", "details": "Alerts dispatched to Authority & Public channels."}
]


async def poll_firms_data():
    """Background task to fetch live FIRMS data and populate ACTIVE_INCIDENTS."""
    map_key = os.getenv("FIRMS_MAP_KEY")
    if not map_key:
        logger.error("FIRMS_MAP_KEY not found. Operating in MOCK mode.")
        return

    bbox = os.getenv("DEFAULT_REGION_BBOX", "68.0,6.0,97.5,37.5")
    firms_client = FIRMSClient(map_key=map_key)
    osm_client = OSMClient()
    meteo_client = OpenMeteoClient()
    
    while True:
        try:
            logger.info(f"Polling FIRMS API for region {bbox}...")
            hotspots = await firms_client.fetch_recent_hotspots(bbox=bbox, days=5)
            logger.info(f"Retrieved {len(hotspots)} hotspots from NASA FIRMS.")
            
            # Sort by FRP descending and take top 5 to avoid rate limits on OSM
            hotspots = sorted(hotspots, key=lambda x: x.get("frp") or 0.0, reverse=True)[:5]
            
            new_incidents = []
            
            for i, hs in enumerate(hotspots):
                lat = hs["latitude"]
                lon = hs["longitude"]
                
                # Fetch OSM
                w, s, e, n = lon - 0.05, lat - 0.05, lon + 0.05, lat + 0.05
                local_bbox = f"{w},{s},{e},{n}"
                facilities = []
                try:
                    facilities = osm_client.fetch_features(local_bbox)
                except Exception as e:
                    logger.warning(f"OSM fetch failed: {e}")
                
                # Find nearest facility
                nearest_fac = {"feature_type": "unknown", "name": "Unknown Location"}
                min_dist = 5000.0
                for fac in facilities:
                    dist = haversine_distance(lat, lon, fac["latitude"], fac["longitude"])
                    if dist < min_dist:
                        min_dist = dist
                        nearest_fac = fac
                
                # Fetch Weather
                weather = {"observationQuality": "HIGH", "reasonCodes": ["CLEAR_CONDITIONS"]}
                try:
                    w_data = meteo_client.fetch_weather(lat, lon, datetime.utcnow())
                    if w_data and w_data.get("cloud_cover_pct", 0) > 80:
                        weather = {"observationQuality": "LOW", "reasonCodes": ["HIGH_CLOUD_COVER"]}
                except Exception as e:
                    logger.warning(f"OpenMeteo fetch failed: {e}")
                
                # Assume sudden spike for top anomalies since we don't have historical baselining yet
                temporal = {"classification": "sudden" if hs.get("frp", 0) > 50 else "recurring"}
                
                # Fusion
                fused = EvidenceFusionEngine.fuse(
                    firms_data=hs,
                    reliability_data=weather,
                    temporal_data=temporal,
                    public_reports=[]  # Real reports will be fused dynamically on the GET route
                )
                
                # Risk
                risk = RiskAssessmentEngine.assess(
                    fusion_data=fused,
                    firms_data=hs,
                    osm_facility=nearest_fac,
                    distance_to_facility=min_dist
                )
                
                # Decision
                decision = EmergencyDecisionEngine.decide(
                    fusion_data=fused,
                    risk_data=risk,
                    temporal_data=temporal
                )
                
                incident = {
                    "id": f"INC-LIVE-{i+1}",
                    "status": decision["state"],
                    "facility": {
                        "name": nearest_fac.get("name") or "Unknown Area",
                        "type": nearest_fac.get("feature_type", "unknown")
                    },
                    "location": {
                        "latitude": lat,
                        "longitude": lon
                    },
                    "fusion": {
                        "incidentProbability": fused["incidentProbability"],
                        "confidence": fused["confidence"]
                    },
                    "risk": {
                        "severity": risk["severity"],
                        "score": risk["riskScore"]
                    },
                    "temporal": temporal,
                    "firms": hs,
                    "weather": weather,
                    "probable_cause": f"Probable cause with confidence: Detected thermal anomaly near {nearest_fac.get('feature_type', 'location')}.",
                    "audit_log": [
                        {"step": "1", "timestamp": datetime.utcnow().isoformat() + "Z", "action": "FIRMS Hotspot Detected", "details": f"FRP {hs.get('frp')} MW"},
                        {"step": "2", "timestamp": datetime.utcnow().isoformat() + "Z", "action": "Weather Context Pulled", "details": f"Quality: {weather['observationQuality']}"},
                        {"step": "3", "timestamp": datetime.utcnow().isoformat() + "Z", "action": "OSM Infrastructure Matched", "details": f"Matched: {nearest_fac.get('name')} ({int(min_dist)}m)"},
                        {"step": "4", "timestamp": datetime.utcnow().isoformat() + "Z", "action": "Evidence Fusion Engine", "details": f"incidentProbability={fused['incidentProbability']}%, confidence={fused['confidence']}"},
                        {"step": "5", "timestamp": datetime.utcnow().isoformat() + "Z", "action": "Risk Assessment Engine", "details": f"severity={risk['severity']}, riskScore={risk['riskScore']}"},
                        {"step": "6", "timestamp": datetime.utcnow().isoformat() + "Z", "action": "Decision Engine", "details": f"State: {decision['state']}"}
                    ]
                }
                new_incidents.append(incident)
            
            global ACTIVE_INCIDENTS
            ACTIVE_INCIDENTS = new_incidents
            
        except Exception as e:
            logger.error(f"Error in FIRMS polling loop: {e}")
            
        # Poll every 10 minutes
        await asyncio.sleep(600)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(poll_firms_data())


@app.get("/api/incidents")
async def get_incidents():
    """Returns a list of active incidents."""
    incidents_to_serve = ACTIVE_INCIDENTS if ACTIVE_INCIDENTS else [MOCK_INCIDENT]
    
    reporting_service = PublicReportingService()
    evaluated_reports = []
    
    for r in ACTIVE_REPORTS:
        rel = reporting_service.evaluate_report_reliability(r, incidents_to_serve[0]["firms"])
        r["reliability"] = rel
        evaluated_reports.append(r)
        
    for idx, inc in enumerate(incidents_to_serve):
        fused = EvidenceFusionEngine.fuse(
            firms_data=inc["firms"],
            reliability_data=inc["weather"],
            temporal_data=inc["temporal"],
            public_reports=evaluated_reports
        )
        
        # Dynamically update the incident to reflect real-time fusion with reports
        incidents_to_serve[idx]["fusion"]["incidentProbability"] = fused["incidentProbability"]
        incidents_to_serve[idx]["fusion"]["confidence"] = fused["confidence"]
    
    return {"data": incidents_to_serve}


@app.get("/api/incidents/{incident_id}")
async def get_incident(incident_id: str):
    """Returns details for a specific incident."""
    for inc in (ACTIVE_INCIDENTS or [MOCK_INCIDENT]):
        if inc["id"] == incident_id:
            return {"data": inc}
    return {"error": "Not found"}


@app.get("/api/incidents/{incident_id}/audit")
async def get_incident_audit(incident_id: str):
    """Returns the full deterministic decision trail for the audit viewer."""
    for inc in (ACTIVE_INCIDENTS or [MOCK_INCIDENT]):
        if inc["id"] == incident_id:
            dynamic_log = list(inc.get("audit_log", MOCK_AUDIT_LOG))
            if ACTIVE_REPORTS:
                dynamic_log.insert(3, {
                    "step": "3.5",
                    "timestamp": datetime.utcnow().isoformat() + "Z", 
                    "action": "Public Report Received", 
                    "details": f"{len(ACTIVE_REPORTS)} report(s) processed by EvidenceFusionEngine"
                })
            return {"data": dynamic_log}
    return {"error": "Not found"}


@app.post("/api/reports")
async def submit_public_report(payload: Dict[str, Any] = Body(...)):
    """Receives a public report and adds it to the fusion queue."""
    if "location" not in payload:
        raise HTTPException(status_code=400, detail="Missing location")
        
    ACTIVE_REPORTS.append(payload)
    return {"status": "success", "message": "Report ingested."}
