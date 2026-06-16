import base64
import hashlib
import logging
import secrets
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from io import BytesIO
from typing import Any, Dict, List, Optional

try:
    import pyotp

    PYOTP_AVAILABLE = True
except ImportError:
    pyotp = None
    PYOTP_AVAILABLE = False
try:
    import qrcode

    QRCODE_AVAILABLE = True
except ImportError:
    qrcode = None
    QRCODE_AVAILABLE = False
from sqlalchemy.orm import Session

"\nAdvanced Authentication Service\n===============================\n\nMulti-factor authentication and advanced security features for financial applications.\n"


class AuthenticationMethod(Enum):
    """Authentication methods."""

    PASSWORD = "password"
    SMS = "sms"
    EMAIL = "email"
    TOTP = "totp"
    BIOMETRIC = "biometric"
    HARDWARE_TOKEN = "hardware_token"
    PUSH_NOTIFICATION = "push_notification"


class AuthenticationStatus(Enum):
    """Authentication status."""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    EXPIRED = "expired"
    BLOCKED = "blocked"


@dataclass
class AuthenticationResult:
    """Authentication result."""

    user_id: str
    session_id: str
    status: AuthenticationStatus
    methods_used: List[AuthenticationMethod]
    risk_score: float
    expires_at: datetime
    requires_additional_auth: bool = False
    next_auth_methods: List[AuthenticationMethod] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "status": self.status.value,
            "methods_used": [method.value for method in self.methods_used],
            "risk_score": self.risk_score,
            "expires_at": self.expires_at.isoformat(),
            "requires_additional_auth": self.requires_additional_auth,
            "next_auth_methods": [
                method.value for method in self.next_auth_methods or []
            ],
        }


class AdvancedAuthenticationService:
    """
    Advanced authentication service with multi-factor authentication.

    Features:
    - Multi-factor authentication (MFA)
    - Risk-based authentication
    - Biometric authentication
    - Hardware token support
    - Session management
    - Account lockout protection
    - Adaptive authentication
    """

    def __init__(self, db_session: Session, config: Dict[str, Any] = None) -> None:
        self.db = db_session
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self._user_credentials = {}
        self._mfa_secrets = {}
        self._active_sessions = {}
        self._failed_attempts = {}
        self._locked_accounts = {}
        self._initialize_auth_service()

    def _initialize_auth_service(self) -> object:
        """Initialize the authentication service."""
        self.logger.info("Advanced authentication service initialized")

    async def authenticate_user(
        self,
        user_id: str,
        credentials: Dict[str, Any],
        request_context: Dict[str, Any] = None,
    ) -> AuthenticationResult:
        """
        Authenticate a user with multiple factors.

        Args:
            user_id: User identifier
            credentials: Authentication credentials
            request_context: Request context for risk assessment

        Returns:
            AuthenticationResult
        """
        session_id = str(uuid.uuid4())
        try:
            if self._is_account_locked(user_id):
                return AuthenticationResult(
                    user_id=user_id,
                    session_id=session_id,
                    status=AuthenticationStatus.BLOCKED,
                    methods_used=[],
                    risk_score=1.0,
                    expires_at=datetime.now(timezone.utc),
                )
            risk_score = await self._assess_authentication_risk(
                user_id, request_context or {}
            )
            required_methods = self._determine_required_auth_methods(
                user_id, risk_score
            )
            validated_methods = []
            if AuthenticationMethod.PASSWORD in required_methods:
                password = credentials.get("password", "")
                if await self._validate_password(user_id, password):
                    validated_methods.append(AuthenticationMethod.PASSWORD)
                else:
                    await self._record_failed_attempt(user_id)
                    return AuthenticationResult(
                        user_id=user_id,
                        session_id=session_id,
                        status=AuthenticationStatus.FAILED,
                        methods_used=[],
                        risk_score=risk_score,
                        expires_at=datetime.now(timezone.utc),
                    )
            if AuthenticationMethod.TOTP in required_methods:
                totp_code = credentials.get("totp_code", "")
                if await self._validate_totp(user_id, totp_code):
                    validated_methods.append(AuthenticationMethod.TOTP)
                else:
                    return AuthenticationResult(
                        user_id=user_id,
                        session_id=session_id,
                        status=AuthenticationStatus.FAILED,
                        methods_used=validated_methods,
                        risk_score=risk_score,
                        expires_at=datetime.now(timezone.utc),
                    )
            if AuthenticationMethod.SMS in required_methods:
                sms_code = credentials.get("sms_code", "")
                if await self._validate_sms_code(user_id, sms_code):
                    validated_methods.append(AuthenticationMethod.SMS)
                else:
                    return AuthenticationResult(
                        user_id=user_id,
                        session_id=session_id,
                        status=AuthenticationStatus.FAILED,
                        methods_used=validated_methods,
                        risk_score=risk_score,
                        expires_at=datetime.now(timezone.utc),
                    )
            if set(validated_methods) >= set(required_methods):
                session_duration = self._calculate_session_duration(risk_score)
                expires_at = datetime.now(timezone.utc) + session_duration
                self._active_sessions[session_id] = {
                    "user_id": user_id,
                    "created_at": datetime.now(timezone.utc),
                    "expires_at": expires_at,
                    "risk_score": risk_score,
                    "methods_used": validated_methods,
                    "last_activity": datetime.now(timezone.utc),
                }
                if user_id in self._failed_attempts:
                    del self._failed_attempts[user_id]
                return AuthenticationResult(
                    user_id=user_id,
                    session_id=session_id,
                    status=AuthenticationStatus.SUCCESS,
                    methods_used=validated_methods,
                    risk_score=risk_score,
                    expires_at=expires_at,
                )
            else:
                remaining_methods = [
                    m for m in required_methods if m not in validated_methods
                ]
                return AuthenticationResult(
                    user_id=user_id,
                    session_id=session_id,
                    status=AuthenticationStatus.PENDING,
                    methods_used=validated_methods,
                    risk_score=risk_score,
                    expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
                    requires_additional_auth=True,
                    next_auth_methods=remaining_methods,
                )
        except Exception as e:
            self.logger.error(f"Authentication error for user {user_id}: {str(e)}")
            return AuthenticationResult(
                user_id=user_id,
                session_id=session_id,
                status=AuthenticationStatus.FAILED,
                methods_used=[],
                risk_score=1.0,
                expires_at=datetime.now(timezone.utc),
            )

    async def _assess_authentication_risk(
        self, user_id: str, request_context: Dict[str, Any]
    ) -> float:
        """Assess authentication risk based on context."""
        risk_score = 0.0
        ip_address = request_context.get("ip_address", "")
        if self._is_suspicious_ip(ip_address):
            risk_score += 0.3
        location = request_context.get("location", {})
        if self._is_unusual_location(user_id, location):
            risk_score += 0.2
        device_fingerprint = request_context.get("device_fingerprint", "")
        if self._is_new_device(user_id, device_fingerprint):
            risk_score += 0.2
        if self._is_unusual_time(user_id):
            risk_score += 0.1
        if user_id in self._failed_attempts:
            attempts = len(self._failed_attempts[user_id])
            risk_score += min(attempts * 0.1, 0.3)
        return min(risk_score, 1.0)

    def _determine_required_auth_methods(
        self, user_id: str, risk_score: float
    ) -> List[AuthenticationMethod]:
        """Determine required authentication methods based on risk."""
        methods = [AuthenticationMethod.PASSWORD]
        if risk_score >= 0.7:
            methods.extend([AuthenticationMethod.TOTP, AuthenticationMethod.SMS])
        elif risk_score >= 0.4:
            methods.append(AuthenticationMethod.TOTP)
        elif risk_score >= 0.2:
            if self._has_totp_enabled(user_id):
                methods.append(AuthenticationMethod.TOTP)
        return methods

    async def _validate_password(self, user_id: str, password: str) -> bool:
        """Validate user password."""
        stored_hash = self._user_credentials.get(user_id, {}).get("password_hash", "")
        if not stored_hash:
            return False
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        return password_hash == stored_hash

    async def _validate_totp(self, user_id: str, totp_code: str) -> bool:
        """Validate TOTP code."""
        secret = self._mfa_secrets.get(user_id, {}).get("totp_secret", "")
        if not secret:
            return False
        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(totp_code, valid_window=1)
        except Exception:
            return False

    async def _validate_sms_code(self, user_id: str, sms_code: str) -> bool:
        """Validate SMS verification code."""
        stored_code = self._mfa_secrets.get(user_id, {}).get("sms_code", "")
        code_timestamp = self._mfa_secrets.get(user_id, {}).get("sms_code_timestamp")
        if not stored_code or not code_timestamp:
            return False
        if datetime.now(timezone.utc) - code_timestamp > timedelta(minutes=5):
            return False
        return sms_code == stored_code

    def _calculate_session_duration(self, risk_score: float) -> timedelta:
        """Calculate session duration based on risk score."""
        base_duration = timedelta(hours=8)
        if risk_score >= 0.7:
            return timedelta(minutes=30)
        elif risk_score >= 0.4:
            return timedelta(hours=2)
        else:
            return base_duration

    async def _record_failed_attempt(self, user_id: str):
        """Record failed authentication attempt."""
        if user_id not in self._failed_attempts:
            self._failed_attempts[user_id] = []
        self._failed_attempts[user_id].append(datetime.now(timezone.utc))
        cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
        self._failed_attempts[user_id] = [
            attempt for attempt in self._failed_attempts[user_id] if attempt > cutoff
        ]
        if len(self._failed_attempts[user_id]) >= 5:
            await self._lock_account(user_id, timedelta(minutes=30))

    async def _lock_account(self, user_id: str, duration: timedelta):
        """Lock user account for specified duration."""
        self._locked_accounts[user_id] = {
            "locked_at": datetime.now(timezone.utc),
            "expires_at": datetime.now(timezone.utc) + duration,
            "reason": "Multiple failed authentication attempts",
        }
        self.logger.warning(f"Account locked: {user_id}")

    def _is_account_locked(self, user_id: str) -> bool:
        """Check if account is currently locked."""
        if user_id not in self._locked_accounts:
            return False
        lock_info = self._locked_accounts[user_id]
        if datetime.now(timezone.utc) > lock_info["expires_at"]:
            del self._locked_accounts[user_id]
            return False
        return True

    def _is_suspicious_ip(self, ip_address: str) -> bool:
        """Check if IP address is suspicious."""
        suspicious_ips = ["192.168.1.100", "10.0.0.50"]
        return ip_address in suspicious_ips

    def _is_unusual_location(self, user_id: str, location: Dict[str, Any]) -> bool:
        """Check if location is unusual for user."""
        return False

    def _is_new_device(self, user_id: str, device_fingerprint: str) -> bool:
        """Check if device is new for user."""
        return device_fingerprint not in ["known_device_1", "known_device_2"]

    def _is_unusual_time(self, user_id: str) -> bool:
        """Check if current time is unusual for user."""
        current_hour = datetime.now(timezone.utc).hour
        return current_hour < 6 or current_hour > 22

    def _has_totp_enabled(self, user_id: str) -> bool:
        """Check if user has TOTP enabled."""
        return (
            user_id in self._mfa_secrets and "totp_secret" in self._mfa_secrets[user_id]
        )

    async def setup_totp(self, user_id: str) -> Dict[str, Any]:
        """Set up TOTP for a user."""
        secret = pyotp.random_base32()
        if user_id not in self._mfa_secrets:
            self._mfa_secrets[user_id] = {}
        self._mfa_secrets[user_id]["totp_secret"] = secret
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=user_id, issuer_name="Flowlet Financial"
        )
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        qr_code_data = base64.b64encode(buffer.getvalue()).decode()
        return {
            "secret": secret,
            "qr_code": qr_code_data,
            "provisioning_uri": provisioning_uri,
        }

    async def send_sms_code(self, user_id: str, phone_number: str) -> bool:
        """Send SMS verification code."""
        code = f"{secrets.randbelow(1000000):06d}"
        if user_id not in self._mfa_secrets:
            self._mfa_secrets[user_id] = {}
        self._mfa_secrets[user_id]["sms_code"] = code
        self._mfa_secrets[user_id]["sms_code_timestamp"] = datetime.now(timezone.utc)
        self.logger.info(f"SMS code sent to {phone_number}: {code}")
        return True

    def validate_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Validate and return session information."""
        if session_id not in self._active_sessions:
            return None
        session = self._active_sessions[session_id]
        if datetime.now(timezone.utc) > session["expires_at"]:
            del self._active_sessions[session_id]
            return None
        session["last_activity"] = datetime.now(timezone.utc)
        return session

    def logout_session(self, session_id: str) -> bool:
        """Logout and invalidate session."""
        if session_id in self._active_sessions:
            del self._active_sessions[session_id]
            return True
        return False

    def logout_all_sessions(self, user_id: str) -> int:
        """Logout all sessions for a user."""
        sessions_to_remove = [
            sid
            for sid, session in self._active_sessions.items()
            if session["user_id"] == user_id
        ]
        for session_id in sessions_to_remove:
            del self._active_sessions[session_id]
        return len(sessions_to_remove)

    def get_active_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """Get active sessions for a user."""
        user_sessions = []
        for session_id, session in self._active_sessions.items():
            if session["user_id"] == user_id:
                user_sessions.append(
                    {
                        "session_id": session_id,
                        "created_at": session["created_at"].isoformat(),
                        "expires_at": session["expires_at"].isoformat(),
                        "last_activity": session["last_activity"].isoformat(),
                        "risk_score": session["risk_score"],
                    }
                )
        return user_sessions

    def get_authentication_statistics(self) -> Dict[str, Any]:
        """Get authentication service statistics."""
        return {
            "active_sessions": len(self._active_sessions),
            "locked_accounts": len(self._locked_accounts),
            "users_with_totp": len(
                [u for u in self._mfa_secrets.values() if "totp_secret" in u]
            ),
            "users_with_failed_attempts": len(self._failed_attempts),
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
