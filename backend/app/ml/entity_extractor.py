"""
Named Entity Recognition (NER) & Slot Extractor
Extracts item, quantity, unit, price, discount, GST, customer, phone,
and shop attributes from English, Hindi, and Hinglish utterances.
"""
import re
from typing import Dict, Any, List, Optional
from backend.app.ml.regional_numbers import (
    parse_number_value, normalize_unit, parse_currency_amount, normalize_devanagari_digits
)
from backend.app.billing.hsn_db import HSN_DATABASE

SHOP_TYPES = [
    "kirana", "grocery", "pharmacy", "medical", "chemist", "garments", "clothing",
    "cloth", "restaurant", "cafe", "dhaba", "electronics", "electricals",
    "hardware", "stationery", "bakery", "dairy", "sweet shop", "mithai"
]

def extract_shop_type(text: str) -> Optional[str]:
    """Identifies shop / business category from utterance."""
    t = text.lower()
    for st in SHOP_TYPES:
        if st in t:
            return "kirana" if st in ["grocery", "kirana"] else ("pharmacy" if st in ["medical", "chemist"] else st)
    return None

def extract_shop_name(text: str) -> Optional[str]:
    """Extracts shop name from phrases like 'shop name is Sharma Kirana' or 'Mera dukan Mithai House'."""
    # Reject if customer is mentioned
    if any(w in text.lower() for w in ["customer", "grahak", "client"]):
        return None
        
    patterns = [
        r'(?:shop name is|dukaan ka naam|dukan ka naam|store name is)\s*[:=]?\s*([A-Za-z0-9\s\u0900-\u097F]+?)(?:$|\.|\,)',
        r'(?:mera|meri)\s+([A-Za-z0-9\s\u0900-\u097F]+?)\s+(?:dukan|shop|store)\s+hai'
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            # Clean filler words
            if len(candidate) > 2 and candidate.lower() not in ["ek", "a", "the", "mera"]:
                return candidate.title()
    return None

def extract_customer_info(text: str) -> Dict[str, Optional[str]]:
    """Extracts customer name and 10-digit Indian mobile number."""
    phone = None
    # 10 digit Indian phone starting with 6, 7, 8, or 9
    phone_match = re.search(r'(?:\+91[\-\s]?)?([6-9][0-9]{9})\b', text)
    if phone_match:
        phone = phone_match.group(1)

    name = None
    
    # 1. Check correction pattern first: "ramesh nhi ayush", "ramesh nahi ayush chaubey", "not ramesh ayush"
    corr_m = re.search(
        r'(?:[A-Za-z\u0900-\u097F]+)\s+(?:nhi|nahi|not|mat)\s*(?:hai|likho|rakho)?\s+([A-Za-z\s\u0900-\u097F]+?)(?:$|\.|\,)', 
        text, 
        re.IGNORECASE
    )
    if corr_m:
        cand = corr_m.group(1).strip()
        tokens = [t for t in cand.split() if t.lower() not in ['hai', 'is', 'ko', 'bhi', 'rakho', 'likho']]
        if tokens:
            name = " ".join(tokens).title()
            return {"customer_name": name, "phone": phone}

    # 2. Check for name patterns:
    # "Customer ka naam ayush chaubey hai", "Customer Ramesh 9876543210", "Grahak Sunita"
    patterns = [
        r'(?:customer|grahak|client)(?:\s+(?:ka|ki))?\s*(?:naam|name)?\s*(?:hai|is)?\s*([A-Za-z\s\u0900-\u097F]+?)(?:\s+(?:hai|is|[0-9]{10})|$|\.|\,)',
        r'(?:naam|name)\s+(?:is|hai)\s+([A-Za-z\s\u0900-\u097F]+?)(?:$|\.|\,)',
        r'(?:customer|grahak)\s+([A-Za-z\s\u0900-\u097F]+)'
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            cand = m.group(1).strip()
            tokens = [
                t for t in cand.split() 
                if t.lower() not in ['ka', 'ki', 'ke', 'hai', 'is', 'ko', 'bhi', 'customer', 'grahak', 'naam', 'name', 'phone', 'mobile', 'number']
            ]
            if tokens:
                name = " ".join(tokens).title()
                break

    return {"customer_name": name, "phone": phone}

def extract_gst_rate(text: str) -> Optional[float]:
    """Extracts requested GST rate percentage like '12% GST', 'GST 18%', 'gst lgao 50%', 'tax lagao 18%'."""
    # 1. Any number followed by % or percent or pratishat
    m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:%|percent|pratishat|प्रतिशत)', text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            pass
    # 2. gst/tax followed by words then number: "gst @ 18", "gst rate 18", "tax 18", "gst lgao 18"
    m2 = re.search(r'(?:gst|tax|जीएसटी|टैक्स)\s*(?:@|rate|rate is|is|lagao|lgao|karo|do|add|me)?\s*([0-9]+(?:\.[0-9]+)?)', text, re.IGNORECASE)
    if m2:
        try:
            return float(m2.group(1))
        except ValueError:
            pass
    return None

def extract_rate_change(text: str, existing_items: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Extracts the target item and new rate from utterances such as:
    - 'peti tile rate change krdo 20 rupya prati'
    - 'rice ka rate 20 rupy prati kilo hai'
    - 'tile rate 25 kar do'
    - 'rate change karo 30 rs'
    - 'change rate to 40'
    """
    clean = normalize_devanagari_digits(text).strip()
    rate = parse_currency_amount(clean)
    
    # If not found via currency, search for numbers after rate/price/bhav keywords
    if rate is None or rate == 0.0:
        m = re.search(r'(?:rate|bhav|daam|price|रेट|भाव|दर|दाम)\s*(?:change\s*krdo|change\s*karo|change|badlo|badal\s*do|to|hai|is|=|:)?\s*([0-9]+(?:\.[0-9]+)?)', clean, re.IGNORECASE)
        if m:
            try:
                rate = float(m.group(1))
            except ValueError:
                pass
                
    # If still not found, check any number in the text
    if rate is None or rate == 0.0:
        tokens = clean.split()
        for t in reversed(tokens):
            v = parse_number_value(t)
            if v is not None:
                rate = v
                break
                
    if rate is None:
        rate = 0.0

    matched_name = None
    clean_lower = clean.lower()
    
    # Match against existing items in current session
    if existing_items:
        # 1. Exact or partial match on item names in bill
        for itm in existing_items:
            itm_name = itm.get("name", "").lower()
            if itm_name and (itm_name in clean_lower or any(tok in clean_lower for tok in itm_name.split() if len(tok) > 2)):
                matched_name = itm.get("name")
                break
                
        # 2. If no name matched but bill has items, default to the last added item
        if not matched_name and len(existing_items) > 0:
            matched_name = existing_items[-1].get("name")

    # If still no matched name, try matching HSN DB
    if not matched_name:
        for k in HSN_DATABASE.keys():
            if re.search(r'\b' + re.escape(k) + r'\b', clean_lower):
                matched_name = k.capitalize()
                break

    if not matched_name:
        # Fallback noun extraction
        stop_words = {
            "rate", "change", "krdo", "kardo", "karo", "kar", "do", "badlo", "badal", "hai", "is",
            "ka", "ki", "ke", "ko", "se", "to", "rupees", "rupay", "rupy", "rupya", "rupye", "rs",
            "prati", "per", "kilo", "kg", "peti", "each", "bhav", "daam", "price", "wali", "wala"
        }
        cand_tokens = [w for w in clean.split() if w.lower() not in stop_words and parse_number_value(w) is None]
        if cand_tokens:
            matched_name = " ".join(cand_tokens).capitalize()

    return {
        "item_name": matched_name or "Item",
        "new_rate": rate
    }

def extract_discount(text: str) -> Dict[str, Optional[float]]:
    """Extracts discount percent or flat amount from text with robust Hindi/Hinglish support."""
    clean = normalize_devanagari_digits(text).lower()

    # 1. Any percentage pattern: "50%", "50 percent", "50 pratishat", "discount dedo 50%"
    m_pct = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:%|percent|pratishat|percentage)', clean, re.IGNORECASE)
    if m_pct:
        return {"discount_percent": float(m_pct.group(1)), "discount_amount": None}

    # Word percentages in Hindi: "dus percent", "bees percent", "pachas percent"
    word_pcts = {
        "paanch": 5.0, "panch": 5.0, "five": 5.0,
        "dus": 10.0, "das": 10.0, "ten": 10.0,
        "pandrah": 15.0, "fifteen": 15.0,
        "bees": 20.0, "twenty": 20.0,
        "pachees": 25.0, "twenty five": 25.0,
        "pachas": 50.0, "fifty": 50.0
    }
    for w, val in word_pcts.items():
        if re.search(rf'\b{w}\s*(?:%|percent|pratishat|chhut|discount)\b', clean):
            return {"discount_percent": val, "discount_amount": None}

    # 2. Percentage before discount keywords: "10% discount", "5 off"
    m_pct_pre = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:discount|off|kam|chhut)', clean, re.IGNORECASE)
    # Check if this number could be a percentage (<= 100 and no rupees keyword)
    if m_pct_pre and not re.search(r'(?:₹|rs\.?|inr|rupees?|rupay?|rupya)', clean):
        val = float(m_pct_pre.group(1))
        if val <= 100:
            return {"discount_percent": val, "discount_amount": None}

    # 3. Flat amount discount: "₹100 off", "50 rupees discount", "100 rupay kam karo", "discount dedo 50 rs"
    m_amt = re.search(r'(?:₹|rs\.?|inr|rupees?|rupay?|rupya)\s*([0-9]+(?:\.[0-9]+)?)', clean, re.IGNORECASE)
    if not m_amt:
        m_amt = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(?:₹|rs\.?|inr|rupees?|rupay?|rupya)', clean, re.IGNORECASE)
    if not m_amt:
        m_amt = re.search(r'(?:discount|off|chhut)\s*(?:dedo|de do|karo|laga do|lga do|do|of)?\s*([0-9]+(?:\.[0-9]+)?)', clean, re.IGNORECASE)

    if m_amt:
        return {"discount_percent": None, "discount_amount": float(m_amt.group(1))}

    return {"discount_percent": None, "discount_amount": None}

def extract_bulk_items(text: str) -> List[Dict[str, Any]]:
    """
    Handles bulk utterances like:
    'Add 10 tomatoes, 5 potatoes, 2 onions'
    '10 tamatar 5 aalu 2 pyaz'
    """
    clean = normalize_devanagari_digits(text)
    # Match patterns like: [qty] [unit?] [item_name] separated by commas or 'and'
    # E.g. "10 tomatoes", "5 kg potatoes", "2 onions"
    clauses = re.split(r'[,;]|(?:\s+and\s+)|\b(?:aur)\b', clean, flags=re.IGNORECASE)
    extracted = []
    
    for clause in clauses:
        clause = clause.strip()
        if not clause or clause.lower() in ["add", "jodo", "dalo", "please"]:
            continue
        item_data = extract_single_item(clause)
        if item_data.get("name") and (item_data.get("rate", 0) > 0 or item_data.get("quantity", 0) > 0):
            extracted.append(item_data)

    if len(extracted) > 1:
        return extracted
    return []

def extract_single_item(text: str) -> Dict[str, Any]:
    """
    Parses item name, quantity, unit, and price/rate from phrases such as:
    - 'add 2 kg rice at 60 rupees'
    - '2 kilo chawal 45'
    - '3 biscuit 20 each'
    - 'दो किलो चावल पैंसठ रुपये'
    - 'paracetamol 2 strips 30 rs'
    - 'shirt 500'
    - 'crocin 1 packet 25 rs'
    """
    clean = normalize_devanagari_digits(text).strip()
    tokens = clean.split()
    
    # 1. Price extraction via currency / rate pattern
    rate = parse_currency_amount(clean)
    
    # 2. Extract numbers in utterance to separate quantity vs rate
    numbers = []
    for idx, t in enumerate(tokens):
        v = parse_number_value(t)
        if v is not None:
            numbers.append((idx, v))
            
    qty = 1.0
    unit = "pc"
    qty_indices = set()
    rate_indices = set()
    
    # If 2 or more numbers are detected:
    # First number is quantity, second number is rate!
    if len(numbers) >= 2:
        q_idx, q_val = numbers[0]
        r_idx, r_val = numbers[1]
        qty = q_val
        qty_indices.add(q_idx)
        # Unit after quantity: e.g. "5 kilo aalu", "3 packet biscuit", "20 peti tile"
        if q_idx + 1 < len(tokens):
            cand_unit = normalize_unit(tokens[q_idx + 1])
            if cand_unit != tokens[q_idx + 1].lower() or tokens[q_idx + 1].lower() in ["kg", "g", "gm", "litre", "ltr", "pkt", "pc", "pcs", "packet", "strip", "box", "nag", "kilo", "peti", "dabba", "crate", "carton"]:
                unit = cand_unit
                qty_indices.add(q_idx + 1)
        # Rate assignment if not already found or fallback to second number
        if rate is None or rate == 0.0:
            rate = r_val
        rate_indices.add(r_idx)
        # Mark all trailing rate modifier tokens: "20 each", "20 rupya kilo", "2 rupya prati kilo"
        for ri in range(r_idx + 1, len(tokens)):
            rate_indices.add(ri)
    elif len(numbers) == 1:
        n_idx, n_val = numbers[0]
        # Check if this single number is price (e.g., preceded by rate or followed by rs)
        is_price_token = any(w in clean.lower() for w in ['rs', 'rupee', 'rupay', 'rupy', 'rupya', 'each', 'rate', 'bhav', 'daam']) and n_idx >= len(tokens) - 2
        if is_price_token:
            rate = n_val
            rate_indices.add(n_idx)
        else:
            qty = n_val
            qty_indices.add(n_idx)
            if n_idx + 1 < len(tokens):
                cand_unit = normalize_unit(tokens[n_idx + 1])
                if cand_unit != tokens[n_idx + 1].lower() or tokens[n_idx + 1].lower() in ["kg", "g", "gm", "litre", "ltr", "pkt", "pc", "pcs", "packet", "strip", "box", "nag", "kilo", "peti", "dabba", "crate", "carton"]:
                    unit = cand_unit
                    qty_indices.add(n_idx + 1)

    # 3. Item Name extraction:
    clean_lower = clean.lower()
    matched_item = None
    for item_key in HSN_DATABASE.keys():
        if re.search(r'\b' + re.escape(item_key) + r'(?:es|s)?\b', clean_lower):
            matched_item = item_key
            break

    if not matched_item:
        # Fallback: remove stop words, rate tokens, and numbers
        stop_words = {
            "add", "jodo", "dalo", "plus", "kar", "do", "karo", "item", "at", "rate", "for", "ka", "ki",
            "ke", "rupees", "rupay", "rupy", "rupya", "rupye", "rupiya", "rs", "inr", "each", "per", "prati", "please",
            "bhi", "aur", "and", "ek", "kilo", "kg", "packet", "pcs", "piece", "gm", "gram", "litre",
            "peti", "dabba", "box", "crate", "carton", "change", "krdo", "kardo", "badlo", "badal", "hai", "is", "ko", "bhav", "daam", "price",
            "रुपये", "रुपया", "पैसे", "प्रति", "भाव", "दर", "दाम", "वाला", "wali"
        }
        item_words = []
        for i, t in enumerate(tokens):
            if i in qty_indices or i in rate_indices:
                continue
            val = parse_number_value(t)
            if val is not None:
                continue
            if t.lower() in stop_words:
                continue
            item_words.append(t)
        if item_words:
            matched_item = " ".join(item_words)

    # If rate is still not found, check if last number token was price
    if (rate is None or rate == 0.0) and len(tokens) > 1:
        last_num = parse_number_value(tokens[-1])
        if last_num is not None and last_num != qty:
            rate = last_num

    if rate is None:
        rate = 0.0

    return {
        "name": (matched_item or "Item").capitalize(),
        "quantity": qty,
        "unit": unit,
        "rate": rate,
        "price": rate
    }
