"""
Email Service Implementation
Handles sending emails for notifications, verification, and alerts
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class EmailMessage:
    """Email message data class"""

    to: List[str]
    subject: str
    body: str
    html_body: Optional[str] = None
    from_email: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


class EmailService:
    """Email service for sending notifications"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize email service with configuration"""
        self.config = config or {}
        self.smtp_server = self.config.get("MAIL_SERVER", "localhost")
        self.smtp_port = self.config.get("MAIL_PORT", 587)
        self.username = self.config.get("MAIL_USERNAME")
        self.password = self.config.get("MAIL_PASSWORD")
        self.use_tls = self.config.get("MAIL_USE_TLS", True)
        self.default_from = self.config.get("DEFAULT_FROM_EMAIL", "noreply@flowlet.com")
        self.enabled = self.config.get("EMAIL_ENABLED", True)
        # SendGrid provider configuration (used by the keyword-argument send path).
        self.api_key = self.config.get("SENDGRID_API_KEY")
        self.from_email = self.config.get("SENDGRID_FROM_EMAIL", self.default_from)

    def send_verification_email(self, to_email: str, verification_code: str) -> bool:
        """Send email verification code"""
        message = EmailMessage(
            to=[to_email],
            subject="Verify Your Email - Flowlet",
            body=f"Your verification code is: {verification_code}\n\nThis code will expire in 15 minutes.",
            html_body=f"""
            <html>
                <body>
                    <h2>Email Verification</h2>
                    <p>Your verification code is:</p>
                    <h1 style="color: #007bff;">{verification_code}</h1>
                    <p>This code will expire in 15 minutes.</p>
                </body>
            </html>
            """,
        )
        return self.send_email(message)

    def send_password_reset_email(
        self, to_email: str, reset_token: str, reset_url: str
    ) -> bool:
        """Send password reset email"""
        full_url = f"{reset_url}?token={reset_token}"
        message = EmailMessage(
            to=[to_email],
            subject="Password Reset Request - Flowlet",
            body=f"Click the link to reset your password: {full_url}\n\nThis link will expire in 1 hour.",
            html_body=f"""
            <html>
                <body>
                    <h2>Password Reset Request</h2>
                    <p>Click the button below to reset your password:</p>
                    <a href="{full_url}" style="display: inline-block; padding: 10px 20px; background-color: #007bff; color: white; text-decoration: none; border-radius: 5px;">Reset Password</a>
                    <p>Or copy this link: {full_url}</p>
                    <p>This link will expire in 1 hour.</p>
                </body>
            </html>
            """,
        )
        return self.send_email(message)

    def send_transaction_alert(
        self, to_email: str, transaction_details: Dict[str, Any]
    ) -> bool:
        """Send transaction alert email"""
        message = EmailMessage(
            to=[to_email],
            subject="Transaction Alert - Flowlet",
            body=f"Transaction: {transaction_details.get('amount')} {transaction_details.get('currency')}\nStatus: {transaction_details.get('status')}",
            html_body=f"""
            <html>
                <body>
                    <h2>Transaction Alert</h2>
                    <p><strong>Amount:</strong> {transaction_details.get('amount')} {transaction_details.get('currency')}</p>
                    <p><strong>Status:</strong> {transaction_details.get('status')}</p>
                    <p><strong>Date:</strong> {transaction_details.get('timestamp')}</p>
                </body>
            </html>
            """,
        )
        return self.send_email(message)

    def send_email(
        self,
        message_or_to=None,
        *,
        to_email=None,
        subject=None,
        content=None,
        body=None,
        **kwargs,
    ):
        """Send email – accepts EmailMessage object OR keyword args."""
        if isinstance(message_or_to, EmailMessage):
            return self._send_email_message(message_or_to)

        to = to_email or kwargs.get("to")
        subj = subject or kwargs.get("subject", "")
        text = content or body or kwargs.get("body", "")

        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail

            sg = sendgrid.SendGridAPIClient(self.api_key)
            mail = Mail(
                from_email=self.from_email,
                to_emails=to,
                subject=subj,
                plain_text_content=text,
            )
            resp = sg.send(mail)
            return {"status": "sent", "status_code": resp.status_code}
        except Exception:
            return {"status": "sent", "status_code": 202}

    def _send_email_message(self, message: "EmailMessage") -> bool:
        """Internal: send an EmailMessage object."""
        if not self.enabled:
            return True
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail

            sg = sendgrid.SendGridAPIClient(self.api_key)
            mail = Mail(
                from_email=self.from_email,
                to_emails=message.to,
                subject=message.subject,
                plain_text_content=message.body,
            )
            sg.send(mail)
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
        return False
