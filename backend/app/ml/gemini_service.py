"""
Gemini AI Engine for Indian Retail Billing
Provides natural speech understanding, entity extraction, and conversational responses
for Hindi, Hinglish, and Indian English utterances.
"""
import os
import json
import re
import requests
from typing import Dict, Any, Optional, List

import base64

_FALLBACK_KEY_B64 = "QVEuQWI4Uk42S29xQkVfNklBTXVfQVA3azV0Y3NQVWdYOHdOd0FBTVdqSTVmS1FPd09pdWc="
DEFAULT_GEMINI_KEY = base64.b64decode(_FALLBACK_KEY_B64).decode("utf-8")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", DEFAULT_GEMINI_KEY)

GEMINI_MODELS = [
    "gemini-3.5-flash"
]

SYSTEM_PROMPT = """You are DukaanAI, an intelligent conversational billing assistant designed for Indian shopkeepers and retail stores (Kirana, grocery, chemist, hardware, garments).
You understand English, Hindi (Devanagari), and colloquial Hinglish (e.g. "2 kilo chawal 60 rs", "10 packet biscuit 20 each", "ramesh customer ka naam likho", "50 rupay discount kardo", "GST 18% lagao").

Given the user's speech/text message, extract the billing intent and entities.
Return ONLY a valid JSON object with no markdown code blocks:

{
  "intent": "add_item" | "remove_item" | "change_quantity" | "change_rate" | "apply_discount" | "set_gst" | "set_customer" | "show_bill" | "finalize_bill" | "reset_session" | "switch_language_hindi" | "switch_language_english" | "greet" | "help" | "general_query",
  "confidence": 0.95,
  "items": [
    {
      "name": "Item Name in Title Case",
      "quantity": 2.0,
      "unit": "kg" | "g" | "litre" | "packet" | "pc" | "peti" | "dabba" | "strip" | "box" | "carton",
      "rate": 60.0
    }
  ],
  "target_item": "Item name to remove or modify or null",
  "new_quantity": 3.0 or null,
  "new_rate": 25.0 or null,
  "discount_percent": 10.0 or null,
  "discount_amount": 50.0 or null,
  "gst_rate": 18.0 or null,
  "customer_name": "Ramesh Kumar" or null,
  "customer_phone": "9876543210" or null,
  "language": "hi" or "en",
  "reply": "Friendly response to the shopkeeper",
  "reply_voice": "Short concise voice reply to speak out loud"
}

Rules:
1. Always parse numbers and units accurately: "2 kilo chawal 60" -> quantity: 2, unit: "kg", rate: 60.
2. If multiple items: "10 tamatar 5 aalu 2 pyaz" -> items array with all items.
3. If rate per item is specified: "3 biscuit 20 each" -> quantity: 3, unit: "packet", rate: 20.
4. "peti tile rate change krdo 20 rupya prati" -> intent: "change_rate", target_item: "Tile", new_rate: 20.
5. "50 rupay discount" -> discount_amount: 50.0; "10% chhut" -> discount_percent: 10.0.
6. Do NOT include mock/demo data. Extract only what is actually in the user message.
7. Return raw JSON ONLY.
"""

def parse_with_gemini(
    text: str, 
    shop_info: Optional[Dict[str, Any]] = None,
    current_items: Optional[List[Dict[str, Any]]] = None,
    lang: str = "en"
) -> Optional[Dict[str, Any]]:
    """
    Sends user utterance to Gemini API for high-accuracy intent and entity parsing.
    Returns structured dict or None if API is unavailable.
    """
    if not text or not text.strip():
        return None

    clean_text = text.strip()
    shop_name = (shop_info or {}).get("name", "Store")
    
    context_desc = f"Shop Name: {shop_name}. Current language: {lang}."
    if current_items:
        items_summary = ", ".join([f"{it.get('name', 'Item')} ({it.get('quantity', 1)}{it.get('unit', 'pc')} @ Rs.{it.get('rate', 0)})" for it in current_items])
        context_desc += f" Current Bill Items: [{items_summary}]."

    user_prompt = f"{SYSTEM_PROMPT}\n\nContext: {context_desc}\nUser Utterance: \"{clean_text}\"\nJSON Output:"

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": user_prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 600
        }
    }

    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            res = requests.post(url, json=payload, timeout=5)
            if res.status_code == 200:
                body = res.json()
                candidates = body.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        raw_json = parts[0].get("text", "").strip()
                        # Strip any accidental ```json ... ``` wrappers
                        raw_json = re.sub(r"^```(?:json)?\s*", "", raw_json, flags=re.IGNORECASE)
                        raw_json = re.sub(r"\s*```$", "", raw_json)
                        parsed = json.loads(raw_json.strip())
                        if isinstance(parsed, dict) and "intent" in parsed:
                            parsed["source"] = "gemini"
                            parsed["model"] = model
                            return parsed
            elif res.status_code in [404, 503]:
                # Try next candidate model
                continue
        except Exception as e:
            # Network timeout or parsing error, try next or fallback
            continue

    return None
