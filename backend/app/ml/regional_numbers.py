"""
Regional and Multilingual Number & Unit Parser
Handles English, Hindi (Devanagari), and Hinglish numerals, fractional words, and currencies.
"""
import re
from typing import Optional, Tuple

# Devanagari numerals to standard digits
DEVANAGARI_DIGITS = {
    '०': '0', '१': '1', '२': '2', '३': '3', '४': '4',
    '५': '5', '६': '6', '७': '7', '८': '8', '९': '9'
}

# Hindi Devanagari word mappings
HINDI_NUMBER_WORDS = {
    'आधा': 0.5, 'सवा': 1.25, 'डेढ़': 1.5, 'ढाई': 2.5, 'पौन': 0.75,
    'शून्य': 0, 'एक': 1, 'दो': 2, 'तीन': 3, 'चार': 4, 'पांच': 5,
    'पाँच': 5, 'छह': 6, 'सात': 7, 'आठ': 8, 'नौ': 9, 'दस': 10,
    'ग्यारह': 11, 'बारह': 12, 'तेरह': 13, 'चौदह': 14, 'पंद्रह': 15,
    'सोलह': 16, 'सत्रह': 17, 'अठारह': 18, 'उन्नीस': 19, 'बीस': 20,
    'इक्कीस': 21, 'बाईस': 22, 'तेईस': 23, 'चौबीस': 24, 'पच्चीस': 25,
    'छब्बीस': 26, 'सत्ताईस': 27, 'अट्ठाईस': 28, 'उनतीस': 29, 'तीस': 30,
    'इकतीस': 31, 'बत्तीस': 32, 'पैंतीस': 35, 'चालीस': 40, 'पैंतालीस': 45,
    'पचास': 50, 'प बचपन': 55, 'साठ': 60, 'पैंसठ': 65, 'सत्तर': 70,
    'पचहत्तर': 75, 'अस्सी': 80, 'पचासी': 85, 'नब्बे': 90, 'पंचानवे': 95,
    'सौ': 100, 'हज़ार': 1000, 'हजार': 1000, 'लाख': 100000
}

# Hinglish Romanized number words
HINGLISH_NUMBER_WORDS = {
    'aadha': 0.5, 'adha': 0.5, 'half': 0.5,
    'sawa': 1.25, 'dedh': 1.5, 'dhai': 2.5, 'dhaii': 2.5, 'paun': 0.75,
    'zero': 0, 'ek': 1, 'aik': 1, 'one': 1,
    'do': 2, 'two': 2,
    'teen': 3, 'tin': 3, 'three': 3,
    'char': 4, 'chaar': 4, 'four': 4,
    'paanch': 5, 'panch': 5, 'five': 5,
    'che': 6, 'chhe': 6, 'six': 6,
    'saat': 7, 'seven': 7,
    'aath': 8, 'eight': 8,
    'nau': 9, 'no': 9, 'nine': 9,
    'das': 10, 'dass': 10, 'ten': 10,
    'gyarah': 11, 'barah': 12, 'terah': 13, 'chaudah': 14,
    'pandrah': 15, 'solah': 16, 'satrah': 17, 'atharah': 18,
    'unnees': 19, 'bees': 20, 'pachees': 25, 'pachis': 25,
    'tees': 30, 'paintees': 35, 'chalees': 40, 'paintaalees': 45,
    'pachaas': 50, 'pachas': 50, 'saath': 60, 'sath': 60,
    'painsath': 65, 'pensath': 65, 'sattar': 70, 'assi': 80,
    'nabbe': 90, 'sau': 100, 'so': 100, 'hundred': 100,
    'hazaar': 1000, 'hazar': 1000, 'thousand': 1000, 'lakh': 100000
}

# Standard Indian metric & retail units
UNIT_SYNONYMS = {
    'kg': ['kg', 'kgs', 'kilo', 'kilos', 'kilogram', 'kilograms', 'किलो', 'किग्रा'],
    'g': ['g', 'gm', 'gms', 'gram', 'grams', 'ग्राम'],
    'litre': ['l', 'lt', 'ltr', 'litre', 'litres', 'liter', 'liters', 'लीटर'],
    'ml': ['ml', 'milli', 'millilitre', 'मिली'],
    'packet': ['pkt', 'pkts', 'packet', 'packets', 'pack', 'packs', 'पैकेट'],
    'piece': ['pc', 'pcs', 'piece', 'pieces', 'nag', 'नग', 'पीस'],
    'box': ['box', 'boxes', 'dabba', 'dabbae', 'डिब्बा'],
    'bottle': ['bottle', 'bottles', 'शीशी', 'बोतल'],
    'strip': ['strip', 'strips', 'पत्ता'],
    'meter': ['m', 'meter', 'meters', 'metre', 'मीटर'],
    'dozen': ['dozen', 'darjan', 'दर्जन']
}

def normalize_devanagari_digits(text: str) -> str:
    """Converts any Devanagari numerals (०-९) to ASCII 0-9."""
    for dev, asc in DEVANAGARI_DIGITS.items():
        text = text.replace(dev, asc)
    return text

def parse_number_value(token: str) -> Optional[float]:
    """
    Parses a single word or numeral into a numeric float value.
    Handles: '2', '2.5', '२.५', 'दो', 'dhai', 'paintaalees', etc.
    """
    token = token.strip().lower()
    clean_token = normalize_devanagari_digits(token)

    # Direct float/int parse
    try:
        return float(clean_token)
    except ValueError:
        pass

    # Hindi Devanagari map
    if token in HINDI_NUMBER_WORDS:
        return float(HINDI_NUMBER_WORDS[token])

    # Hinglish map
    if token in HINGLISH_NUMBER_WORDS:
        return float(HINGLISH_NUMBER_WORDS[token])

    return None

def normalize_unit(unit_raw: str) -> str:
    """Normalizes raw unit strings like 'kilos', 'किलो' -> 'kg'."""
    u = unit_raw.strip().lower()
    for standard_unit, synonyms in UNIT_SYNONYMS.items():
        if u in synonyms:
            return standard_unit
    return u or "pc"

def parse_currency_amount(text: str) -> Optional[float]:
    """
    Extracts Indian currency amounts and item rates like:
    '₹1,200.50', '60 rs', '20 rupya', '2 rupya prati kilo', '20 each', 'rate 20', '75 rupay', 'पैंसठ रुपये'
    """
    text = normalize_devanagari_digits(text)
    
    # 1. Currency / Rate Prefix: ₹1,200.50, Rs 1,200, rate 20, rate: 20, bhav 50
    m = re.search(r'(?:₹|rs\.?|inr|rupees?|rupay|rupya|rupye|rupiya|रुपये?|रुपया|rate|bhav|भाव|दर)\s*[:=]?\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)', text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except ValueError:
            pass

    # 2. Currency / Rate Suffix: 60 rs, 20 rupya, 2 rupya prati, 20 each, 20 per pc, 20/-
    m = re.search(r'([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)\s*(?:₹|rs\.?|inr|rupees?|rupay|rupya|rupye|rupiya|रुपये?|रुपया|/-|each|per\b|prati\b|प्रति\b)', text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except ValueError:
            pass

    # 3. Check for at / @ rate: 'at 60', '@ 20'
    m = re.search(r'(?:at|@)\s*([0-9]+(?:,[0-9]+)*(?:\.[0-9]+)?)', text, re.IGNORECASE)
    if m:
        try:
            return float(m.group(1).replace(',', ''))
        except ValueError:
            pass

    # 4. Check for words followed by रुपये, rupya, each, etc.
    tokens = text.split()
    for i, token in enumerate(tokens):
        if token.lower() in ['रुपये', 'रुपया', 'rupay', 'rupya', 'rupye', 'rupiya', 'rupees', 'rs', 'each', 'prati', 'प्रति']:
            if i > 0:
                prev_val = parse_number_value(tokens[i-1])
                if prev_val is not None:
                    return prev_val

    return None
