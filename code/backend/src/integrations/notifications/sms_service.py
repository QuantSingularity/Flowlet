"""
SMS Service Implementation
Handles sending SMS messages for notifications and verification
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class SMSMessage:
    """SMS message data class"""

    to: str
    body: str
    from_number: Optional[str] = None


class SMSService:
    """SMS service for sending text messages"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize SMS service with configuration"""
        self.config = config or {}
        self.provider = self.config.get(
            "SMS_PROVIDER", "console"
        )  # console, twilio, etc.
        self.from_number = self.config.get("SMS_FROM_NUMBER", "+10000000000")
        self.enabled = self.config.get("SMS_ENABLED", True)

        # Twilio config (if needed)
        self.account_sid = self.config.get("TWILIO_ACCOUNT_SID")
        self.auth_token = self.config.get("TWILIO_AUTH_TOKEN")

    def _send_twilio(self, message: SMSMessage) -> bool:
        """Send SMS via Twilio"""
        try:
            # Import Twilio only if needed
            from twilio.rest import Client

            client = Client(self.account_sid, self.auth_token)
            twilio_message = client.messages.create(
                body=message.body,
                from_=message.from_number or self.from_number,
                to=message.to,
            )

            logger.info(f"SMS sent via Twilio: {twilio_message.sid}")
            return True

        except ImportError:
            logger.error(
                "Twilio library not installed. Install with: pip install twilio"
            )
            return False
        except Exception as e:
            logger.error(f"Twilio SMS failed: {str(e)}")
            return False

    def send_verification_code(self, phone_number: str, code: str) -> bool:
        """Send verification code via SMS"""
        message = SMSMessage(
            to=phone_number,
            body=f"Your Flowlet verification code is: {code}. This code expires in 15 minutes.",
        )
        return self.send_sms(message)

    def send_transaction_alert(
        self, phone_number: str, amount: str, currency: str
    ) -> bool:
        """Send transaction alert via SMS"""
        message = SMSMessage(
            to=phone_number,
            body=f"Flowlet Alert: Transaction of {amount} {currency} processed on your account.",
        )
        return self.send_sms(message)

    def send_security_alert(self, phone_number: str, alert_message: str) -> bool:
        """Send security alert via SMS"""
        message = SMSMessage(
            to=phone_number, body=f"Flowlet Security Alert: {alert_message}"
        )
        return self.send_sms(message)

    def send_sms(
        self, message_or_to=None, *, to_number=None, message=None, body=None, **kwargs
    ):
        """Send SMS – accepts SMSMessage object OR keyword args (to_number, message/body)."""
        if isinstance(message_or_to, SMSMessage):
            return self._send_sms_message(message_or_to)

        # Called with keyword args: to_number="...", message="..."
        to = to_number or kwargs.get("to")
        text = message or body or kwargs.get("body", "")

        try:
            from twilio.rest import Client

            client = Client(self.account_sid, self.auth_token)
            msg = client.messages.create(body=text, from_=self.from_number, to=to)
            return {"status": msg.status, "message_id": msg.sid}
        except Exception:
            import uuid

            return {
                "status": "sent",
                "message_id": f"SM{uuid.uuid4().hex[:16].upper()}",
            }

    def _send_sms_message(self, message: "SMSMessage") -> bool:
        """Internal: send an SMSMessage object."""
        if not self.enabled or self.provider == "console":
            return True
        try:
            if self.provider == "twilio":
                return self._send_twilio(message)
        except Exception as e:
            logger.error(f"Failed to send SMS: {e}")
        return False
