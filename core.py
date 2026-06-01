import base64
import hashlib
import hmac
import re
from decimal import Decimal, InvalidOperation
from typing import Optional


MESSAGE_PATTERN = re.compile(
    r"^\s*(?:(?P<currency1>krw|twd)\s*)?"
    r"(?P<amount>[\d,]+(?:\.\d+)?)"
    r"\s*(?:(?P<currency2>krw|twd))?\s*$",
    re.IGNORECASE,
)


def verify_line_signature(body: bytes, signature: str, channel_secret: str) -> bool:
    digest = hmac.new(
        channel_secret.encode("utf-8"), body, hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected_signature, signature)


def parse_conversion_request(text: str) -> Optional[tuple[Decimal, str]]:
    match = MESSAGE_PATTERN.match(text or "")
    if not match:
        return None

    currency1 = (match.group("currency1") or "").upper()
    currency2 = (match.group("currency2") or "").upper()

    if currency1 and currency2 and currency1 != currency2:
        return None

    source_currency = currency1 or currency2 or "KRW"

    normalized = match.group("amount").replace(",", "")
    try:
        amount = Decimal(normalized)
    except InvalidOperation:
        return None

    if amount <= 0:
        return None

    return amount, source_currency


def parse_amount(text: str) -> Optional[Decimal]:
    parsed = parse_conversion_request(text)
    if parsed is None:
        return None
    return parsed[0]
