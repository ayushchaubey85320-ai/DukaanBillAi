"""
Hugging Face Dataset Loader for Indian Retail Billing Agent.
Fetches and processes:
1. DSMJ910/hinglish-instruct-10k (conversational Hinglish instruction dataset)
2. ankitdhiman/hinglish-conversations (multi-turn Hinglish conversations)
3. LingoIITGN/COMI-LINGUA (code-mixed Hindi-English sentences with LID)
Maps utterances into billing agent intent taxonomy, including remove_gst and negative controls.
"""
import os
import json
import urllib.request
import re

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HF_OUTPUT_FILE = os.path.join(DATA_DIR, "huggingface_hinglish.json")

def fetch_hf_rows(url):
    """Fetches rows from HuggingFace dataset-server API."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DukaanAI/1.0"}
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode("utf-8"))

def classify_hinglish_utterance(text):
    """
    Intelligently maps Hinglish conversational text to billing agent intents.
    Returns (intent, cleaned_utterance) or None if unrelated.
    """
    if not text or not isinstance(text, str):
        return None
    text_clean = text.strip()
    text_lower = text_clean.lower()
    
    # 0. GST Removal vs Addition (Crucial bugfix for 'gst htao')
    if ("gst" in text_lower or "tax" in text_lower) and any(w in text_lower for w in ["htao", "hatao", "hata", "nikal", "mat", "bina", "without", "remove", "no", "zero", "cancel"]):
        return ("remove_gst", text_clean)
    if any(w in text_lower for w in ["gst lagao", "tax lagao", "add gst", "plus gst", "gst jodo"]):
        return ("add_gst", text_clean)

    # 1. Greetings / Chitchat
    if any(w in text_lower for w in ["namaste", "pranam", "kaise ho", "kya haal", "hello", "hi bhai", "ram ram", "kya chal raha"]):
        return ("greet", text_clean)
    
    # 2. Add / Purchase / Buying items
    if any(w in text_lower for w in ["chahiye", "dena", "kharid", "pack", "packet", "kilo", "order karna", "add karo", "daal do", "le lo"]):
        return ("add_item", text_clean)
        
    # 3. Price inquiry / How much
    if any(w in text_lower for w in ["kitna hai", "price kya", "kitne ka hai", "rate kya", "kya bhav", "rupaye"]):
        return ("query_item_price", text_clean)
        
    # 4. Discounts / Bargaining
    if any(w in text_lower for w in ["discount", "kam karo", "thoda kam", "sasta", "offer", "chhoot", "kam lagao"]):
        return ("apply_discount", text_clean)
        
    # 5. Order status / Bill inquiry
    if any(w in text_lower for w in ["mera bill", "order kab", "receipt", "parcha", "invoice", "kya status", "total kitna"]):
        return ("show_bill", text_clean)
        
    # 6. Payment / UPI / Cash
    if any(w in text_lower for w in ["payment", "upi", "paytm", "phonepe", "gpay", "online pay", "cash", "khata"]):
        return ("set_payment_mode", text_clean)
        
    # 7. Cancellations / Removals / Returns
    if any(w in text_lower for w in ["cancel", "hatao", "htao", "wapas", "return", "nahi chahiye", "nikal do", "delete"]):
        return ("remove_item", text_clean)
        
    # 8. Confirmation / Done
    if any(w in text_lower for w in ["theek hai", "haan", "done", "ho gaya", "sahi hai", "pakka"]):
        return ("affirm", text_clean)
        
    # 9. General help / Questions
    if any(w in text_lower for w in ["madad", "help", "kaise use", "kya kar sakte"]):
        return ("help", text_clean)
        
    return None

def load_all_huggingface_datasets():
    """
    Loads rows from all 3 HuggingFace dataset servers:
    1. DSMJ910/hinglish-instruct-10k
    2. ankitdhiman/hinglish-conversations
    3. LingoIITGN/COMI-LINGUA
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    extracted_data = []

    # 1. DSMJ910/hinglish-instruct-10k (100 rows)
    print("Fetching DSMJ910/hinglish-instruct-10k from HuggingFace...")
    try:
        url1 = "https://datasets-server.huggingface.co/rows?dataset=DSMJ910%2Fhinglish-instruct-10k&config=default&split=train&offset=0&length=100"
        res1 = fetch_hf_rows(url1)
        for item in res1.get("rows", []):
            row = item.get("row", {})
            msg = row.get("user_message", "")
            mapped = classify_hinglish_utterance(msg)
            if mapped:
                intent, utterance = mapped
                extracted_data.append({
                    "utterance": utterance,
                    "intent": intent,
                    "source": "DSMJ910/hinglish-instruct-10k"
                })
        print(f"  Processed DSMJ910 (Total extracted so far: {len(extracted_data)})")
    except Exception as e:
        print(f"  Warning on DSMJ910: {e}")

    # 2. ankitdhiman/hinglish-conversations (100 rows)
    print("Fetching ankitdhiman/hinglish-conversations from HuggingFace...")
    try:
        url2 = "https://datasets-server.huggingface.co/rows?dataset=ankitdhiman%2Fhinglish-conversations&config=default&split=train&offset=0&length=100"
        res2 = fetch_hf_rows(url2)
        for item in res2.get("rows", []):
            row = item.get("row", {})
            u_msg = row.get("user_message", "")
            mapped = classify_hinglish_utterance(u_msg)
            if mapped:
                intent, utterance = mapped
                extracted_data.append({
                    "utterance": utterance,
                    "intent": intent,
                    "source": "ankitdhiman/hinglish-conversations"
                })
        print(f"  Processed ankitdhiman (Total extracted so far: {len(extracted_data)})")
    except Exception as e:
        print(f"  Warning on ankitdhiman: {e}")

    # 3. LingoIITGN/COMI-LINGUA (100 rows)
    print("Fetching LingoIITGN/COMI-LINGUA from HuggingFace...")
    try:
        url3 = "https://datasets-server.huggingface.co/rows?dataset=LingoIITGN%2FCOMI-LINGUA&config=LID&split=train&offset=0&length=100"
        res3 = fetch_hf_rows(url3)
        for item in res3.get("rows", []):
            row = item.get("row", {})
            sentence = row.get("Sentences", "")
            mapped = classify_hinglish_utterance(sentence)
            if mapped:
                intent, utterance = mapped
                extracted_data.append({
                    "utterance": utterance,
                    "intent": intent,
                    "source": "LingoIITGN/COMI-LINGUA"
                })
        print(f"  Processed COMI-LINGUA (Total extracted: {len(extracted_data)})")
    except Exception as e:
        print(f"  Warning on COMI-LINGUA: {e}")

    # Save to huggingface_hinglish.json
    with open(HF_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully cached {len(extracted_data)} Hugging Face Hinglish utterances to {HF_OUTPUT_FILE}")
    return extracted_data

if __name__ == "__main__":
    load_all_huggingface_datasets()
