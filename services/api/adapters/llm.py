"""
LLM Provider Adapter

Defines the LLMProvider interface and the concrete GroqProvider using the
OpenAI-compatible chat completions endpoint.
"""

import json
import logging
import os
from abc import ABC, abstractmethod

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Raised when LLM API is unreachable or returns an error."""
    pass


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_prompt: str, incident_id: str) -> str:
        pass


class GroqProvider(LLMProvider):
    """
    Concrete implementation of LLMProvider using Groq's OpenAI-compatible endpoint.
    """

    URL = "https://api.groq.com/openai/v1/chat/completions"

    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model or os.getenv("GROQ_MODEL", "llama3-8b-8192")

        if not self.api_key or self.api_key.startswith("<"):
            raise ValueError("Invalid or missing GROQ_API_KEY")

        self.timeout = httpx.Timeout(15.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True,
    )
    def generate(self, system_prompt: str, user_prompt: str, incident_id: str) -> str:
        """
        Generate text using the Groq API and log the audit trail.
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2, # Keep low for deterministic-ish reasoning
            "max_tokens": 512
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(self.URL, headers=headers, json=payload)

            if response.status_code != 200:
                logger.error(f"Groq API Error: {response.status_code} {response.text}")
                raise LLMError(f"API Error {response.status_code}")

            data = response.json()
            output = data["choices"][0]["message"]["content"].strip()

            # Use Case 4: Log every Groq call linked to incident ID for audit trail
            audit_log = {
                "incident_id": incident_id,
                "model": self.model,
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "output": output
            }
            logger.info(f"AUDIT LOG: {json.dumps(audit_log)}")

            return output

        except Exception as e:
            logger.error(f"Error generating text from Groq: {e}")
            raise LLMError(str(e))
