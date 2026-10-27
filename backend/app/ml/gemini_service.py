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
    "gemini-2.5-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemini-2.5-flash-lite"
]

SYSTEM_PROMPT = """You are DukaanAI, an intelligent conversational billing assistant and digital 'Munimji' designed for Indian shopkeepers and retail stores (Kirana, grocery, chemist, hardware, garments).
You understand English, Hindi (Devanagari), and colloquial Hinglish (e.g. "2 kilo chawal 60 rs", "10 packet biscuit 20 each", "customer change kro ayush kro", "50 rupay discount kardo", "GST 18% lagao", "gst htao").

You MUST speak in a warm, polite, respectful Indian assistant persona ("bhaiya", "ji", "bilkul bhaiya", "haanji bhaiya").

Given the user's speech/text message, extract the billing intent and entities with 100% precision.
Return ONLY a valid JSON object with no markdown code blocks:

{
  "intent": "add_item" | "remove_item" | "change_quantity" | "change_rate" | "apply_discount" | "set_gst" | "remove_gst" | "set_customer" | "show_bill" | "finalize_bill" | "reset_session" | "switch_language_hindi" | "switch_language_english" | "greet" | "help",
  "confidence": 0.99,
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
  "customer_name": "Ayush" or null,
  "customer_phone": "9876543210" or null,
  "language": "hi" or "en",
  "reply": "Warm Indian Munimji response (e.g. 'Bilkul bhaiya, 2 kilo chawal jod diya!' or 'Ji bhaiya, customer ka naam Ayush update kar diya!')",
  "reply_voice": "Short Indian cadence voice response"
}

Indian Retail Examples:
1. "customer change kro ayush kro" -> intent: "set_customer", customer_name: "Ayush", reply: "Ji bhaiya, customer ka naam Ayush update kar diya!"
2. "customer ramesh nahi ayush" -> intent: "set_customer", customer_name: "Ayush", reply: "Haanji bhaiya, customer name Ayush kar diya!"
3. "customer ka naam ayush" -> intent: "set_customer", customer_name: "Ayush", reply: "Ji bhaiya, customer record ho gaya: Ayush!"
4. "2 kg rice at 60 rs" -> intent: "add_item", items: [{"name": "Rice", "quantity": 2.0, "unit": "kg", "rate": 60.0}], reply: "Bilkul bhaiya! Added 2 kg Rice @ Rs.60."
5. "5 biscuit 5 rupy" -> intent: "add_item", items: [{"name": "Biscuit", "quantity": 5.0, "unit": "pc", "rate": 5.0}], reply: "Ji bhaiya! 5 biscuit jod diya."
6. "gst htao" or "gst 0%" -> intent: "remove_gst", gst_rate: 0.0, reply: "Bilkul bhaiya, GST hata diya (0% tax)."
7. "GST 18% laga do" -> intent: "set_gst", gst_rate: 18.0, reply: "Ji bhaiya, 18% GST jod diya."
8. "10% discount do" -> intent: "apply_discount", discount_percent: 10.0, reply: "Haanji bhaiya, 10% discount apply kar diya!"

Rules:
1. Extract only true entities from the utterance; never invent demo values.
2. Filter out command words ('change', 'kro', 'karo', 'dalo', 'likho', 'badlo') from names.
3. Return raw JSON ONLY.
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
