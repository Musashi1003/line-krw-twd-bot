import base64
import hashlib
import hmac
import re
from decimal import Decimal, InvalidOperation
from typing import Optional


MESSAGE_PATTERN = re.compile(
    r"^\s*(?:(?P<currency1>krw)\s*)?(?P<amount>[\d,]+(?:\.\d+)?)\s*(?:(?P<currency2>krw)|원|韓元)?\s*$",
    re.IGNORECASE,
)


def verify_line_signature(body: bytes, signature: str, channel_secret: str) -> bool:
    digest = hmac.new(
        channel_secret.encode("utf-8"), body, hashlib.sha256
    ).digest()
    expected_signature = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(expected_signature, signature)


def parse_amount(text: str) -> Optional[Decimal]:
    match = MESSAGE_PATTERN.match(text or "")
    if not match:
        return None

    if not match.group("currency1") and not match.group("currency2"):
        if not any(char.isdigit() for char in text):
            return None

    normalized = match.group("amount").replace(",", "")
    try:
        amount = Decimal(normalized)
    except InvalidOperation:
        return None

    if amount <= 0:
        return None
    return amount
