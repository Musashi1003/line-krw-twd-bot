import base64
import hashlib
import hmac
import unittest
from decimal import Decimal
from unittest.mock import patch

from app import build_flex_message
from core import parse_amount, parse_conversion_request, verify_line_signature


class AppTests(unittest.TestCase):
    def test_parse_amount_accepts_basic_inputs(self):
        self.assertEqual(str(parse_amount("10000 krw")), "10000")
        self.assertEqual(str(parse_amount("krw 25,000")), "25000")
        self.assertEqual(str(parse_amount("1000 twd")), "1000")
        self.assertEqual(str(parse_amount("1500")), "1500")

    def test_parse_conversion_request_detects_currency(self):
        self.assertEqual(parse_conversion_request("10000 krw"), (Decimal("10000"), "KRW"))
        self.assertEqual(parse_conversion_request("twd 2500"), (Decimal("2500"), "TWD"))
        self.assertEqual(parse_conversion_request("1500"), (Decimal("1500"), "KRW"))
    def test_parse_amount_rejects_invalid_inputs(self):
        self.assertIsNone(parse_amount("hello"))
        self.assertIsNone(parse_amount("-100 krw"))
        self.assertIsNone(parse_amount("0"))

    def test_verify_line_signature(self):
        secret = "secret123"
        body = b'{"events":[]}'
        digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
        signature = base64.b64encode(digest).decode("utf-8")
        self.assertTrue(verify_line_signature(body, signature, secret))
    def test_build_flex_message_contains_expected_shape(self):
        with patch(
            "app.fetch_exchange_rate",
            return_value=(Decimal("0.0229"), "2026-04-15 10:00:00 UTC"),
        ):
            message = build_flex_message(Decimal("10000"), "KRW")

        self.assertEqual(message["type"], "flex")
        self.assertEqual(message["contents"]["type"], "bubble")
        self.assertIn("韓幣轉台幣", message["altText"])
        self.assertEqual(
            message["contents"]["footer"]["contents"][0]["action"]["text"],
            "10000 krw",
        )

    def test_build_flex_message_supports_twd_to_krw(self):
        with patch(
            "app.fetch_exchange_rate",
            return_value=(Decimal("44.25"), "2026-04-15 10:00:00 UTC"),
        ):
            message = build_flex_message(Decimal("1000"), "TWD")

        self.assertIn("台幣轉韓幣", message["altText"])
        self.assertEqual(
            message["contents"]["footer"]["contents"][0]["action"]["text"],
            "1000 twd",
        )


if __name__ == "__main__":
    unittest.main()
