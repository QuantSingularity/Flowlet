import math
import re
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Optional

from ..core.exceptions import InvalidTransactionError

_CURRENCY = re.compile(r"^[A-Za-z]{3}$")
MAX_AMOUNT = 1_000_000_000.0
ISO_COUNTRY_CODES = frozenset(
    {
        "AD",
        "AE",
        "AF",
        "AG",
        "AI",
        "AL",
        "AM",
        "AO",
        "AQ",
        "AR",
        "AS",
        "AT",
        "AU",
        "AW",
        "AX",
        "AZ",
        "BA",
        "BB",
        "BD",
        "BE",
        "BF",
        "BG",
        "BH",
        "BI",
        "BJ",
        "BL",
        "BM",
        "BN",
        "BO",
        "BQ",
        "BR",
        "BS",
        "BT",
        "BV",
        "BW",
        "BY",
        "BZ",
        "CA",
        "CC",
        "CD",
        "CF",
        "CG",
        "CH",
        "CI",
        "CK",
        "CL",
        "CM",
        "CN",
        "CO",
        "CR",
        "CU",
        "CV",
        "CW",
        "CX",
        "CY",
        "CZ",
        "DE",
        "DJ",
        "DK",
        "DM",
        "DO",
        "DZ",
        "EC",
        "EE",
        "EG",
        "EH",
        "ER",
        "ES",
        "ET",
        "FI",
        "FJ",
        "FK",
        "FM",
        "FO",
        "FR",
        "GA",
        "GB",
        "GD",
        "GE",
        "GF",
        "GG",
        "GH",
        "GI",
        "GL",
        "GM",
        "GN",
        "GP",
        "GQ",
        "GR",
        "GS",
        "GT",
        "GU",
        "GW",
        "GY",
        "HK",
        "HM",
        "HN",
        "HR",
        "HT",
        "HU",
        "ID",
        "IE",
        "IL",
        "IM",
        "IN",
        "IO",
        "IQ",
        "IR",
        "IS",
        "IT",
        "JE",
        "JM",
        "JO",
        "JP",
        "KE",
        "KG",
        "KH",
        "KI",
        "KM",
        "KN",
        "KP",
        "KR",
        "KW",
        "KY",
        "KZ",
        "LA",
        "LB",
        "LC",
        "LI",
        "LK",
        "LR",
        "LS",
        "LT",
        "LU",
        "LV",
        "LY",
        "MA",
        "MC",
        "MD",
        "ME",
        "MF",
        "MG",
        "MH",
        "MK",
        "ML",
        "MM",
        "MN",
        "MO",
        "MP",
        "MQ",
        "MR",
        "MS",
        "MT",
        "MU",
        "MV",
        "MW",
        "MX",
        "MY",
        "MZ",
        "NA",
        "NC",
        "NE",
        "NF",
        "NG",
        "NI",
        "NL",
        "NO",
        "NP",
        "NR",
        "NU",
        "NZ",
        "OM",
        "PA",
        "PE",
        "PF",
        "PG",
        "PH",
        "PK",
        "PL",
        "PM",
        "PN",
        "PR",
        "PS",
        "PT",
        "PW",
        "PY",
        "QA",
        "RE",
        "RO",
        "RS",
        "RU",
        "RW",
        "SA",
        "SB",
        "SC",
        "SD",
        "SE",
        "SG",
        "SH",
        "SI",
        "SJ",
        "SK",
        "SL",
        "SM",
        "SN",
        "SO",
        "SR",
        "SS",
        "ST",
        "SV",
        "SX",
        "SY",
        "SZ",
        "TC",
        "TD",
        "TF",
        "TG",
        "TH",
        "TJ",
        "TK",
        "TL",
        "TM",
        "TN",
        "TO",
        "TR",
        "TT",
        "TV",
        "TW",
        "TZ",
        "UA",
        "UG",
        "UM",
        "US",
        "UY",
        "UZ",
        "VA",
        "VC",
        "VE",
        "VG",
        "VI",
        "VN",
        "VU",
        "WF",
        "WS",
        "YE",
        "YT",
        "ZA",
        "ZM",
        "ZW",
    }
)


def _parse_amount(value: Any) -> float:
    if value is None or isinstance(value, bool):
        raise InvalidTransactionError("amount is required")
    try:
        number = float(Decimal(str(value)))
    except (InvalidOperation, ValueError, TypeError):
        raise InvalidTransactionError("amount must be numeric")
    if not math.isfinite(number):
        raise InvalidTransactionError("amount must be finite")
    if number < 0:
        raise InvalidTransactionError("amount must be non-negative")
    if number > MAX_AMOUNT:
        raise InvalidTransactionError("amount exceeds supported range")
    return number


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        seconds = float(value)
        if seconds > 1e12:
            seconds = seconds / 1000.0
        try:
            parsed = datetime.fromtimestamp(seconds, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            raise InvalidTransactionError("timestamp is out of range")
    elif isinstance(value, str):
        text = value.strip()
        if text.endswith("Z") or text.endswith("z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            raise InvalidTransactionError("timestamp must be ISO 8601")
    else:
        raise InvalidTransactionError("timestamp has unsupported type")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _clean_text(value: Any, limit: int = 255) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text[:limit]


def _resolve_location(data: Dict[str, Any]) -> Dict[str, Optional[str]]:
    country = _clean_text(data.get("location_country") or data.get("country"), 16)
    city = _clean_text(data.get("location_city") or data.get("city"), 100)
    raw = _clean_text(data.get("location"), 200)
    if raw and not country and not city:
        parts = [part.strip() for part in raw.split(",") if part.strip()]
        if len(parts) == 1 and parts[0].upper() in ISO_COUNTRY_CODES:
            country = parts[0]
        elif parts:
            city = parts[0]
            if len(parts) > 1 and parts[-1].upper() in ISO_COUNTRY_CODES:
                country = parts[-1]
    if country and country.upper() not in ISO_COUNTRY_CODES:
        country = None
    return {
        "location_country": country.upper() if country else None,
        "location_city": city,
        "location_raw": raw,
    }


def normalize_transaction(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise InvalidTransactionError("transaction must be an object")
    amount = _parse_amount(data.get("amount"))
    currency = _clean_text(data.get("currency"), 16) or "USD"
    if not _CURRENCY.match(currency):
        raise InvalidTransactionError("currency must be a 3 letter code")
    timestamp = _parse_timestamp(data.get("timestamp"))
    hour_override = data.get("time_of_day")
    if timestamp is None:
        timestamp = datetime.now(timezone.utc)
        if hour_override is not None:
            try:
                hour = int(hour_override)
            except (TypeError, ValueError):
                raise InvalidTransactionError("time_of_day must be an integer")
            if not 0 <= hour <= 23:
                raise InvalidTransactionError("time_of_day must be between 0 and 23")
            timestamp = timestamp.replace(hour=hour)
    category = _clean_text(data.get("merchant_category"), 64)
    if category:
        category = re.sub(r"[\s\-]+", "_", category.lower())
    location = _resolve_location(data)
    user_id = _clean_text(data.get("user_id"), 64) or "anonymous"
    return {
        "transaction_id": _clean_text(data.get("transaction_id"), 64)
        or str(uuid.uuid4()),
        "user_id": user_id,
        "amount": amount,
        "currency": currency.upper(),
        "timestamp": timestamp,
        "merchant_category": category,
        "device_fingerprint": _clean_text(data.get("device_fingerprint"), 255),
        "ip_address": _clean_text(data.get("ip_address"), 45),
        "payment_method": _clean_text(data.get("payment_method"), 32),
        "channel": _clean_text(data.get("channel"), 32),
        "card_id": _clean_text(data.get("card_id"), 64),
        "account_id": _clean_text(data.get("account_id"), 64),
        **location,
    }
