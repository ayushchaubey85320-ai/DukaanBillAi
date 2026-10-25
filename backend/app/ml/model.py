"""
Offline Machine Learning Intent Classification Inference Engine
Loads the trained Calibrated Scikit-Learn Pipeline and provides real-time intent prediction.
"""
import os
import re
import joblib
from typing import Dict, Any, Optional
from backend.app.ml.tokenizer import clean_and_normalize_text

MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "intent_model.joblib")
_MODEL_PIPELINE = None

def get_or_load_model():
    """Singleton loader for the offline intent classification model."""
    global _MODEL_PIPELINE
    if _MODEL_PIPELINE is None:
        if os.path.exists(MODEL_PATH):
            try:
                _MODEL_PIPELINE = joblib.load(MODEL_PATH)
            except Exception as e:
                print(f"Warning: Failed to load model from {MODEL_PATH}: {e}")
                _MODEL_PIPELINE = None
    return _MODEL_PIPELINE

def predict_intent(text: str) -> Dict[str, Any]:
    """
    Predicts intent and confidence score for a given utterance.
    Uses trained ML classifier with deterministic fallback guards.
    """
    cleaned = clean_and_normalize_text(text)
    if not cleaned:
        return {"intent": "fallback", "confidence": 0.0, "clean_text": ""}

    lower_t = cleaned.lower()

    # Priority 1: High-Precision Business Rule Guards
    # Customer Identification / Name / Phone / Correction
    if any(w in lower_t for w in ["customer", "grahak", "client", "buyer"]) or \
       re.search(r'\b[A-Za-z\u0900-\u097F]+\s+(?:nhi|nahi|not|mat)\s+[A-Za-z\u0900-\u097F]+', lower_t) or \
       re.search(r'\b(?:nahi|nhi|not|mat)\s+[A-Za-z\u0900-\u097F]+[,\s]+[A-Za-z\u0900-\u097F]+', lower_t):
        return {"intent": "set_customer", "confidence": 0.99, "clean_text": cleaned}

    # Rate / Price Change / Modification
    # Rate / Price Change / Modification
    # e.g.:
    # - "peti tile rate change krdo 20 rupya prati"
    # - "rice ka rate 20 rupy prati kilo hai"
    # - "biscuit change krke 5 rupya prati peice"
    # - "biscuit ka price change kro 5 rupya per biscuit"
    # - "1 biscuit 5 rupya ka hai"
    # - "rate 25 kar do"
    is_rate_change = (
        any(w in lower_t for w in ["rate change", "price change", "bhav change", "daam change", "rate badlo", "rate badal"]) or
        (any(w in lower_t for w in ["change", "badal", "badlo"]) and any(w in lower_t for w in ["prati", "per", "each", "प्रति", "rate", "price", "bhav", "daam"])) or
        bool(re.search(r'\b(?:rate|bhav|daam|price|रेट|भाव|दर|दाम)\s+.*(?:hai|krdo|karo|kar do|kardena|change|badlo|badal|hoga)', lower_t)) or
        bool(re.search(r'\b[A-Za-z\u0900-\u097F]+\s+ka\s+(?:rate|bhav|daam|price)\s+[0-9]+', lower_t)) or
        bool(re.search(r'\b(?:change|update)\s+.*(?:rate|price|bhav|daam)', lower_t)) or
        bool(re.search(r'\b(?:1|ek)\s+[A-Za-z\u0900-\u097F]+\s+[0-9]+(?:\.[0-9]+)?\s*(?:rupya|rupay|rupy|rupees|rs|रुपये|रुपया)\s*(?:ka\s*hai|hai)', lower_t)) or
        (bool(re.search(r'[0-9]+(?:\.[0-9]+)?\s*(?:rupya|rupay|rupy|rupees|rs|रुपये|रुपया)?\s*(?:prati|per|each|प्रति)\s*(?:piece|peice|pc|packet|kilo|kg|nag)?', lower_t)) and any(w in lower_t for w in ["change", "krdo", "karo", "badlo", "rate", "price"]))
    )
    if is_rate_change:
        return {"intent": "change_rate", "confidence": 0.99, "clean_text": cleaned}

    # GST Handling: Remove GST vs Add GST
    has_gst_word = ("gst" in lower_t or "tax" in lower_t or "जीएसटी" in lower_t or "टैक्स" in lower_t)
    has_removal_word = any(w in lower_t for w in ["htao", "hatao", "hata", "nikal", "mat", "bina", "without", "remove", "delete", "cancel", "zero", "हटाओ", "हटा"])
    has_zero_pct = bool(re.search(r'\b0(?:\.0)?\s*%', lower_t) or "zero gst" in lower_t or "0 percent" in lower_t)
    has_positive_pct = bool(re.search(r'\b[1-9][0-9]*(?:\.[0-9]+)?\s*%', lower_t))
    has_add_word = any(w in lower_t for w in ["lgao", "lagao", "laga", "add", "jodo", "apply", "include", "dalo", "daalo", "rakho", "calculate", "कैलकुलेट", "लगाओ", "जोड़ो"])

    if has_gst_word and (has_removal_word or has_zero_pct) and not has_positive_pct:
        return {"intent": "remove_gst", "confidence": 0.99, "clean_text": cleaned}

    if has_gst_word and (has_positive_pct or has_add_word):
        return {"intent": "add_gst", "confidence": 0.99, "clean_text": cleaned}

    if any(w in lower_t for w in ["switch to hindi", "hindi me bolo", "hindi language", "hindi me baat"]):
        return {"intent": "switch_language_hindi", "confidence": 0.99, "clean_text": cleaned}
    if any(w in lower_t for w in ["switch to english", "english me bolo", "talk in english", "english language"]):
        return {"intent": "switch_language_english", "confidence": 0.99, "clean_text": cleaned}
    if any(w in lower_t for w in ["start new bill", "naya bill", "clear all", "reset bill"]):
        return {"intent": "reset_session", "confidence": 0.99, "clean_text": cleaned}
    if any(w in lower_t for w in ["cancel last item", "pichla wala item hata do", "undo last", "last wala hatao"]):
        return {"intent": "cancel_last_item", "confidence": 0.99, "clean_text": cleaned}

    model = get_or_load_model()
    
    if model is not None:
        try:
            # Predict intent
            predicted_intent = model.predict([cleaned])[0]
            confidence = 0.90
            
            # Predict probabilities if supported
            if hasattr(model, "predict_proba"):
                probs = model.predict_proba([cleaned])[0]
                classes = model.classes_
                max_idx = probs.argmax()
                predicted_intent = classes[max_idx]
                raw_prob = float(probs[max_idx])
                # Calibrate: 27 classes has baseline ~0.037. Scale raw probability to confidence range
                calibrated = min(0.98, max(0.60, round(raw_prob * 2.2, 4)))
                confidence = calibrated

            # Guard: If model misclassified customer statement as set_shop_name
            if predicted_intent == "set_shop_name" and any(w in lower_t for w in ["customer", "grahak", "client"]):
                predicted_intent = "set_customer"
                confidence = 0.99

            # Guard: If model misclassified add_gst as remove_gst when positive percent or add word is present
            if predicted_intent == "remove_gst" and (has_positive_pct or has_add_word):
                predicted_intent = "add_gst"
                confidence = 0.99

            # Guard: If model misclassified change_rate as query_item_price or add_item
            if predicted_intent in ["query_item_price", "add_item"] and ("rate" in lower_t or "bhav" in lower_t or "daam" in lower_t) and re.search(r'\b[0-9]+', lower_t) and any(w in lower_t for w in ["change", "krdo", "karo", "badlo", "hai"]):
                predicted_intent = "change_rate"
                confidence = 0.99

            # Guard: If model misclassified an item addition without any rate-change keyword as change_rate
            if predicted_intent == "change_rate" and not any(w in lower_t for w in ["rate", "bhav", "daam", "price", "badlo", "change", "रेट", "भाव", "दर", "दाम"]):
                predicted_intent = "add_item"
                confidence = 0.90

            # Guard: If model misclassified change_rate as change_quantity
            if predicted_intent == "change_quantity" and any(w in lower_t for w in ["rate", "price", "bhav", "daam", "rupya", "rupay", "rupy", "rs", "prati", "per", "each", "प्रति"]):
                predicted_intent = "change_rate"
                confidence = 0.99

            return {
                "intent": predicted_intent,
                "confidence": round(confidence, 4),
                "clean_text": cleaned
            }
        except Exception as e:
            print(f"Inference error: {e}")

    # Fallback Rules
    
    if any(w in lower_t for w in ["switch to hindi", "hindi me bolo", "hindi language", "hindi me baat"]):
        return {"intent": "switch_language_hindi", "confidence": 0.99, "clean_text": cleaned}
    if any(w in lower_t for w in ["switch to english", "english me bolo", "talk in english", "english language"]):
        return {"intent": "switch_language_english", "confidence": 0.99, "clean_text": cleaned}
    if any(w in lower_t for w in ["show bill", "total kitna", "bill dikhao", "total batao", "what is the total", "show receipt"]):
        return {"intent": "show_bill", "confidence": 0.98, "clean_text": cleaned}
    if any(w in lower_t for w in ["print invoice", "generate pdf", "bill bana do", "finalize bill", "rased banao"]):
        return {"intent": "finalize_bill", "confidence": 0.98, "clean_text": cleaned}
    if any(w in lower_t for w in ["print thermal", "thermal print", "print 80mm", "parchi print"]):
        return {"intent": "print_thermal", "confidence": 0.98, "clean_text": cleaned}
    if any(w in lower_t for w in ["download pdf", "pdf bill", "download receipt"]):
        return {"intent": "download_pdf", "confidence": 0.98, "clean_text": cleaned}
    if any(w in lower_t for w in ["share on whatsapp", "whatsapp par bhejo", "send on whatsapp"]):
        return {"intent": "share_whatsapp", "confidence": 0.98, "clean_text": cleaned}
    if any(w in lower_t for w in ["start new bill", "naya bill", "clear all", "reset bill"]):
        return {"intent": "reset_session", "confidence": 0.98, "clean_text": cleaned}
    if any(w in lower_t for w in ["cancel last item", "pichla wala item hata do", "undo last", "last wala hatao"]):
        return {"intent": "cancel_last_item", "confidence": 0.98, "clean_text": cleaned}
    # Remove GST / 0% Tax (e.g. "gst htao", "gst hatao", "remove gst", "without gst")
    if any(w in lower_t for w in [
        "gst htao", "gst hatao", "gst hata do", "gst nikal do", "gst mat lagao", 
        "gst cancel", "remove gst", "delete gst", "no gst", "without gst", 
        "zero gst", "bina gst", "tax hatao", "tax hata do", "tax htao", "remove tax", "no tax",
        "जीएसटी हटाओ", "टैक्स हटाओ", "जीएसटी हटा दो"
    ]) or (("gst" in lower_t or "tax" in lower_t or "जीएसटी" in lower_t or "टैक्स" in lower_t) and any(w in lower_t for w in ["htao", "hatao", "hata", "nikal", "mat", "bina", "without", "remove", "no", "zero", "हटाओ", "हटा"])):
        return {"intent": "remove_gst", "confidence": 0.99, "clean_text": cleaned}

    if any(w in lower_t for w in ["discount", "percent off", "off kar do", "chhut"]):
        return {"intent": "apply_discount", "confidence": 0.95, "clean_text": cleaned}
    if any(w in lower_t for w in ["gst", "tax lagao", "tax add", "जीएसटी"]) and not any(w in lower_t for w in ["htao", "hatao", "hata", "nikal", "mat", "bina", "without", "remove", "no", "zero", "हटाओ", "हटा"]):
        return {"intent": "add_gst", "confidence": 0.95, "clean_text": cleaned}
    if any(w in lower_t for w in ["remove", "delete", "hata do", "hatao", "htao", "nikal do", "हटाओ"]):
        return {"intent": "remove_item", "confidence": 0.95, "clean_text": cleaned}
    if any(w in lower_t for w in ["customer", "grahak", "phone", "mobile"]):
        return {"intent": "set_customer", "confidence": 0.95, "clean_text": cleaned}
    if any(w in lower_t for w in ["shop name is", "dukan ka naam", "store name is"]):
        return {"intent": "set_shop_name", "confidence": 0.95, "clean_text": cleaned}
    if any(w in lower_t for w in ["kirana", "grocery", "pharmacy", "medical", "garment", "restaurant"]):
        return {"intent": "setup_shop", "confidence": 0.95, "clean_text": cleaned}
    if any(w in lower_t for w in ["help", "kya kar sakta hoon", "madad"]):
        return {"intent": "help", "confidence": 0.95, "clean_text": cleaned}

    return {"intent": "add_item", "confidence": 0.70, "clean_text": cleaned}
