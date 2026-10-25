"""
Indian GST HSN Code Database & Fast Auto-lookup Engine
Provides standard HSN codes, default GST slabs (0%, 5%, 12%, 18%, 28%), and categories.
"""
from typing import Dict, Any, Optional

HSN_DATABASE: Dict[str, Dict[str, Any]] = {
    # Foodgrains & Essentials (Kirana)
    "rice": {"hsn": "1006", "rate": 5.0, "category": "Kirana / Grains", "description": "Rice pre-packaged"},
    "chawal": {"hsn": "1006", "rate": 5.0, "category": "Kirana / Grains", "description": "Rice / Chawal"},
    "wheat": {"hsn": "1001", "rate": 0.0, "category": "Kirana / Grains", "description": "Wheat (Unpackaged)"},
    "gehu": {"hsn": "1001", "rate": 0.0, "category": "Kirana / Grains", "description": "Wheat / Gehu"},
    "atta": {"hsn": "1101", "rate": 5.0, "category": "Kirana / Flour", "description": "Wheat Flour / Atta"},
    "flour": {"hsn": "1101", "rate": 5.0, "category": "Kirana / Flour", "description": "Flour"},
    "maida": {"hsn": "1101", "rate": 5.0, "category": "Kirana / Flour", "description": "Refined Flour / Maida"},
    "besan": {"hsn": "1102", "rate": 5.0, "category": "Kirana / Flour", "description": "Gram Flour / Besan"},
    "dal": {"hsn": "0713", "rate": 5.0, "category": "Kirana / Pulses", "description": "Pulses / Dal"},
    "toor dal": {"hsn": "0713", "rate": 5.0, "category": "Kirana / Pulses", "description": "Toor / Arhar Dal"},
    "moong dal": {"hsn": "0713", "rate": 5.0, "category": "Kirana / Pulses", "description": "Moong Dal"},
    "sugar": {"hsn": "1701", "rate": 5.0, "category": "Kirana / Sweeteners", "description": "Cane Sugar"},
    "chini": {"hsn": "1701", "rate": 5.0, "category": "Kirana / Sweeteners", "description": "Sugar / Chini"},
    "jaggery": {"hsn": "1701", "rate": 0.0, "category": "Kirana / Sweeteners", "description": "Gur / Jaggery"},
    "salt": {"hsn": "2501", "rate": 0.0, "category": "Kirana / Spices", "description": "Iodised Table Salt"},
    "namak": {"hsn": "2501", "rate": 0.0, "category": "Kirana / Spices", "description": "Table Salt"},
    "oil": {"hsn": "1515", "rate": 5.0, "category": "Kirana / Oils", "description": "Edible Cooking Oil"},
    "tel": {"hsn": "1515", "rate": 5.0, "category": "Kirana / Oils", "description": "Edible Cooking Oil"},
    "mustard oil": {"hsn": "1514", "rate": 5.0, "category": "Kirana / Oils", "description": "Sarson Ka Tel"},
    "ghee": {"hsn": "0405", "rate": 12.0, "category": "Dairy", "description": "Desi Ghee / Butterfat"},
    "butter": {"hsn": "0405", "rate": 12.0, "category": "Dairy", "description": "Butter / Makhan"},
    "milk": {"hsn": "0401", "rate": 0.0, "category": "Dairy", "description": "Fresh Milk (Unpackaged)"},
    "doodh": {"hsn": "0401", "rate": 0.0, "category": "Dairy", "description": "Fresh Milk"},
    "paneer": {"hsn": "0406", "rate": 5.0, "category": "Dairy", "description": "Cottage Cheese / Paneer"},
    "curd": {"hsn": "0403", "rate": 5.0, "category": "Dairy", "description": "Yogurt / Dahi (Packaged)"},
    "dahi": {"hsn": "0403", "rate": 5.0, "category": "Dairy", "description": "Dahi"},
    "tea": {"hsn": "0902", "rate": 5.0, "category": "Kirana / Beverages", "description": "Black / Green Tea"},
    "chai patti": {"hsn": "0902", "rate": 5.0, "category": "Kirana / Beverages", "description": "Tea Leaves"},
    "coffee": {"hsn": "0901", "rate": 5.0, "category": "Kirana / Beverages", "description": "Coffee Beans / Powder"},
    "pani": {"hsn": "2201", "rate": 18.0, "category": "Beverages", "description": "Packaged Drinking Water"},
    "water": {"hsn": "2201", "rate": 18.0, "category": "Beverages", "description": "Packaged Drinking Water"},
    "biscuit": {"hsn": "1905", "rate": 18.0, "category": "Kirana / Snacks", "description": "Biscuits & Cookies"},
    "biscuits": {"hsn": "1905", "rate": 18.0, "category": "Kirana / Snacks", "description": "Biscuits & Cookies"},
    "chips": {"hsn": "2005", "rate": 12.0, "category": "Kirana / Snacks", "description": "Potato Chips / Namkeen"},
    "namkeen": {"hsn": "2106", "rate": 12.0, "category": "Kirana / Snacks", "description": "Bhujia / Savouries"},
    "soap": {"hsn": "3401", "rate": 18.0, "category": "Personal Care", "description": "Toilet / Bathing Soap"},
    "sabun": {"hsn": "3401", "rate": 18.0, "category": "Personal Care", "description": "Bathing Soap"},
    "shampoo": {"hsn": "3305", "rate": 18.0, "category": "Personal Care", "description": "Hair Shampoo"},
    "toothpaste": {"hsn": "3306", "rate": 18.0, "category": "Personal Care", "description": "Dental Cream / Toothpaste"},
    "detergent": {"hsn": "3402", "rate": 18.0, "category": "Cleaning", "description": "Washing Powder / Detergent"},

    # Vegetables & Fruits
    "tomato": {"hsn": "0702", "rate": 0.0, "category": "Produce", "description": "Fresh Tomatoes"},
    "tamatar": {"hsn": "0702", "rate": 0.0, "category": "Produce", "description": "Tamatar"},
    "potato": {"hsn": "0701", "rate": 0.0, "category": "Produce", "description": "Fresh Potatoes"},
    "aalu": {"hsn": "0701", "rate": 0.0, "category": "Produce", "description": "Aalu"},
    "onion": {"hsn": "0703", "rate": 0.0, "category": "Produce", "description": "Fresh Onions"},
    "pyaz": {"hsn": "0703", "rate": 0.0, "category": "Produce", "description": "Pyaz"},

    # Pharmacy & Medicines
    "paracetamol": {"hsn": "3004", "rate": 12.0, "category": "Pharmacy", "description": "Paracetamol Tablets"},
    "crocin": {"hsn": "3004", "rate": 12.0, "category": "Pharmacy", "description": "Pain Reliever / Antipyretic"},
    "cough syrup": {"hsn": "3004", "rate": 12.0, "category": "Pharmacy", "description": "Expectorant Syrup"},
    "syrup": {"hsn": "3004", "rate": 12.0, "category": "Pharmacy", "description": "Medicinal Syrup"},
    "bandaid": {"hsn": "3005", "rate": 12.0, "category": "Pharmacy", "description": "First Aid Bandages"},
    "bandage": {"hsn": "3005", "rate": 12.0, "category": "Pharmacy", "description": "Cotton Gauze Bandage"},
    "dettol": {"hsn": "3808", "rate": 18.0, "category": "Pharmacy", "description": "Antiseptic Liquid"},
    "aspirin": {"hsn": "3004", "rate": 12.0, "category": "Pharmacy", "description": "Aspirin Tablets"},
    "azithromycin": {"hsn": "3004", "rate": 12.0, "category": "Pharmacy", "description": "Antibiotic Tablets"},
    "cetirizine": {"hsn": "3004", "rate": 12.0, "category": "Pharmacy", "description": "Anti-allergic Tablets"},

    # Garments & Textiles
    "shirt": {"hsn": "6205", "rate": 5.0, "category": "Garments", "description": "Cotton / Poly Shirt"},
    "t-shirt": {"hsn": "6109", "rate": 5.0, "category": "Garments", "description": "T-shirt / Polo"},
    "tshirt": {"hsn": "6109", "rate": 5.0, "category": "Garments", "description": "T-shirt"},
    "jeans": {"hsn": "6203", "rate": 12.0, "category": "Garments", "description": "Denim Trousers / Jeans"},
    "pants": {"hsn": "6203", "rate": 5.0, "category": "Garments", "description": "Trousers / Pants"},
    "kurta": {"hsn": "6204", "rate": 5.0, "category": "Garments", "description": "Ethnic Kurta"},
    "saree": {"hsn": "5208", "rate": 5.0, "category": "Garments", "description": "Cotton Saree"},
    "dupatta": {"hsn": "6214", "rate": 5.0, "category": "Garments", "description": "Scarf / Dupatta"},

    # Electronics & Hardware
    "charger": {"hsn": "8504", "rate": 18.0, "category": "Electronics", "description": "Mobile Phone Charger"},
    "cable": {"hsn": "8544", "rate": 18.0, "category": "Electronics", "description": "USB / Data Cable"},
    "earphones": {"hsn": "8518", "rate": 18.0, "category": "Electronics", "description": "Headphones / Earphones"},
    "bulb": {"hsn": "8539", "rate": 12.0, "category": "Electricals", "description": "LED Bulb 9W/12W"},
    "battery": {"hsn": "8506", "rate": 18.0, "category": "Electronics", "description": "Dry Cell Battery AA/AAA"},

    # Stationery
    "pen": {"hsn": "9608", "rate": 12.0, "category": "Stationery", "description": "Ballpoint / Gel Pen"},
    "notebook": {"hsn": "4820", "rate": 12.0, "category": "Stationery", "description": "Paper Notebook / Copy"},
    "copy": {"hsn": "4820", "rate": 12.0, "category": "Stationery", "description": "Exercise Book / Copy"},
    "register": {"hsn": "4820", "rate": 12.0, "category": "Stationery", "description": "Accounting Register"},
    "pencil": {"hsn": "9609", "rate": 12.0, "category": "Stationery", "description": "Graphite Pencil"}
}

DEFAULT_HSN = "9999"
DEFAULT_GST_RATE = 5.0

def lookup_hsn(item_name: str) -> Dict[str, Any]:
    """
    Looks up HSN code, standard GST rate, and category for an item name.
    Matches exact tokens or sub-strings.
    """
    clean_name = item_name.strip().lower()
    
    # 1. Exact match
    if clean_name in HSN_DATABASE:
        return HSN_DATABASE[clean_name]

    # 2. Token match (e.g. "basmati rice" -> "rice", "pantene shampoo" -> "shampoo")
    tokens = clean_name.split()
    for token in tokens:
        if token in HSN_DATABASE:
            return HSN_DATABASE[token]

    # 3. Substring match
    for k, v in HSN_DATABASE.items():
        if k in clean_name or clean_name in k:
            return v

    return {
        "hsn": DEFAULT_HSN,
        "rate": DEFAULT_GST_RATE,
        "category": "General Goods",
        "description": item_name.capitalize()
    }
