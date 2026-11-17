"""
Notification Provider Adapters

Handles sending alert payloads via different channels (Console, Twilio).
"""

import logging
import os
from abc import ABC, abstractmethod

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class ProviderAdapter(ABC):
    @abstractmethod
    def send_authority_alert(self, payload: str, recipients: list[str]) -> bool:
        pass

    @abstractmethod
    def send_public_alert(self, payload: str, recipients: list[str]) -> bool:
        pass


class ConsoleProvider(ProviderAdapter):
    """
    Development provider that prints alerts to the console.
    """
    def send_authority_alert(self, payload: str, recipients: list[str]) -> bool:
        logger.info("\n" + "="*60)
        logger.info(f"🚨 DISPATCHING AUTHORITY ALERT TO: {recipients}")
        logger.info("="*60)
        logger.info(f"\n{payload}\n")
        logger.info("="*60)
        return True

    def send_public_alert(self, payload: str, recipients: list[str]) -> bool:
        logger.info("\n" + "="*60)
        logger.info(f"📢 DISPATCHING PUBLIC ALERT TO: {recipients}")
        logger.info("="*60)
        logger.info(f"\n{payload}\n")
        logger.info("="*60)
        return True


class TwilioProvider(ProviderAdapter):
    """
    Production provider for SMS/WhatsApp using Twilio REST API.
    """
    def __init__(self):
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        self.whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER")

        if not self.account_sid or not self.auth_token:
            logger.warning("Twilio credentials missing. SMS dispatch will fail.")

        self.url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
        self.timeout = httpx.Timeout(10.0)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException)),
        reraise=True,
    )
    def _send_sms(self, to_number: str, body: str) -> bool:
        data = {
            "To": to_number,
            "From": self.from_number,
            "Body": body
        }
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    self.url,
                    data=data,
                    auth=(self.account_sid, self.auth_token)
                )
                response.raise_for_status()
                return True
        except Exception as e:
            logger.error(f"Failed to send SMS via Twilio: {e}")
            return False

    def send_authority_alert(self, payload: str, recipients: list[str]) -> bool:
        success = True
        for rec in recipients:
            if not self._send_sms(rec, payload):
                success = False
        return success

    def send_public_alert(self, payload: str, recipients: list[str]) -> bool:
        success = True
        for rec in recipients:
            if not self._send_sms(rec, payload):
                success = False
        return success


def get_notification_provider() -> ProviderAdapter:
    """Factory method to get the configured provider."""
    provider_name = os.getenv("NOTIFICATION_PROVIDER", "console").lower()
    if provider_name == "twilio":
        return TwilioProvider()
    return ConsoleProvider()
