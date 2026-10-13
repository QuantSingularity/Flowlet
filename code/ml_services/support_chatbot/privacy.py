import re
from typing import Tuple

_PATTERNS = [
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "[card]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[ssn]"),
    (re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "[email]"),
    (re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b"), "[iban]"),
    (re.compile(r"(?<!\d)\+?\d[\d\s().-]{8,}\d(?!\d)"), "[phone]"),
]


def redact_pii(text: str) -> Tuple[str, int]:
    count = 0
    for pattern, token in _PATTERNS:
        text, replaced = pattern.subn(token, text)
        count += replaced
    return text, count
