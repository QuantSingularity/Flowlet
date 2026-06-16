import html
import ipaddress
import json
import logging
import os
import re
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Union

try:
    import phonenumbers
    from phonenumbers import NumberParseException

    PHONENUMBERS_AVAILABLE = True
except ImportError:
    phonenumbers = None
    NumberParseException = Exception
    PHONENUMBERS_AVAILABLE = False

try:
    from email_validator import EmailNotValidError, validate_email

    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EmailNotValidError = Exception

    def validate_email(email, **kw):
        raise Exception("email_validator not installed")

    EMAIL_VALIDATOR_AVAILABLE = False

"\nInput Validation and Sanitization System\n"
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom validation error"""

    def __init__(self, message: str, field: str = None, code: str = None) -> None:
        self.message = message
        self.field = field
        self.code = code
        super().__init__(message)


class InputValidator:
    """Comprehensive input validation and sanitization"""

    def __init__(self) -> None:
        self.patterns = {
            "alphanumeric": re.compile("^[a-zA-Z0-9]+$"),
            "alpha": re.compile("^[a-zA-Z]+$"),
            "numeric": re.compile("^[0-9]+$"),
            "uuid": re.compile(
                "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
                re.IGNORECASE,
            ),
            "card_number": re.compile("^[0-9]{13,19}$"),
            "cvv": re.compile("^[0-9]{3,4}$"),
            "pin": re.compile("^[0-9]{4}$"),
            "routing_number": re.compile("^[0-9]{9}$"),
            "swift_code": re.compile("^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$"),
            "iban": re.compile(
                "^[A-Z]{2}[0-9]{2}[A-Z0-9]{4}[0-9]{7}([A-Z0-9]?){0,16}$"
            ),
            "ssn": re.compile("^[0-9]{3}-[0-9]{2}-[0-9]{4}$"),
            "ein": re.compile("^[0-9]{2}-[0-9]{7}$"),
            "ip_address": re.compile("^(?:[0-9]{1,3}\\.){3}[0-9]{1,3}$"),
            "url": re.compile(
                "^https?://(?:[-\\w.])+(?:[:\\d]+)?(?:/(?:[\\w/_.])*(?:\\?(?:[\\w&=%.])*)?(?:#(?:\\w*))?)?$"
            ),
            "base64": re.compile("^[A-Za-z0-9+/]*={0,2}$"),
            "hex": re.compile("^[0-9a-fA-F]+$"),
            "currency_code": re.compile("^[A-Z]{3}$"),
            "country_code": re.compile("^[A-Z]{2}$"),
            "postal_code_us": re.compile("^[0-9]{5}(-[0-9]{4})?$"),
            "postal_code_ca": re.compile("^[A-Z][0-9][A-Z] [0-9][A-Z][0-9]$"),
            "postal_code_uk": re.compile("^[A-Z]{1,2}[0-9R][0-9A-Z]? [0-9][A-Z]{2}$"),
        }
        self.dangerous_patterns = [
            re.compile("<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
            re.compile("javascript:", re.IGNORECASE),
            re.compile("on\\w+\\s*=", re.IGNORECASE),
            re.compile("<iframe[^>]*>.*?</iframe>", re.IGNORECASE | re.DOTALL),
            re.compile("<object[^>]*>.*?</object>", re.IGNORECASE | re.DOTALL),
            re.compile("<embed[^>]*>", re.IGNORECASE),
            re.compile("<link[^>]*>", re.IGNORECASE),
            re.compile("<meta[^>]*>", re.IGNORECASE),
            re.compile("<style[^>]*>.*?</style>", re.IGNORECASE | re.DOTALL),
            re.compile("expression\\s*\\(", re.IGNORECASE),
            re.compile("url\\s*\\(", re.IGNORECASE),
            re.compile("@import", re.IGNORECASE),
            re.compile("vbscript:", re.IGNORECASE),
            re.compile("data:", re.IGNORECASE),
        ]
        self.sql_patterns = [
            re.compile(
                "(\\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\\b)",
                re.IGNORECASE,
            ),
            re.compile("(\\b(OR|AND)\\s+\\d+\\s*=\\s*\\d+)", re.IGNORECASE),
            re.compile(
                "(\\b(OR|AND)\\s+[\\'\"]?\\w+[\\'\"]?\\s*=\\s*[\\'\"]?\\w+[\\'\"]?)",
                re.IGNORECASE,
            ),
            re.compile("(--|#|/\\*|\\*/)", re.IGNORECASE),
            re.compile("(\\bUNION\\b.*\\bSELECT\\b)", re.IGNORECASE),
            re.compile("(\\b(EXEC|EXECUTE)\\b)", re.IGNORECASE),
        ]

    def sanitize_string(
        self, value: str, max_length: int = None, allow_html: bool = False
    ) -> str:
        """Sanitize string input"""
        if not isinstance(value, str):
            raise ValidationError("Value must be a string", code="INVALID_TYPE")
        value = value.replace("\x00", "")
        value = value.strip()
        if max_length and len(value) > max_length:
            raise ValidationError(
                f"String too long (max {max_length} characters)", code="STRING_TOO_LONG"
            )
        if not allow_html:
            value = html.escape(value)
        if not allow_html:
            for pattern in self.dangerous_patterns:
                if pattern.search(value):
                    raise ValidationError(
                        "Potentially dangerous content detected",
                        code="DANGEROUS_CONTENT",
                    )
        for pattern in self.sql_patterns:
            if pattern.search(value):
                raise ValidationError(
                    "Potentially malicious SQL content detected", code="SQL_INJECTION"
                )
        return value

    def validate_phone(self, phone: str, country_code: str = None) -> str:
        """Validate and format phone number"""
        if not phone:
            raise ValidationError(
                "Phone number is required", field="phone", code="PHONE_REQUIRED"
            )
        try:
            parsed_number = phonenumbers.parse(phone, country_code)
            if not phonenumbers.is_valid_number(parsed_number):
                raise ValidationError(
                    "Invalid phone number", field="phone", code="INVALID_PHONE"
                )
            return phonenumbers.format_number(
                parsed_number, phonenumbers.PhoneNumberFormat.E164
            )
        except NumberParseException as e:
            raise ValidationError(
                f"Invalid phone number format: {str(e)}",
                field="phone",
                code="INVALID_PHONE_FORMAT",
            )

    def validate_uuid(self, uuid_str: str) -> str:
        """Validate UUID format"""
        if not uuid_str:
            raise ValidationError("UUID is required", code="UUID_REQUIRED")
        uuid_str = uuid_str.strip().lower()
        if not self.patterns["uuid"].match(uuid_str):
            raise ValidationError("Invalid UUID format", code="INVALID_UUID")
        return uuid_str

    def _validate_luhn(self, card_number: str) -> bool:
        """Validate card number using Luhn algorithm"""
        digits = [int(d) for d in card_number]
        for i in range(len(digits) - 2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        return sum(digits) % 10 == 0

    def validate_cvv(self, cvv: str) -> str:
        """Validate CVV"""
        if not cvv:
            raise ValidationError("CVV is required", field="cvv", code="CVV_REQUIRED")
        cvv = cvv.strip()
        if not self.patterns["cvv"].match(cvv):
            raise ValidationError("Invalid CVV format", field="cvv", code="INVALID_CVV")
        return cvv

    def validate_pin(self, pin: str) -> str:
        """Validate PIN"""
        if not pin:
            raise ValidationError("PIN is required", field="pin", code="PIN_REQUIRED")
        pin = pin.strip()
        if not self.patterns["pin"].match(pin):
            raise ValidationError(
                "PIN must be exactly 4 digits", field="pin", code="INVALID_PIN"
            )
        if self._is_weak_pin(pin):
            raise ValidationError("PIN is too weak", field="pin", code="WEAK_PIN")
        return pin

    def _is_weak_pin(self, pin: str) -> bool:
        """Check if PIN is weak"""
        weak_pins = [
            "0000",
            "1111",
            "2222",
            "3333",
            "4444",
            "5555",
            "6666",
            "7777",
            "8888",
            "9999",
            "1234",
            "4321",
            "1122",
            "2211",
            "1212",
            "2121",
            "0123",
            "3210",
        ]
        return pin in weak_pins

    def validate_amount(
        self,
        amount: Union[str, int, float, Decimal],
        min_amount: Decimal = None,
        max_amount: Decimal = None,
        currency: str = "USD",
    ) -> Decimal:
        """Validate monetary amount"""
        if amount is None:
            raise ValidationError(
                "Amount is required", field="amount", code="AMOUNT_REQUIRED"
            )
        try:
            if isinstance(amount, str):
                amount = amount.strip()
                amount = re.sub("[^\\d.-]", "", amount)
            decimal_amount = Decimal(str(amount))
        except (InvalidOperation, ValueError):
            raise ValidationError(
                "Invalid amount format", field="amount", code="INVALID_AMOUNT"
            )
        if decimal_amount < 0:
            raise ValidationError(
                "Amount cannot be negative", field="amount", code="NEGATIVE_AMOUNT"
            )
        if decimal_amount.as_tuple().exponent < -2:
            raise ValidationError(
                "Amount has too many decimal places",
                field="amount",
                code="INVALID_PRECISION",
            )
        if min_amount is not None and decimal_amount < min_amount:
            raise ValidationError(
                f"Amount must be at least {min_amount}",
                field="amount",
                code="AMOUNT_TOO_LOW",
            )
        if max_amount is not None and decimal_amount > max_amount:
            raise ValidationError(
                f"Amount cannot exceed {max_amount}",
                field="amount",
                code="AMOUNT_TOO_HIGH",
            )
        return decimal_amount

    def validate_country_code(self, country: str) -> str:
        """Validate ISO 3166-1 alpha-2 country code"""
        if not country:
            raise ValidationError(
                "Country code is required", field="country", code="COUNTRY_REQUIRED"
            )
        country = country.strip().upper()
        if not self.patterns["country_code"].match(country):
            raise ValidationError(
                "Invalid country code format", field="country", code="INVALID_COUNTRY"
            )
        valid_countries = {
            "US",
            "CA",
            "GB",
            "DE",
            "FR",
            "IT",
            "ES",
            "NL",
            "BE",
            "CH",
            "AT",
            "SE",
            "NO",
            "DK",
            "FI",
            "IE",
            "PT",
            "GR",
            "PL",
            "CZ",
            "HU",
            "SK",
            "SI",
            "EE",
            "LV",
            "LT",
            "LU",
            "MT",
            "CY",
            "BG",
            "RO",
            "HR",
            "AU",
            "NZ",
            "JP",
            "KR",
            "SG",
            "HK",
            "IN",
            "CN",
            "BR",
            "MX",
            "AR",
            "CL",
            "CO",
            "PE",
            "ZA",
            "NG",
            "EG",
            "MA",
            "KE",
            "GH",
            "TN",
            "AE",
            "SA",
            "IL",
            "TR",
            "RU",
            "UA",
            "BY",
            "KZ",
            "UZ",
            "TH",
            "VN",
            "MY",
            "ID",
            "PH",
            "TW",
            "BD",
            "PK",
        }
        if country not in valid_countries:
            raise ValidationError(
                f"Unsupported country code: {country}",
                field="country",
                code="UNSUPPORTED_COUNTRY",
            )
        return country

    def validate_date(self, date_str: str, date_format: str = "%Y-%m-%d") -> date:
        """Validate date string"""
        if not date_str:
            raise ValidationError(
                "Date is required", field="date", code="DATE_REQUIRED"
            )
        try:
            parsed_date = datetime.strptime(date_str.strip(), date_format).date()
            return parsed_date
        except ValueError as e:
            raise ValidationError(
                f"Invalid date format: {str(e)}", field="date", code="INVALID_DATE"
            )

    def validate_datetime(
        self, datetime_str: str, datetime_format: str = "%Y-%m-%d %H:%M:%S"
    ) -> datetime:
        """Validate datetime string"""
        if not datetime_str:
            raise ValidationError(
                "Datetime is required", field="datetime", code="DATETIME_REQUIRED"
            )
        try:
            parsed_datetime = datetime.strptime(datetime_str.strip(), datetime_format)
            return parsed_datetime
        except ValueError as e:
            raise ValidationError(
                f"Invalid datetime format: {str(e)}",
                field="datetime",
                code="INVALID_DATETIME",
            )

    def validate_ip_address(self, ip: str) -> str:
        """Validate IP address"""
        if not ip:
            raise ValidationError(
                "IP address is required", field="ip", code="IP_REQUIRED"
            )
        ip = ip.strip()
        try:
            ip_obj = ipaddress.ip_address(ip)
            return str(ip_obj)
        except ValueError:
            raise ValidationError(
                "Invalid IP address format", field="ip", code="INVALID_IP"
            )

    def validate_url(self, url: str, allowed_schemes: List[str] = None) -> str:
        """Validate URL"""
        if not url:
            raise ValidationError("URL is required", field="url", code="URL_REQUIRED")
        url = url.strip()
        if not self.patterns["url"].match(url):
            raise ValidationError("Invalid URL format", field="url", code="INVALID_URL")
        if allowed_schemes:
            scheme = url.split("://")[0].lower()
            if scheme not in allowed_schemes:
                raise ValidationError(
                    f"URL scheme not allowed: {scheme}",
                    field="url",
                    code="INVALID_URL_SCHEME",
                )
        return url

    def validate_json(self, json_str: str) -> dict:
        """Validate JSON string"""
        if not json_str:
            raise ValidationError(
                "JSON is required", field="json", code="JSON_REQUIRED"
            )
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValidationError(
                f"Invalid JSON format: {str(e)}", field="json", code="INVALID_JSON"
            )

    def validate_base64(self, base64_str: str) -> str:
        """Validate base64 string"""
        if not base64_str:
            raise ValidationError(
                "Base64 string is required", field="base64", code="BASE64_REQUIRED"
            )
        base64_str = base64_str.strip()
        if not self.patterns["base64"].match(base64_str):
            raise ValidationError(
                "Invalid base64 format", field="base64", code="INVALID_BASE64"
            )
        try:
            import base64

            base64.b64decode(base64_str, validate=True)
            return base64_str
        except Exception:
            raise ValidationError(
                "Invalid base64 encoding",
                field="base64",
                code="INVALID_BASE64_ENCODING",
            )

    def validate_activation_code(self, code: str) -> bool:
        """Validate activation code format"""
        if not code:
            return False
        code = code.strip().upper()
        if len(code) < 8 or len(code) > 12:
            return False
        return self.patterns["alphanumeric"].match(code) is not None

    def validate_routing_number(self, routing_number: str) -> str:
        """Validate US bank routing number"""
        if not routing_number:
            raise ValidationError(
                "Routing number is required",
                field="routing_number",
                code="ROUTING_NUMBER_REQUIRED",
            )
        routing_number = routing_number.strip()
        if not self.patterns["routing_number"].match(routing_number):
            raise ValidationError(
                "Invalid routing number format",
                field="routing_number",
                code="INVALID_ROUTING_NUMBER",
            )
        if not self._validate_routing_checksum(routing_number):
            raise ValidationError(
                "Invalid routing number checksum",
                field="routing_number",
                code="INVALID_ROUTING_CHECKSUM",
            )
        return routing_number

    def _validate_routing_checksum(self, routing_number: str) -> bool:
        """Validate routing number checksum"""
        weights = [3, 7, 1, 3, 7, 1, 3, 7, 1]
        total = sum(
            (int(digit) * weight for digit, weight in zip(routing_number, weights))
        )
        return total % 10 == 0

    def validate_swift_code(self, swift_code: str) -> str:
        """Validate SWIFT/BIC code"""
        if not swift_code:
            raise ValidationError(
                "SWIFT code is required", field="swift_code", code="SWIFT_CODE_REQUIRED"
            )
        swift_code = swift_code.strip().upper()
        if not self.patterns["swift_code"].match(swift_code):
            raise ValidationError(
                "Invalid SWIFT code format",
                field="swift_code",
                code="INVALID_SWIFT_CODE",
            )
        return swift_code

    def validate_iban(self, iban: str) -> str:
        """Validate IBAN"""
        if not iban:
            raise ValidationError(
                "IBAN is required", field="iban", code="IBAN_REQUIRED"
            )
        iban = iban.strip().upper().replace(" ", "")
        if not self.patterns["iban"].match(iban):
            raise ValidationError(
                "Invalid IBAN format", field="iban", code="INVALID_IBAN"
            )
        if not self._validate_iban_checksum(iban):
            raise ValidationError(
                "Invalid IBAN checksum", field="iban", code="INVALID_IBAN_CHECKSUM"
            )
        return iban

    def _validate_iban_checksum(self, iban: str) -> bool:
        """Validate IBAN checksum using mod-97 algorithm"""
        rearranged = iban[4:] + iban[:4]
        numeric_string = ""
        for char in rearranged:
            if char.isalpha():
                numeric_string += str(ord(char) - ord("A") + 10)
            else:
                numeric_string += char
        return int(numeric_string) % 97 == 1

    def sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        if not filename:
            raise ValidationError(
                "Filename is required", field="filename", code="FILENAME_REQUIRED"
            )
        filename = re.sub('[<>:"/\\\\|?*\\x00-\\x1f]', "", filename)
        filename = filename.strip(". ")
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[: 255 - len(ext)] + ext
        if not filename:
            raise ValidationError(
                "Invalid filename", field="filename", code="INVALID_FILENAME"
            )
        return filename

    def validate_password_complexity(self, password: str) -> Dict[str, Any]:
        """Validate password complexity"""
        if not password:
            raise ValidationError(
                "Password is required", field="password", code="PASSWORD_REQUIRED"
            )
        errors = []
        score = 0
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        elif len(password) >= 12:
            score += 2
        else:
            score += 1
        if re.search("[a-z]", password):
            score += 1
        else:
            errors.append("Password must contain at least one lowercase letter")
        if re.search("[A-Z]", password):
            score += 1
        else:
            errors.append("Password must contain at least one uppercase letter")
        if re.search("[0-9]", password):
            score += 1
        else:
            errors.append("Password must contain at least one digit")
        if re.search("[!@#$%^&*()_+\\-=\\[\\]{}|;:,.<>?]", password):
            score += 2
        else:
            errors.append("Password must contain at least one special character")
        common_passwords = ["password", "123456", "qwerty", "abc123", "password123"]
        if password.lower() in common_passwords:
            errors.append("Password is too common")
            score = 0
        if score >= 6:
            strength = "strong"
        elif score >= 4:
            strength = "medium"
        else:
            strength = "weak"
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "strength": strength,
            "score": score,
        }

    @staticmethod
    def validate_string(
        value: str,
        field_name: str,
        min_length: int = 0,
        max_length: int = 255,
        allow_empty: bool = False,
    ) -> str:
        """Validate a string field."""
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} must be a string", field=field_name)
        if not allow_empty and len(value) < max(1, min_length):
            if len(value) == 0:
                raise ValidationError(f"{field_name} cannot be empty", field=field_name)
            raise ValidationError(
                f"{field_name} must be at least {min_length} characters",
                field=field_name,
            )
        if len(value) > max_length:
            raise ValidationError(
                f"{field_name} must be at most {max_length} characters",
                field=field_name,
            )
        return value

    @staticmethod
    def validate_email(email: str, field_name: str = "email") -> str:
        """Validate email address format."""
        if not email or not isinstance(email, str):
            raise ValidationError("Email is required", field=field_name)
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(pattern, email.strip()):
            raise ValidationError("Invalid email format", field=field_name)
        return email.strip().lower()

    @staticmethod
    def validate_decimal(value, field_name: str, min_value=None, max_value=None):
        """Validate a decimal/numeric field."""
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError(
                f"{field_name} must be a valid number", field=field_name
            )
        if min_value is not None and decimal_value < min_value:
            raise ValidationError(
                f"{field_name} must be at least {min_value}", field=field_name
            )
        if max_value is not None and decimal_value > max_value:
            raise ValidationError(
                f"{field_name} must be at most {max_value}", field=field_name
            )
        return decimal_value

    @staticmethod
    def validate_card_number(card_number: str, field_name: str = "card_number") -> str:
        """Validate credit card number using Luhn algorithm."""
        if not card_number or not isinstance(card_number, str):
            raise ValidationError("Card number is required", field=field_name)
        digits = card_number.replace(" ", "").replace("-", "")
        if not digits.isdigit() or not (13 <= len(digits) <= 19):
            raise ValidationError("Invalid card number format", field=field_name)
        total = 0
        for i, d in enumerate(digits[::-1]):
            n = int(d)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        if total % 10 != 0:
            raise ValidationError(
                "Invalid card number (failed Luhn check)", field=field_name
            )
        return digits

    @staticmethod
    def validate_currency_code(currency: str, field_name: str = "currency") -> str:
        """Validate ISO 4217 currency code."""
        if not currency or not isinstance(currency, str):
            raise ValidationError("Currency code is required", field=field_name)
        currency = currency.strip().upper()
        if not re.match(r"^[A-Z]{3}$", currency):
            raise ValidationError(
                "Currency must be a 3-letter ISO 4217 code", field=field_name
            )
        valid_currencies = {
            "USD",
            "EUR",
            "GBP",
            "JPY",
            "CAD",
            "AUD",
            "CHF",
            "CNY",
            "SEK",
            "NZD",
            "MXN",
            "SGD",
            "HKD",
            "NOK",
            "TRY",
            "ZAR",
            "BRL",
            "INR",
            "KRW",
            "PLN",
            "DKK",
            "CZK",
            "HUF",
            "RON",
            "BGN",
            "HRK",
            "ISK",
            "RUB",
            "UAH",
            "AED",
            "SAR",
            "ILS",
            "THB",
            "IDR",
            "MYR",
            "PHP",
            "VND",
            "PKR",
            "BDT",
            "NGN",
            "KES",
            "GHS",
            "ZMW",
            "UGX",
            "TZS",
            "EGP",
            "MAD",
            "TND",
        }
        if currency not in valid_currencies:
            raise ValidationError(
                f"Unsupported currency code: {currency}", field=field_name
            )
        return currency


input_validator = InputValidator()


# ---------------------------------------------------------------------------
# Backward-compatibility helpers used by auth.py (old tuple-returning API)
# ---------------------------------------------------------------------------


def _compat_validate_email(email: str):
    """Return (True, normalized_email) or (False, error_message)."""
    try:
        result = InputValidator.validate_email(email)
        return True, result
    except (ValidationError, Exception) as exc:
        return False, str(exc)


def _compat_validate_password(password: str):
    """Return (True, password) or (False, error_message) with basic complexity rules."""
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>/?]", password):
        return False, "Password must contain at least one special character"
    return True, password


# Patch the class so existing callers work with either the old tuple API or new string API
InputValidator._validate_email_compat = staticmethod(_compat_validate_email)
InputValidator._validate_password_compat = staticmethod(_compat_validate_password)
