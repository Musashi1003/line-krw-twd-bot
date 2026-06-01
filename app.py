import logging
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

import requests
from flask import Flask, abort, jsonify, request

from core import parse_amount, verify_line_signature


LINE_REPLY_API = "https://api.line.me/v2/bot/message/reply"
BASE_CURRENCY = os.getenv("BASE_CURRENCY", "KRW").upper()
TARGET_CURRENCY = os.getenv("TARGET_CURRENCY", "TWD").upper()
FX_API_URL_TEMPLATE = os.getenv(
    "FX_API_URL_TEMPLATE", "https://open.er-api.com/v6/latest/{base}"
)
ALLOWED_GROUP_ID = os.getenv("ALLOWED_GROUP_ID", "").strip()

app = Flask(__name__)
logger = logging.getLogger(__name__)


def fetch_exchange_rate(base_currency: str, target_currency: str) -> tuple[Decimal, str]:
    url = FX_API_URL_TEMPLATE.format(base=base_currency)
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    rates = data.get("rates") or {}
    rate = rates.get(target_currency)
    if rate is None:
        raise ValueError(f"Currency {target_currency} not found in FX response")

    updated_at = (
        data.get("time_last_update_utc")
        or data.get("time_last_update_unix")
        or datetime.now(timezone.utc).isoformat()
    )
    return Decimal(str(rate)), str(updated_at)


def format_decimal(value: Decimal, places: str) -> str:
    quantized = value.quantize(Decimal(places), rounding=ROUND_HALF_UP)
    return f"{quantized:,}"


def build_reply_message(amount_krw: Decimal) -> str:
    rate, updated_at = fetch_exchange_rate(BASE_CURRENCY, TARGET_CURRENCY)
    converted = amount_krw * rate

    return (
        f"韓幣轉台幣\n"
        f"{format_decimal(amount_krw, '1')} {BASE_CURRENCY} = "
        f"{format_decimal(converted, '0.01')} {TARGET_CURRENCY}\n"
        f"參考匯率: 1 {BASE_CURRENCY} = {format_decimal(rate, '0.0001')} {TARGET_CURRENCY}\n"
        f"更新時間: {updated_at}"
    )


def build_flex_message(amount_krw: Decimal) -> dict:
    rate, updated_at = fetch_exchange_rate(BASE_CURRENCY, TARGET_CURRENCY)
    converted = amount_krw * rate
    amount_text = format_decimal(amount_krw, "1")
    converted_text = format_decimal(converted, "0.01")
    rate_text = format_decimal(rate, "0.0001")

    return {
        "type": "flex",
        "altText": (
            f"韓幣轉台幣: {amount_text} {BASE_CURRENCY} = "
            f"{converted_text} {TARGET_CURRENCY}"
        ),
        "contents": {
            "type": "bubble",
            "size": "mega",
            "header": {
                "type": "box",
                "layout": "vertical",
                "paddingAll": "20px",
                "backgroundColor": "#0B6E4F",
                "contents": [
                    {
                        "type": "text",
                        "text": "KRW -> TWD",
                        "color": "#DDF4E7",
                        "size": "sm",
                        "weight": "bold",
                    },
                    {
                        "type": "text",
                        "text": "韓幣轉台幣",
                        "color": "#FFFFFF",
                        "size": "xl",
                        "weight": "bold",
                        "margin": "md",
                    },
                ],
            },
            "body": {
                "type": "box",
                "layout": "vertical",
                "spacing": "lg",
                "paddingAll": "20px",
                "backgroundColor": "#F7FBF8",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "cornerRadius": "16px",
                        "paddingAll": "16px",
                        "backgroundColor": "#FFFFFF",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"{amount_text} {BASE_CURRENCY}",
                                "size": "md",
                                "color": "#5C6B73",
                            },
                            {
                                "type": "text",
                                "text": f"{converted_text} {TARGET_CURRENCY}",
                                "size": "xxl",
                                "weight": "bold",
                                "color": "#0B6E4F",
                                "margin": "sm",
                            },
                        ],
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "spacing": "md",
                        "contents": [
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "參考匯率",
                                        "size": "sm",
                                        "color": "#5C6B73",
                                        "flex": 3,
                                    },
                                    {
                                        "type": "text",
                                        "text": f"1 {BASE_CURRENCY} = {rate_text} {TARGET_CURRENCY}",
                                        "size": "sm",
                                        "color": "#111111",
                                        "align": "end",
                                        "wrap": True,
                                        "flex": 7,
                                    },
                                ],
                            },
                            {
                                "type": "box",
                                "layout": "baseline",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "更新時間",
                                        "size": "sm",
                                        "color": "#5C6B73",
                                        "flex": 3,
                                    },
                                    {
                                        "type": "text",
                                        "text": updated_at,
                                        "size": "sm",
                                        "color": "#111111",
                                        "align": "end",
                                        "wrap": True,
                                        "flex": 7,
                                    },
                                ],
                            },
                        ],
                    },
                ],
            },
            "footer": {
                "type": "box",
                "layout": "vertical",
                "spacing": "sm",
                "paddingAll": "16px",
                "contents": [
                    {
                        "type": "button",
                        "style": "primary",
                        "height": "sm",
                        "color": "#0B6E4F",
                        "action": {
                            "type": "message",
                            "label": "換算 10,000 KRW",
                            "text": "10000 krw",
                        },
                    },
                    {
                        "type": "button",
                        "style": "secondary",
                        "height": "sm",
                        "action": {
                            "type": "message",
                            "label": "換算 50,000 KRW",
                            "text": "50000 krw",
                        },
                    },
                ],
            },
        },
    }


def build_help_message() -> dict:
    return {
        "type": "text",
        "text": "請輸入韓幣金額，例如:\n10000 krw\nkrw 25000",
        "quickReply": {
            "items": [
                {
                    "type": "action",
                    "action": {
                        "type": "message",
                        "label": "10,000 KRW",
                        "text": "10000 krw",
                    },
                },
                {
                    "type": "action",
                    "action": {
                        "type": "message",
                        "label": "50,000 KRW",
                        "text": "50000 krw",
                    },
                },
            ]
        },
    }


def send_line_reply(reply_token: str, messages: list[dict]) -> None:
    access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", "").strip()
    if not access_token:
        raise RuntimeError("Missing LINE_CHANNEL_ACCESS_TOKEN")

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "replyToken": reply_token,
        "messages": messages,
    }
    response = requests.post(LINE_REPLY_API, json=payload, headers=headers, timeout=10)
    if not response.ok:
        logger.error(
            "LINE reply failed: status=%s body=%s",
            response.status_code,
            response.text,
        )
    response.raise_for_status()


def is_allowed_source(event: dict) -> bool:
    source = event.get("source") or {}
    source_type = source.get("type")

    if ALLOWED_GROUP_ID:
        return source_type == "group" and source.get("groupId") == ALLOWED_GROUP_ID

    return source_type in {"group", "user", "room"}


@app.get("/health")
def healthcheck():
    return jsonify({"ok": True, "base": BASE_CURRENCY, "target": TARGET_CURRENCY})


@app.post("/callback")
def callback():
    channel_secret = os.getenv("LINE_CHANNEL_SECRET", "").strip()
    signature = request.headers.get("X-Line-Signature", "")
    body = request.get_data()

    if not channel_secret or not verify_line_signature(body, signature, channel_secret):
        logger.warning("Rejected callback due to invalid LINE signature")
        abort(400, description="Invalid LINE signature")

    payload = request.get_json(silent=True) or {}
    events = payload.get("events") or []

    for event in events:
        if event.get("type") != "message":
            continue
        if event.get("message", {}).get("type") != "text":
            continue
        if not is_allowed_source(event):
            source = event.get("source") or {}
            logger.info(
                "Ignored event from source_type=%s group_id=%s user_id=%s",
                source.get("type"),
                source.get("groupId"),
                source.get("userId"),
            )
            continue

        text = event.get("message", {}).get("text", "")
        reply_token = event.get("replyToken")
        amount = parse_amount(text)

        if not reply_token:
            continue

        if amount is None:
            try:
                send_line_reply(reply_token, [build_help_message()])
            except Exception:
                logger.exception("Failed to send help message reply")
            continue

        try:
            send_line_reply(reply_token, [build_flex_message(amount)])
        except Exception:
            logger.exception("Failed to build or send FX reply")
            fallback = {
                "type": "text",
                "text": "目前暫時無法取得匯率，請稍後再試。",
            }
            try:
                send_line_reply(reply_token, [fallback])
            except Exception:
                logger.exception("Failed to send fallback reply")

    return "OK"


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port, debug=True)
