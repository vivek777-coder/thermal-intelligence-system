import json
import logging
import os
import sys

# Ensure we can import from services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.fusion import EvidenceFusionEngine
from services.risk import RiskAssessmentEngine
from services.decision import EmergencyDecisionEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("evaluate_scenarios")

def load_fixtures():
    fixtures_path = os.path.join(os.path.dirname(__file__), "..", "tests", "fixtures", "historical_data.json")
    with open(fixtures_path, "r") as f:
        return json.load(f)

def evaluate_scenario(scenario):
    logger.info(f"\n--- Testing Scenario: {scenario['scenario_id']} ---")
    logger.info(f"Description: {scenario['description']}")
    
    inputs = scenario["inputs"]
    
    # 1. Fusion Engine
    fused_data = EvidenceFusionEngine.fuse(
        firms_data=inputs.get("firms_data", {}),
        reliability_data=inputs.get("weather_data", {}),
        temporal_data=inputs.get("temporal_behavior", {}),
        public_reports=inputs.get("public_reports", [])
    )
    
    logger.info(f"Fusion Output: Prob={fused_data['incidentProbability']}%, Conf={fused_data['confidence']}, Conflicts={fused_data['evidenceConflicts']}")
    
    # Check conflict expectation
    has_conflict = bool(fused_data.get("evidenceConflicts"))
    if has_conflict != scenario["expected_conflict"]:
        logger.error(f"❌ Conflict mismatch! Expected {scenario['expected_conflict']} but got {has_conflict}")
        return False
        
    # 2. Risk Assessment
    risk_data = RiskAssessmentEngine.assess(
        fusion_data=fused_data,
        firms_data=inputs.get("firms_data", {}),
        osm_facility={"feature_type": inputs.get("osm_context", {}).get("facility_type")},
        distance_to_facility=100.0 # Assuming all scenarios represent a direct hit/nearby for simplicity
    )
    
    logger.info(f"Risk Output: Severity={risk_data['severity']}, Score={risk_data['riskScore']}")
    
    # 3. Decision Engine
    decision_data = EmergencyDecisionEngine.decide(
        fusion_data=fused_data,
        risk_data=risk_data,
        temporal_data=inputs.get("temporal_behavior", {})
    )
    
    logger.info(f"Decision Output: State={decision_data['state']}, Reason={decision_data['reasoning']}")
    
    if decision_data["state"] == scenario["expected_decision"]:
        logger.info("✅ Scenario Passed!")
        return True
    else:
        logger.error(f"❌ State mismatch! Expected {scenario['expected_decision']} but got {decision_data['state']}")
        return False

def main():
    logger.info("Starting Automated Scenarios Evaluation (Real Historical Fixtures)")
    scenarios = load_fixtures()
    
    passed = 0
    for scenario in scenarios:
        success = evaluate_scenario(scenario)
        if success:
            passed += 1
            
    logger.info(f"\n--- Final Results: {passed}/{len(scenarios)} Scenarios Passed ---")
    if passed != len(scenarios):
        sys.exit(1)

if __name__ == "__main__":
    main()
