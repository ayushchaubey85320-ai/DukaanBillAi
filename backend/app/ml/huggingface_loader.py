"""
Hugging Face Dataset Loader for Indian Retail Billing Agent.
Fetches and processes:
1. DSMJ910/hinglish-instruct-10k (conversational Hinglish instruction dataset)
2. HumynLabs/e-commerce-customersupport-hinglish-audio (Hinglish customer support metadata)
Maps utterances into the billing agent intent taxonomy and integrates with offline training.
"""
import os
import json
import urllib.request
import re

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
HF_OUTPUT_FILE = os.path.join(DATA_DIR, "huggingface_hinglish.json")

def fetch_hf_rows(url, length=100):
    """Fetches rows from HuggingFace dataset-server API."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) DukaanAI/1.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))

def classify_hinglish_utterance(user_text, assistant_text, category, scenario):
    """
    Intelligently maps Hinglish conversational pairs to billing agent intents.
    Returns (intent, cleaned_utterance) or None if unrelated.
    """
    text_lower = user_text.lower().strip()
    
    # 1. Greetings / Chitchat
    if any(w in text_lower for w in ["namaste", "pranam", "kaise ho", "kya haal", "hello", "hi bhai", "ram ram", "kya chal raha"]):
        return ("greet", user_text)
    
    # 2. Add / Purchase / Buying items
    if any(w in text_lower for w in ["chahiye", "dena", "kharid", "pack", "packet", "kilo", "order karna", "add karo", "daal do", "le lo"]):
        return ("add_item", user_text)
        
    # 3. Price inquiry / How much
    if any(w in text_lower for w in ["kitna hai", "price kya", "kitne ka hai", "rate kya", "kya bhav", "rupaye"]):
        return ("query_item_price", user_text)
        
    # 4. Discounts / Bargaining
    if any(w in text_lower for w in ["discount", "kam karo", "thoda kam", "sasta", "offer", "chhoot", "kam lagao"]):
        return ("apply_discount", user_text)
        
    # 5. Order status / Bill inquiry
    if any(w in text_lower for w in ["mera bill", "order kab", "receipt", "parcha", "invoice", "kya status", "total kitna"]):
        return ("show_bill", user_text)
        
    # 6. Payment / UPI / Cash
    if any(w in text_lower for w in ["payment", "upi", "paytm", "phonepe", "gpay", "online pay", "cash", "khata"]):
        return ("set_payment_mode", user_text)
        
    # 7. Cancellations / Removals / Returns
    if any(w in text_lower for w in ["cancel", "hatao", "wapas", "return", "nahi chahiye", "nikal do"]):
        return ("remove_item", user_text)
        
    # 8. Confirmation / Done
    if any(w in text_lower for w in ["theek hai", "haan", "done", "ho gaya", "sahi hai", "pakka"]):
        return ("affirm", user_text)
        
    # General customer query fallback
    if category in ["customer_support", "question"]:
        return ("help", user_text)
        
    return None

def load_huggingface_datasets(max_pages=3):
    """
    Loads rows from HuggingFace dataset server and caches extracted labeled pairs.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    extracted_data = []

    # 1. DSMJ910/hinglish-instruct-10k
    print("Fetching DSMJ910/hinglish-instruct-10k from HuggingFace...")
    for page in range(max_pages):
        offset = page * 100
        url = f"https://datasets-server.huggingface.co/rows?dataset=DSMJ910%2Fhinglish-instruct-10k&config=default&split=train&offset={offset}&length=100"
        try:
            res = fetch_hf_rows(url, length=100)
            rows = res.get("rows", [])
            for item in rows:
                row = item.get("row", {})
                user_msg = row.get("user_message", "")
                asst_msg = row.get("assistant_response", "")
                cat = row.get("category", "")
                scen = row.get("scenario", "")
                
                mapped = classify_hinglish_utterance(user_msg, asst_msg, cat, scen)
                if mapped:
                    intent, utterance = mapped
                    extracted_data.append({
                        "utterance": utterance,
                        "intent": intent,
                        "source": "DSMJ910/hinglish-instruct-10k",
                        "category": cat
                    })
            print(f"  Page {page+1}: Processed {len(rows)} rows (Total extracted: {len(extracted_data)})")
        except Exception as e:
            print(f"  Warning: could not fetch page {page}: {e}")
            break

    # 2. HumynLabs/e-commerce-customersupport-hinglish-audio metadata
    print("Fetching HumynLabs/e-commerce-customersupport-hinglish-audio from HuggingFace...")
    try:
        url_audio = "https://datasets-server.huggingface.co/rows?dataset=HumynLabs%2Fe-commerce-customersupport-hinglish-audio&config=default&split=train&offset=0&length=100"
        res_audio = fetch_hf_rows(url_audio, length=100)
        audio_rows = res_audio.get("rows", [])
        print(f"  Fetched {len(audio_rows)} audio records from HumynLabs")
    except Exception as e:
        print(f"  Notice on audio dataset: {e}")

    # Save to huggingface_hinglish.json
    with open(HF_OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(extracted_data, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully cached {len(extracted_data)} Hugging Face Hinglish utterances to {HF_OUTPUT_FILE}")
    return extracted_data

if __name__ == "__main__":
    load_huggingface_datasets(max_pages=3)
