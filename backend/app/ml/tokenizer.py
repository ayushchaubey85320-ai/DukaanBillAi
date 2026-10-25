"""
Indic, Hinglish & English Multi-script Tokenizer with Speech-to-Text Phonetic Normalization
Handles mixed Devanagari and Latin text, repairs acoustic STT misspellings,
and normalizes tokens for Intent & NER classification.
"""
import re
from typing import List
from backend.app.ml.regional_numbers import normalize_devanagari_digits

# Common acoustic and speech-to-text phonetic mishearings in Indian accents
SPEECH_PHONETIC_REPLACEMENTS = [
    # Grains & Essentials
    (r'\b(?:travel|chavel|chaaval|chawl|chawla)\b', 'chawal'),
    (r'\b(?:dude|dudh|dood)\b', 'doodh'),
    (r'\b(?:ata|aata|atta flour)\b', 'atta'),
    (r'\b(?:gehun|gehoo)\b', 'gehu'),
    (r'\b(?:cheeni|chini|chinny)\b', 'sugar'),
    (r'\b(?:tamater|tomatos|tamator)\b', 'tomato'),
    (r'\b(?:pyaaz|piyaz|piyaaj)\b', 'onion'),
    (r'\b(?:aaloo|allu|aloo)\b', 'potato'),
    (r'\b(?:biskit|biscut|biskut)\b', 'biscuit'),
    (r'\b(?:sabon|saabun)\b', 'soap'),
    (r'\b(?:paracitamol|parasitamol|parasitamal)\b', 'paracetamol'),
    (r'\b(?:dolo650|dolo 650 tablet)\b', 'dolo 650'),
    (r'\b(?:magi|meggi)\b', 'maggi'),
    (r'\b(?:kay gee|kilos?|kilograms?)\b', 'kg'),
    (r'\b(?:liter|liters|litres?|ltr)\b', 'litre'),
    (r'\b(?:packets?|pkts?|pouch)\b', 'packet'),
    (r'\b(?:pieces?|pcs?|nag|piece)\b', 'pc'),
    (r'\b(?:rupees?|rupay|rupiya|rupia|ares)\b', 'rs'),
    (r'\b(?:percent|pratishat)\b', '%'),
    (r'\b(?:bhaiya|bhai|arre suno|please)\b', '')
]

def clean_and_normalize_text(text: str) -> str:
    """
    Cleans raw user input or speech-to-text audio transcript:
    - Normalizes unicode whitespace
    - Converts Devanagari numerals (०-९) to ASCII 0-9
    - Lowercases Latin characters
    - Normalizes Indian currency symbols and punctuation
    - Repairs speech-to-text phonetic distortions
    """
    if not text:
        return ""
    
    # 1. Normalize Devanagari numerals
    text = normalize_devanagari_digits(text)
    
    # 2. Lowercase for uniform phonetic matching
    text = text.lower()

    # 3. Currency symbol normalization
    text = re.sub(r'[₹]', ' rs ', text)

    # 4. Apply phonetic speech repairs
    for pattern, replacement in SPEECH_PHONETIC_REPLACEMENTS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # 5. Remove excessive punctuation but keep decimal dots and hyphens
    text = re.sub(r'[,;:!?]+', ' ', text)

    # 6. Normalize multiple whitespaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def tokenize(text: str) -> List[str]:
    """
    Splits text into tokens handling words, numbers, and symbols across Hindi and English.
    """
    cleaned = clean_and_normalize_text(text)
    pattern = r'[a-zA-Z0-9]+(?:\.[0-9]+)?%?|[\u0900-\u097F]+'
    tokens = re.findall(pattern, cleaned)
    return tokens
