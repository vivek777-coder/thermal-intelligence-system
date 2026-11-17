import json
import logging
from typing import Any, Dict

from adapters.llm import LLMProvider

logger = logging.getLogger(__name__)


class SafetyViolationError(Exception):
    """Raised when an LLM outputs safety directives not present in the original message."""
    pass


class GenerativeService:
    """
    Handles LLM integrations for narrative generation, audit summarization, and translation.
    Enforces strict project rules around model autonomy and safety instructions.
    """

    def __init__(self, provider: LLMProvider):
        self.provider = provider

    def generate_cause_narrative(self, incident_id: str, evidence: Dict[str, Any]) -> str:
        """
        Generate a human-readable probable cause explanation.
        Project Rule: Must always state it as probable/uncertain, never confirmed.
        """
        system_prompt = (
            "You are an industrial thermal intelligence analyst. "
            "Write a 2-sentence explanation of a thermal anomaly based on the provided evidence. "
            "CRITICAL RULE: You must state the cause as 'probable cause with confidence' or 'likely due to'. "
            "NEVER state the cause as confirmed. NEVER recommend evacuations in this narrative."
        )

        user_prompt = f"Evidence Data:\n{json.dumps(evidence, indent=2)}"

        return self.provider.generate(system_prompt, user_prompt, incident_id)

    def generate_audit_summary(self, incident_id: str, evidence: Dict[str, Any], decision: Dict[str, Any]) -> str:
        """
        Generate a short analyst-readable summary of why the deterministic engine reached its decision.
        """
        system_prompt = (
            "You are an AI audit assistant. Summarize WHY the deterministic rule engine made its alerting decision. "
            "Keep it under 3 sentences. Be extremely concise. Focus on Hazard, Exposure, and Consequence."
        )

        payload = {
            "evidence": evidence,
            "decision": decision
        }
        user_prompt = f"Pipeline Output:\n{json.dumps(payload, indent=2)}"

        return self.provider.generate(system_prompt, user_prompt, incident_id)

    def translate_safety_message(
        self,
        incident_id: str,
        original_message: str,
        target_language: str,
        allowed_directives: list[str]
    ) -> str:
        """
        Translate a safety message.
        Enforces a safety-phrase allowlist check to ensure the model does not invent new directives.
        """
        system_prompt = (
            "You are a critical emergency alert translator. "
            f"Translate the provided safety message into {target_language}. "
            "CRITICAL RULE: DO NOT invent new safety instructions. Fill variables only. "
            "You MUST output valid JSON with two keys: "
            "'translation' (the translated string) and "
            "'directives_found' (a list of English safety directives you translated, e.g. ['evacuate', 'monitor'])."
        )

        user_prompt = f"Message to translate:\n{original_message}\n\nAllowed directives in original: {allowed_directives}"

        # We allow up to 3 retries for safety violations
        for attempt in range(3):
            try:
                output = self.provider.generate(system_prompt, user_prompt, incident_id)

                # Parse JSON
                try:
                    data = json.loads(output)
                except json.JSONDecodeError:
                    # Sometimes the model wraps in ```json
                    if "```json" in output:
                        cleaned = output.split("```json")[1].split("```")[0].strip()
                        data = json.loads(cleaned)
                    else:
                        raise ValueError("LLM did not return valid JSON")

                translation = data.get("translation", "")
                directives_found = data.get("directives_found", [])

                # SAFETY ALLOWLIST CHECK
                # Ensure the model didn't invent a directive that wasn't in the original allowed list
                allowed_set = set(d.lower() for d in allowed_directives)
                found_set = set(d.lower() for d in directives_found)

                unauthorized = found_set - allowed_set

                if unauthorized:
                    logger.warning(f"Safety Violation in translation! Unauthorized directives: {unauthorized}")
                    raise SafetyViolationError(f"Unauthorized safety directives detected: {unauthorized}")

                return translation

            except (ValueError, SafetyViolationError) as e:
                logger.error(f"Translation validation failed (Attempt {attempt+1}/3): {e}")
                if attempt == 2:
                    raise Exception(f"Failed to generate a safe translation after 3 attempts: {e}")

        return ""
