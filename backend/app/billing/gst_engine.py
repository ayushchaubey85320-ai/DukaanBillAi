"""
GST Calculation & Compliance Engine for Indian Businesses
Handles GSTIN validation, HSN lookup, CGST/SGST/IGST breakdown,
discounts, round-off to nearest Rupee without drift, and phone masking.
"""
import re
from typing import List, Dict, Any, Optional
from backend.app.billing.hsn_db import lookup_hsn

# State code mapping for GST
GST_STATE_CODES = {
    "01": "Jammu and Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
    "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan", "09": "Uttar Pradesh",
    "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh", "13": "Nagaland", "14": "Manipur",
    "15": "Mizoram", "16": "Tripura", "17": "Meghalaya", "18": "Assam", "19": "West Bengal",
    "20": "Jharkhand", "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "27": "Maharashtra", "29": "Karnataka", "30": "Goa", "32": "Kerala", "33": "Tamil Nadu",
    "36": "Telangana", "37": "Andhra Pradesh"
}

def validate_gstin(gstin: str) -> Dict[str, Any]:
    """
    Validates 15-character Indian GSTIN format.
    Format: 2 digits (State) + 5 letters (PAN) + 4 digits (PAN) + 1 letter (PAN) + 1 entity num + 'Z' + 1 checksum
    Example: 07AAACB1234D1Z5
    """
    if not gstin:
        return {"valid": False, "message": "GSTIN cannot be empty"}
    
    clean_gstin = gstin.strip().upper()
    pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
    
    if not re.match(pattern, clean_gstin):
        return {
            "valid": False,
            "gstin": clean_gstin,
            "message": "Invalid GSTIN format. Must be 15 characters (e.g., 07AAACB1234D1Z5)"
        }
    
    state_code = clean_gstin[:2]
    state_name = GST_STATE_CODES.get(state_code, "Unknown State")
    pan = clean_gstin[2:12]
    
    return {
        "valid": True,
        "gstin": clean_gstin,
        "state_code": state_code,
        "state_name": state_name,
        "pan": pan,
        "message": f"Valid GSTIN for {state_name}"
    }

def mask_phone_number(phone: str) -> str:
    """Masks customer phone number for privacy: e.g. 9876543210 -> ******3210"""
    clean = re.sub(r'\D', '', phone or '')
    if len(clean) >= 10:
        return '*' * (len(clean) - 4) + clean[-4:]
    elif len(clean) > 4:
        return '*' * (len(clean) - 4) + clean[-4:]
    return phone or ""

def calculate_bill_totals(
    items: List[Dict[str, Any]],
    overall_discount_percent: float = 0.0,
    overall_discount_amount: float = 0.0,
    supplier_state_code: str = "07",
    customer_state_code: str = "07",
    reverse_charge: bool = False
) -> Dict[str, Any]:
    """
    Computes line-item details, taxes (CGST/SGST or IGST), discounts,
    subtotal, and exact round-off to nearest Rupee.
    """
    is_interstate = (supplier_state_code != customer_state_code)
    
    processed_items = []
    items_subtotal = 0.0
    total_tax_amount = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    total_igst = 0.0

    for idx, item in enumerate(items, start=1):
        name = str(item.get("name", "Item")).strip()
        qty = float(item.get("quantity", 1.0))
        rate = float(item.get("rate", item.get("price", 0.0)))
        unit = str(item.get("unit", "pc")).strip()
        
        # HSN and rate lookup
        hsn_info = lookup_hsn(name)
        hsn = item.get("hsn") or hsn_info["hsn"]
        gst_rate = float(item.get("gst_rate") if item.get("gst_rate") is not None else hsn_info["rate"])
        
        # Line level discount
        item_discount = float(item.get("discount", 0.0))
        gross_amount = round(qty * rate, 2)
        taxable_value = max(0.0, round(gross_amount - item_discount, 2))
        
        # Calculate tax
        if gst_rate > 0 and not reverse_charge:
            if is_interstate:
                igst_rate = gst_rate
                cgst_rate = 0.0
                sgst_rate = 0.0
                igst_amount = round(taxable_value * (igst_rate / 100.0), 2)
                cgst_amount = 0.0
                sgst_amount = 0.0
            else:
                igst_rate = 0.0
                cgst_rate = gst_rate / 2.0
                sgst_rate = gst_rate / 2.0
                cgst_amount = round(taxable_value * (cgst_rate / 100.0), 2)
                sgst_amount = round(taxable_value * (sgst_rate / 100.0), 2)
                igst_amount = 0.0
            
            line_tax = round(cgst_amount + sgst_amount + igst_amount, 2)
        else:
            cgst_rate = sgst_rate = igst_rate = 0.0
            cgst_amount = sgst_amount = igst_amount = line_tax = 0.0
            
        line_total = round(taxable_value + line_tax, 2)
        
        processed_items.append({
            "sl_no": idx,
            "name": name,
            "hsn": hsn,
            "quantity": qty,
            "unit": unit,
            "rate": rate,
            "gross_amount": gross_amount,
            "discount": item_discount,
            "taxable_value": taxable_value,
            "gst_rate": gst_rate,
            "cgst_rate": cgst_rate,
            "cgst_amount": cgst_amount,
            "sgst_rate": sgst_rate,
            "sgst_amount": sgst_amount,
            "igst_rate": igst_rate,
            "igst_amount": igst_amount,
            "total_tax": line_tax,
            "total_amount": line_total
        })
        
        items_subtotal += taxable_value
        total_cgst += cgst_amount
        total_sgst += sgst_amount
        total_igst += igst_amount
        total_tax_amount += line_tax

    # Apply global bill discount
    discount_val = 0.0
    if overall_discount_percent > 0:
        discount_val = round(items_subtotal * (overall_discount_percent / 100.0), 2)
    elif overall_discount_amount > 0:
        discount_val = min(items_subtotal, round(overall_discount_amount, 2))

    net_taxable = round(items_subtotal - discount_val, 2)
    
    # Recalculate taxes if global discount applies
    if discount_val > 0 and items_subtotal > 0:
        ratio = net_taxable / items_subtotal
        total_cgst = round(total_cgst * ratio, 2)
        total_sgst = round(total_sgst * ratio, 2)
        total_igst = round(total_igst * ratio, 2)
        total_tax_amount = round(total_cgst + total_sgst + total_igst, 2)

    unrounded_grand_total = round(net_taxable + total_tax_amount, 2)
    
    # Indian standard rounding to nearest Rupee
    rounded_grand_total = float(round(unrounded_grand_total))
    round_off = round(rounded_grand_total - unrounded_grand_total, 2)

    return {
        "items": processed_items,
        "items_count": len(processed_items),
        "items_subtotal": round(items_subtotal, 2),
        "discount_applied": discount_val,
        "discount_percent": overall_discount_percent,
        "net_taxable": net_taxable,
        "total_cgst": total_cgst,
        "total_sgst": total_sgst,
        "total_igst": total_igst,
        "total_tax": total_tax_amount,
        "reverse_charge": reverse_charge,
        "unrounded_grand_total": unrounded_grand_total,
        "round_off": round_off,
        "grand_total": rounded_grand_total,
        "is_interstate": is_interstate
    }
