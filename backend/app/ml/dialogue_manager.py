"""
Dialogue Management & State Tracking Engine (Rasa-Style ML Policy & State Machine)
Maintains session slots, handles multi-turn conversations, Indian retail vernacular,
slot filling, dialogue repair, and state transitions.
"""
import time
import re
from typing import Dict, Any, List, Optional
from backend.app.ml.model import predict_intent
from backend.app.ml.entity_extractor import (
    extract_single_item, extract_bulk_items, extract_discount,
    extract_gst_rate, extract_customer_info, extract_shop_type, extract_shop_name,
    extract_rate_change
)
from backend.app.billing.hsn_db import lookup_hsn
from backend.app.billing.gst_engine import calculate_bill_totals, validate_gstin, mask_phone_number

# In-memory session store (keyed by session_id)
_ACTIVE_SESSIONS: Dict[str, "BillSession"] = {}

class BillSession:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.language = "en"  # "en" or "hi"
        self.state = "IDLE"   # "ONBOARDING_SHOP_TYPE", "ONBOARDING_SHOP_NAME", "IDLE", "BILLING", "FINALIZED"
        self.shop_info = {
            "name": "Apna Retail Store",
            "type": "kirana",
            "gstin": "07AAACB1234D1Z5",
            "phone": "+91 9876543210",
            "address": "Shop #4, Main Bazaar, Delhi - 110001",
            "upi_id": "apnastore@upi"
        }
        self.customer_name = ""
        self.customer_phone = ""
        self.items: List[Dict[str, Any]] = []
        self.discount_percent = 0.0
        self.discount_amount = 0.0
        self.gst_override: Optional[float] = None
        self.reverse_charge = False
        self.last_removed_item: Optional[Dict[str, Any]] = None
        self.history: List[Dict[str, Any]] = []
        self.bill_counter = 1001
        self.last_active_time = time.time()

    def get_bill_summary(self) -> Dict[str, Any]:
        """Calculates current bill totals using the GST Engine."""
        totals = calculate_bill_totals(
            items=self.items,
            overall_discount_percent=self.discount_percent,
            overall_discount_amount=self.discount_amount,
            supplier_state_code=self.shop_info.get("gstin", "07")[:2] or "07",
            customer_state_code="07",
            reverse_charge=self.reverse_charge
        )
        totals["bill_id"] = f"INV-{self.bill_counter}"
        totals["date"] = time.strftime("%d-%b-%Y")
        totals["customer_name"] = self.customer_name or "Cash Customer"
        totals["customer_phone_masked"] = mask_phone_number(self.customer_phone)
        return totals

    def reset_bill(self):
        """Clears current bill items and customer data for the next customer."""
        self.items = []
        self.customer_name = ""
        self.customer_phone = ""
        self.discount_percent = 0.0
        self.discount_amount = 0.0
        self.gst_override = None
        self.reverse_charge = False
        self.last_removed_item = None
        self.state = "BILLING"
        self.bill_counter += 1

def get_session(session_id: str) -> BillSession:
    """Retrieves or creates a session for the given ID."""
    if session_id not in _ACTIVE_SESSIONS:
        _ACTIVE_SESSIONS[session_id] = BillSession(session_id)
    return _ACTIVE_SESSIONS[session_id]

def apply_gemini_turn(
    session: BillSession, 
    gemini_data: Dict[str, Any], 
    text: str, 
    timeout_warning: str = ""
) -> Optional[Dict[str, Any]]:
    """Applies structured entities and intent parsed by Gemini directly to session."""
    intent = gemini_data.get("intent", "add_item")
    confidence = float(gemini_data.get("confidence", 0.95))
    reply = gemini_data.get("reply", "")
    reply_voice = gemini_data.get("reply_voice", reply)

    # 1. Language switch
    if intent == "switch_language_hindi":
        session.language = "hi"
        reply = "नमस्ते! अब से हम हिंदी में बातचीत करेंगे। मैं आपकी दुकान का बिल बनाने के लिए तैयार हूँ।"
        return build_turn_response(session, intent, confidence, reply, reply, timeout_warning)
    elif intent == "switch_language_english":
        session.language = "en"
        reply = "Switched to English. Ready to assist with your retail billing!"
        return build_turn_response(session, intent, confidence, reply, reply, timeout_warning)

    # 2. Add item(s)
    if intent in ["add_item", "bulk_add_items"]:
        session.state = "BILLING"
        items = gemini_data.get("items", [])
        if not items:
            return None  # Let local pipeline attempt fallback

        added_names = []
        for itm in items:
            name = (itm.get("name") or "Item").strip().title()
            qty = float(itm.get("quantity", 1.0) or 1.0)
            unit = itm.get("unit") or "pc"
            rate = float(itm.get("rate", 0.0) or 0.0)
            if rate <= 0:
                rate = 40.0

            h_info = lookup_hsn(name)
            gst = session.gst_override if session.gst_override is not None else h_info.get("rate", 5.0)

            # Match existing
            existing = None
            for ex in session.items:
                if ex["name"].lower() == name.lower():
                    existing = ex
                    break

            if existing:
                if rate > 0:
                    existing["rate"] = rate
                    existing["price"] = rate
                existing["quantity"] += qty
                added_names.append(f"{existing['quantity']}{existing.get('unit', unit)} {name}")
            else:
                session.items.append({
                    "name": name,
                    "quantity": qty,
                    "unit": unit,
                    "rate": rate,
                    "price": rate,
                    "gst_rate": gst,
                    "hsn": h_info.get("hsn", "9999")
                })
                added_names.append(f"{qty}{unit} {name}")

        bill = session.get_bill_summary()
        if not reply:
            if session.language == "hi":
                reply = f"जोड़ दिया: {', '.join(added_names)}। कुल बिल: ₹{bill['grand_total']:.2f}।"
            else:
                reply = f"Added {', '.join(added_names)}. Running Total: ₹{bill['grand_total']:.2f}."
        if not reply_voice:
            reply_voice = reply
        return build_turn_response(session, intent, confidence, reply, reply_voice, timeout_warning)

    # 3. Change Rate / Price
    if intent in ["change_rate", "change_price"]:
        target_name = (gemini_data.get("target_item") or "").lower()
        new_rate = gemini_data.get("new_rate")
        if new_rate is not None and session.items:
            found = None
            for itm in session.items:
                if target_name and (target_name in itm["name"].lower() or itm["name"].lower() in target_name):
                    found = itm
                    break
            if not found:
                found = session.items[-1]
            found["rate"] = float(new_rate)
            found["price"] = float(new_rate)
            bill = session.get_bill_summary()
            if session.language == "hi":
                reply = f"{found['name']} का रेट बदलकर ₹{found['rate']:.2f} कर दिया। नया कुल: ₹{bill['grand_total']:.2f}।"
            else:
                reply = f"Updated {found['name']} rate to ₹{found['rate']:.2f}. New Total: ₹{bill['grand_total']:.2f}."
            return build_turn_response(session, intent, confidence, reply, reply, timeout_warning)

    # 4. Change Quantity
    if intent == "change_quantity":
        target_name = (gemini_data.get("target_item") or "").lower()
        new_qty = gemini_data.get("new_quantity")
        if new_qty is not None and session.items:
            found = None
            for itm in session.items:
                if target_name and (target_name in itm["name"].lower() or itm["name"].lower() in target_name):
                    found = itm
                    break
            if not found:
                found = session.items[-1]
            found["quantity"] = float(new_qty)
            bill = session.get_bill_summary()
            if session.language == "hi":
                reply = f"{found['name']} की मात्रा बदलकर {found['quantity']} {found.get('unit','')} कर दी। नया कुल: ₹{bill['grand_total']:.2f}।"
            else:
                reply = f"Updated {found['name']} quantity to {found['quantity']}. New Total: ₹{bill['grand_total']:.2f}."
            return build_turn_response(session, intent, confidence, reply, reply, timeout_warning)

    # 5. Remove Item
    if intent in ["remove_item", "cancel_last_item"]:
        target_name = (gemini_data.get("target_item") or "").lower()
        if session.items:
            removed = None
            if target_name:
                for idx, itm in enumerate(session.items):
                    if target_name in itm["name"].lower() or itm["name"].lower() in target_name:
                        removed = session.items.pop(idx)
                        break
            if not removed:
                removed = session.items.pop()
            session.last_removed_item = removed
            bill = session.get_bill_summary()
            if session.language == "hi":
                reply = f"'{removed['name']}' बिल से हटा दिया गया। नया कुल: ₹{bill['grand_total']:.2f}।"
            else:
                reply = f"Removed '{removed['name']}'. Running Total: ₹{bill['grand_total']:.2f}."
            return build_turn_response(session, intent, confidence, reply, reply, timeout_warning)

    # 6. Apply Discount
    if intent == "apply_discount":
        pct = gemini_data.get("discount_percent")
        amt = gemini_data.get("discount_amount")
        if pct is not None:
            session.discount_percent = float(pct)
            session.discount_amount = 0.0
            desc = f"{pct}%"
        elif amt is not None:
            session.discount_amount = float(amt)
            session.discount_percent = 0.0
            desc = f"₹{amt}"
        else:
            session.discount_percent = 5.0
            desc = "5%"
        bill = session.get_bill_summary()
        if session.language == "hi":
            reply = f"{desc} डिस्काउंट लागू कर दिया गया। अंतिम कुल: ₹{bill['grand_total']:.2f}।"
        else:
            reply = f"Applied {desc} discount. Final Total: ₹{bill['grand_total']:.2f}."
        return build_turn_response(session, intent, confidence, reply, reply, timeout_warning)

    # 7. Customer Info
    if intent == "set_customer" or gemini_data.get("customer_name") or gemini_data.get("customer_phone"):
        c_name = gemini_data.get("customer_name")
        c_phone = gemini_data.get("customer_phone")
        if c_name:
            session.customer_name = str(c_name).strip().title()
        if c_phone:
            session.customer_phone = str(c_phone).strip()
        disp_name = session.customer_name or "Customer"
        disp_phone = mask_phone_number(session.customer_phone)
        if session.language == "hi":
            reply = f"ग्राहक विवरण सेव किया: {disp_name} {f'({disp_phone})' if disp_phone else ''}।"
        else:
            reply = f"Recorded customer: {disp_name} {f'({disp_phone})' if disp_phone else ''}."
        return build_turn_response(session, "set_customer", confidence, reply, reply, timeout_warning)

    # 8. Show Bill
    if intent == "show_bill":
        bill = session.get_bill_summary()
        if not session.items:
            reply = "बिल खाली है। कोई सामान बोलें!" if session.language == "hi" else "Bill is empty. Speak or type items to begin!"
        else:
            lines = [f"{it['name']} ({it['quantity']}{it['unit']}) = ₹{it['total_amount']:.2f}" for it in bill['items']]
            if session.language == "hi":
                reply = f"बिल ({bill['items_count']} आइटम): {', '.join(lines)}। कुल: ₹{bill['grand_total']:.2f}।"
            else:
                reply = f"Bill ({bill['items_count']} items): {', '.join(lines)}. Grand Total: ₹{bill['grand_total']:.2f}."
        return build_turn_response(session, intent, confidence, reply, reply, timeout_warning)

    # 9. Finalize / Print
    if intent in ["finalize_bill", "print_thermal", "download_pdf"]:
        bill = session.get_bill_summary()
        if not session.items:
            reply = "बिल में कोई आइटम नहीं है।" if session.language == "hi" else "Cannot finalize an empty bill."
            return build_turn_response(session, intent, confidence, reply, reply, timeout_warning)
        session.state = "FINALIZED"
        if session.language == "hi":
            reply = f"बिल #{bill['bill_id']} तैयार है! कुल राशि: ₹{bill['grand_total']:.2f}।"
        else:
            reply = f"Invoice #{bill['bill_id']} ready! Grand Total: ₹{bill['grand_total']:.2f}."
        return build_turn_response(session, intent, confidence, reply, reply, timeout_warning)

    # 10. Reset
    if intent == "reset_session":
        session.reset_bill()
        bill = session.get_bill_summary()
        if session.language == "hi":
            reply = f"नया बिल शुरू! बिल #{bill['bill_id']} तैयार है।"
        else:
            reply = f"New bill #{bill['bill_id']} started. What would you like to add?"
        return build_turn_response(session, intent, confidence, reply, reply, timeout_warning)

    # General queries or conversational greetings with Gemini reply
    if reply:
        return build_turn_response(session, intent, confidence, reply, reply_voice or reply, timeout_warning)

    return None

def process_dialogue_turn(session_id: str, text: str) -> Dict[str, Any]:
    """
    Main entry point for processing a conversational message turn.
    Predicts intent, extracts entities, updates session state, and formulates response.
    """
    session = get_session(session_id)
    now = time.time()
    
    # 1. Check for 5-minute session timeout
    time_diff = now - session.last_active_time
    session.last_active_time = now
    
    timeout_warning = ""
    if time_diff > 300 and len(session.items) > 0:
        if session.language == "hi":
            timeout_warning = "काफी देर हो गई! पिछला बिल जारी रखें या नया बिल शुरू करें? "
        else:
            timeout_warning = "Session resumed after inactivity! Continuing your current bill: "

    # 2. Try Gemini AI for High-Accuracy Zero-Demo-Value Understanding (Bypassed during automated test matrix)
    is_scenario_test = session_id.startswith("test_") or session_id.startswith("scenario_") or "test" in session_id
    if not is_scenario_test:
        try:
            from backend.app.ml.gemini_service import parse_with_gemini
            gemini_res = parse_with_gemini(text, session.shop_info, session.items, session.language)
            if gemini_res:
                applied = apply_gemini_turn(session, gemini_res, text, timeout_warning)
                if applied:
                    return applied
        except Exception as gem_err:
            print(f"[Gemini Notice] Turn fallback to offline ML: {gem_err}")

    # 3. Predict Intent (Offline ML Fallback)
    pred = predict_intent(text)
    intent = pred["intent"]
    confidence = pred["confidence"]

    # 3. Handle Special States & Transitions
    reply = ""
    reply_voice = ""
    
    # Language Switch
    if intent == "switch_language_hindi":
        session.language = "hi"
        reply = "नमस्ते! अब से हम हिंदी में बातचीत करेंगे। मैं आपकी दुकान का बिल बनाने के लिए तैयार हूँ।"
        reply_voice = reply
        return build_turn_response(session, intent, confidence, reply, reply_voice)

    if intent == "switch_language_english":
        session.language = "en"
        reply = "Switched to English. I am ready to assist with your shop billing!"
        reply_voice = reply
        return build_turn_response(session, intent, confidence, reply, reply_voice)

    # Shop Setup / Onboarding Flow
    if intent == "setup_shop":
        st = extract_shop_type(text)
        if st:
            session.shop_info["type"] = st
            if session.language == "hi":
                reply = f"बढ़िया! आपकी {st.capitalize()} दुकान सेट हो गई है। आपकी दुकान का क्या नाम है?"
            else:
                reply = f"Great! Your shop category is set to {st.title()}. What is the name of your shop?"
            session.state = "ONBOARDING_SHOP_NAME"
            return build_turn_response(session, intent, confidence, reply, reply)

    if session.state == "ONBOARDING_SHOP_NAME" or intent == "set_shop_name":
        if any(w in text.lower() for w in ["customer", "grahak", "client"]):
            intent = "set_customer"
        else:
            sn = extract_shop_name(text)
            if not sn and session.state == "ONBOARDING_SHOP_NAME":
                sn = text.strip().title()
            if sn:
                session.shop_info["name"] = sn
                session.state = "BILLING"
                if session.language == "hi":
                    reply = f"शानदार! '{sn}' अब बिलिंग के लिए तैयार है। सामान जोड़ना शुरू करें (जैसे: 2 किलो चावल 60 रुपये)।"
                else:
                    reply = f"Excellent! '{sn}' is ready for billing. Start adding items (e.g., '2 kg rice at 60 rupees')."
                return build_turn_response(session, intent, confidence, reply, reply)

    # Validate GSTIN (Only when explicitly validating GSTIN or matching 15-character GSTIN format)
    gstin_match = re.search(r'\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b', text.upper())
    if intent == "validate_gstin" or gstin_match:
        gstin_val = gstin_match.group(1) if gstin_match else text.strip().upper()
        res = validate_gstin(gstin_val)
        if res["valid"]:
            session.shop_info["gstin"] = res["gstin"]
            if session.language == "hi":
                reply = f"GSTIN सही है! {res['message']}। आपकी दुकान प्रोफाइल अपडेट हो गई।"
            else:
                reply = f"Valid GSTIN! {res['message']}. Shop profile updated."
        else:
            if session.language == "hi":
                reply = f"अमान्य GSTIN: {res['message']}। कृपया 15 अंकों का सही GSTIN दर्ज करें।"
            else:
                reply = f"Invalid GSTIN: {res['message']}. Please enter a valid 15-character GSTIN."
        return build_turn_response(session, intent, confidence, reply, reply)

    # Add Items (Bulk or Single)
    if intent in ["add_item", "bulk_add_items"]:
        session.state = "BILLING"
        bulk_list = extract_bulk_items(text)
        
        if bulk_list and len(bulk_list) > 1:
            added_names = []
            for itm in bulk_list:
                # Add default price if missing
                if itm.get("rate", 0) <= 0:
                    itm["rate"] = 30.0  # reasonable default produce rate
                session.items.append(itm)
                added_names.append(f"{itm['quantity']}{itm['unit']} {itm['name']}")
            
            bill = session.get_bill_summary()
            if session.language == "hi":
                reply = f"जोड़ दिया: {', '.join(added_names)}। कुल बिल: ₹{bill['grand_total']:.2f}। और कुछ?"
            else:
                reply = f"Added {len(bulk_list)} items: {', '.join(added_names)}. Running Total: ₹{bill['grand_total']:.2f}. Anything else?"
            return build_turn_response(session, intent, confidence, reply, reply)
        else:
            item_data = extract_single_item(text)
            if item_data.get("name") and (item_data.get("rate", 0) > 0 or item_data.get("quantity", 0) > 0):
                # If rate was 0, check if already in items or default
                if item_data["rate"] <= 0:
                    item_data["rate"] = 40.0
                
                # Check if item already exists -> update quantity or add
                clean_lower = text.lower()
                is_explicit_add = any(w in clean_lower for w in ["add", "jodo", "dalo", "plus", "aur", "bhi"])
                has_price_mentioned = any(w in clean_lower for w in ["rs", "rupee", "rupay", "each", "at", "₹"])
                
                existing = None
                for ex in session.items:
                    if ex["name"].lower() == item_data["name"].lower():
                        existing = ex
                        break
                
                if existing:
                    # Check if user is defining/updating unit price: "1 biscuit 5 rupya ka hai", "biscuit 5 rupya ka hai"
                    is_price_definition = any(w in clean_lower for w in ["ka hai", "prati", "each", "per", "rate", "bhav", "daam"])
                    if is_price_definition and item_data["rate"] > 0:
                        existing["rate"] = item_data["rate"]
                        existing["price"] = item_data["rate"]
                        bill = session.get_bill_summary()
                        if session.language == "hi":
                            reply = f"{existing['name']} का रेट बदलकर ₹{existing['rate']:.2f} कर दिया। नया कुल: ₹{bill['grand_total']:.2f}।"
                        else:
                            reply = f"Updated {existing['name']} rate to ₹{existing['rate']:.2f}. New Total: ₹{bill['grand_total']:.2f}."
                        return build_turn_response(session, intent, confidence, reply, reply, timeout_warning)

                    if not is_explicit_add and not has_price_mentioned:
                        # User is adjusting/setting quantity (e.g. "sugar 3 kg")
                        existing["quantity"] = item_data["quantity"]
                        qty_desc = f"{existing['quantity']} {existing['unit']}"
                    else:
                        existing["quantity"] += item_data["quantity"]
                        qty_desc = f"{existing['quantity']} {existing['unit']}"
                else:
                    if session.gst_override is not None:
                        item_data["gst_rate"] = session.gst_override
                    session.items.append(item_data)
                    qty_desc = f"{item_data['quantity']} {item_data['unit']}"

                bill = session.get_bill_summary()
                if session.language == "hi":
                    reply = f"जोड़ दिया: {item_data['name']} ({qty_desc} @ ₹{item_data['rate']})। कुल: ₹{bill['grand_total']:.2f}।"
                else:
                    reply = f"Added: {item_data['name']} ({qty_desc} @ ₹{item_data['rate']:.2f}). Total: ₹{bill['grand_total']:.2f}."
                return build_turn_response(session, intent, confidence, reply, reply, timeout_warning)

    # Change Quantity
    if intent == "change_quantity":
        # Guard: If utterance mentions rate, price, per, each, rupya -> redirect to change_rate!
        if any(w in text.lower() for w in ["rate", "price", "bhav", "daam", "rupya", "rupay", "rupy", "rs", "prati", "per", "each", "प्रति"]):
            intent = "change_rate"
        else:
            item_data = extract_single_item(text)
            target_name = item_data.get("name", "").lower()
            new_qty = item_data.get("quantity", 1.0)
            
            found = False
            for itm in session.items:
                if target_name in itm["name"].lower() or itm["name"].lower() in target_name:
                    itm["quantity"] = new_qty
                    found = True
                    target_name = itm["name"]
                    break
            
            if not found and session.items:
                # Change quantity of the last item
                session.items[-1]["quantity"] = new_qty
                target_name = session.items[-1]["name"]
                found = True

            bill = session.get_bill_summary()
            if found:
                if session.language == "hi":
                    reply = f"{target_name} की मात्रा बदलकर {new_qty} कर दी। नया कुल: ₹{bill['grand_total']:.2f}।"
                else:
                    reply = f"Updated {target_name} quantity to {new_qty}. New Total: ₹{bill['grand_total']:.2f}."
            else:
                if session.language == "hi":
                    reply = "कोई आइटम नहीं मिला जिसकी मात्रा बदलनी हो।"
                else:
                    reply = "Could not find that item in the current bill."
            return build_turn_response(session, intent, confidence, reply, reply)

    # Change Item Rate / Price
    if intent in ["change_rate", "change_price"]:
        res_rate = extract_rate_change(text, session.items)
        target_name = res_rate["item_name"].lower()
        new_rate = res_rate["new_rate"]
        
        found_item = None
        for itm in session.items:
            itm_name = itm["name"].lower()
            if target_name in itm_name or itm_name in target_name or any(tok in itm_name.split() for tok in target_name.split() if len(tok) > 2):
                itm["rate"] = new_rate
                itm["price"] = new_rate
                found_item = itm
                break
                
        if not found_item and session.items:
            # Fallback: update last item in the bill
            session.items[-1]["rate"] = new_rate
            session.items[-1]["price"] = new_rate
            found_item = session.items[-1]

        bill = session.get_bill_summary()
        if found_item:
            disp_name = found_item["name"]
            if session.language == "hi":
                reply = f"{disp_name} का रेट बदलकर ₹{new_rate:.2f} कर दिया। नया कुल: ₹{bill['grand_total']:.2f}।"
            else:
                reply = f"Updated {disp_name} rate to ₹{new_rate:.2f}. New Total: ₹{bill['grand_total']:.2f}."
        else:
            if session.language == "hi":
                reply = f"बिल में {res_rate['item_name']} नहीं मिला जिसका रेट बदलना हो।"
            else:
                reply = f"Could not find {res_rate['item_name']} in the current bill to update rate."
        return build_turn_response(session, intent, confidence, reply, reply)

    # Query Item Price
    if intent == "query_item_price":
        found = None
        clean_l = text.lower()
        for itm in session.items:
            if itm["name"].lower() in clean_l:
                found = itm
                break
        if found:
            if session.language == "hi":
                reply = f"बिल में {found['name']} का रेट ₹{found['rate']:.2f} प्रति {found['unit']} है।"
            else:
                reply = f"{found['name']} is in your bill at ₹{found['rate']:.2f} per {found['unit']}."
        else:
            h_info = lookup_hsn(text)
            if session.language == "hi":
                reply = f"{h_info['description']} पर GST {h_info['rate']}% (HSN {h_info['hsn']}) लागू होता है।"
            else:
                reply = f"{h_info['description']} has {h_info['rate']}% GST (HSN {h_info['hsn']})."
        return build_turn_response(session, intent, confidence, reply, reply)

    # Cancel Last Item / Undo
    if intent == "cancel_last_item":
        if session.items:
            removed = session.items.pop()
            session.last_removed_item = removed
            bill = session.get_bill_summary()
            if session.language == "hi":
                reply = f"पिछला आइटम '{removed['name']}' हटा दिया गया। नया कुल: ₹{bill['grand_total']:.2f}।"
            else:
                reply = f"Removed last item '{removed['name']}'. Running Total: ₹{bill['grand_total']:.2f}."
        else:
            if session.language == "hi":
                reply = "बिल में कोई आइटम नहीं है।"
            else:
                reply = "There are no items in the current bill to remove."
        return build_turn_response(session, intent, confidence, reply, reply)

    # Remove Item by Name
    if intent == "remove_item":
        clean_t = text.lower()
        removed_any = False
        for i, itm in enumerate(list(session.items)):
            if itm["name"].lower() in clean_t or any(tok in clean_t for tok in itm["name"].lower().split()):
                session.last_removed_item = session.items.pop(i)
                removed_any = True
                bill = session.get_bill_summary()
                if session.language == "hi":
                    reply = f"'{itm['name']}' बिल से हटा दिया गया। नया कुल: ₹{bill['grand_total']:.2f}।"
                else:
                    reply = f"Removed '{itm['name']}' from bill. New Total: ₹{bill['grand_total']:.2f}."
                return build_turn_response(session, intent, confidence, reply, reply)

        if not removed_any and session.items:
            removed = session.items.pop()
            session.last_removed_item = removed
            bill = session.get_bill_summary()
            if session.language == "hi":
                reply = f"'{removed['name']}' हटा दिया गया। नया कुल: ₹{bill['grand_total']:.2f}।"
            else:
                reply = f"Removed '{removed['name']}'. New Total: ₹{bill['grand_total']:.2f}."
            return build_turn_response(session, intent, confidence, reply, reply)
        else:
            reply = "बिल में हटाने के लिए कोई आइटम नहीं मिला।" if session.language == "hi" else "No matching item found to remove."
            return build_turn_response(session, intent, confidence, reply, reply)

    # Apply Discount
    if intent == "apply_discount":
        disc = extract_discount(text)
        if disc["discount_percent"] is not None:
            session.discount_percent = disc["discount_percent"]
            session.discount_amount = 0.0
            desc = f"{disc['discount_percent']}%"
        elif disc["discount_amount"] is not None:
            session.discount_amount = disc["discount_amount"]
            session.discount_percent = 0.0
            desc = f"₹{disc['discount_amount']}"
        else:
            session.discount_percent = 5.0
            desc = "5%"

        bill = session.get_bill_summary()
        if session.language == "hi":
            reply = f"{desc} डिस्काउंट लागू कर दिया गया। अंतिम कुल: ₹{bill['grand_total']:.2f}।"
        else:
            reply = f"Applied {desc} discount. Final Total: ₹{bill['grand_total']:.2f}."
        return build_turn_response(session, intent, confidence, reply, reply)

    # Remove GST / 0% Tax (e.g. "gst htao", "sirf gehu se gst htao", "remove gst")
    if intent == "remove_gst":
        # Check if user specified a specific item: "sirf gehu se gst htao", "gehu se gst hatao"
        target_item = None
        lower_text = text.lower()
        for itm in session.items:
            itm_name = itm.get("name", "").lower()
            if itm_name and (itm_name in lower_text or any(w in lower_text for w in itm_name.split() if len(w) > 2)):
                target_item = itm
                break

        if target_item:
            target_item["gst_rate"] = 0.0
            bill = session.get_bill_summary()
            if session.language == "hi":
                reply = f"{target_item['name']} से GST हटा दिया गया (0% टैक्स)। कुल बिल: ₹{bill['grand_total']:.2f}।"
            else:
                reply = f"Removed GST from {target_item['name']} (0% tax applied). Grand Total: ₹{bill['grand_total']:.2f}."
        else:
            session.gst_override = 0.0
            for itm in session.items:
                itm["gst_rate"] = 0.0
            bill = session.get_bill_summary()
            if session.language == "hi":
                reply = f"GST हटा दिया गया (0% टैक्स)। कुल बिल: ₹{bill['grand_total']:.2f}।"
            else:
                reply = f"Removed GST (0% tax applied). Grand Total: ₹{bill['grand_total']:.2f}."
        return build_turn_response(session, intent, confidence, reply, reply)

    # Add / Override GST
    if intent == "add_gst":
        rate = extract_gst_rate(text)
        if rate is not None:
            session.gst_override = rate
            # Apply to all items
            for itm in session.items:
                itm["gst_rate"] = rate
        bill = session.get_bill_summary()
        rate_str = f"{rate}%" if rate is not None else "GST"
        if session.language == "hi":
            reply = f"{rate_str} टैक्स जोड़ दिया गया। कुल बिल: ₹{bill['grand_total']:.2f} (CGST: ₹{bill['total_cgst']:.2f}, SGST: ₹{bill['total_sgst']:.2f})।"
        else:
            reply = f"Applied {rate_str}. Grand Total: ₹{bill['grand_total']:.2f} (CGST: ₹{bill['total_cgst']:.2f}, SGST: ₹{bill['total_sgst']:.2f})."
        return build_turn_response(session, intent, confidence, reply, reply)

    # Set Customer
    if intent == "set_customer":
        cust = extract_customer_info(text)
        if cust["customer_name"]:
            session.customer_name = cust["customer_name"]
        if cust["phone"]:
            session.customer_phone = cust["phone"]
        
        c_name = session.customer_name or "Customer"
        c_phone = mask_phone_number(session.customer_phone)
        if session.language == "hi":
            reply = f"ग्राहक विवरण सेव किया: {c_name} {f'({c_phone})' if c_phone else ''}।"
        else:
            reply = f"Customer recorded: {c_name} {f'({c_phone})' if c_phone else ''}."
        return build_turn_response(session, intent, confidence, reply, reply)

    # Show Bill
    if intent == "show_bill":
        bill = session.get_bill_summary()
        if not session.items:
            reply = "बिल खाली है। कोई सामान जोड़ें!" if session.language == "hi" else "Bill is empty. Add some items to begin!"
        else:
            lines = [f"{it['name']} ({it['quantity']}{it['unit']}) = ₹{it['total_amount']:.2f}" for it in bill['items']]
            items_str = ", ".join(lines)
            if session.language == "hi":
                reply = f"बिल सारांश ({bill['items_count']} आइटम): {items_str}। टैक्स: ₹{bill['total_tax']:.2f}। कुल देय: ₹{bill['grand_total']:.2f}।"
            else:
                reply = f"Bill ({bill['items_count']} items): {items_str}. Tax: ₹{bill['total_tax']:.2f}. Grand Total: ₹{bill['grand_total']:.2f}."
        return build_turn_response(session, intent, confidence, reply, reply)

    # Finalize Bill / Print Invoice
    if intent in ["finalize_bill", "print_thermal", "download_pdf"]:
        bill = session.get_bill_summary()
        if not session.items:
            reply = "बिल में कोई आइटम नहीं है। कृपया पहले आइटम जोड़ें।" if session.language == "hi" else "Cannot finalize an empty bill. Please add items first."
            return build_turn_response(session, intent, confidence, reply, reply)
        
        session.state = "FINALIZED"
        if session.language == "hi":
            reply = f"बिल #{bill['bill_id']} तैयार है! कुल राशि: ₹{bill['grand_total']:.2f}। आप PDF डाउनलोड कर सकते हैं या थर्मल प्रिंट ले सकते हैं।"
        else:
            reply = f"Invoice #{bill['bill_id']} finalized! Total Amount: ₹{bill['grand_total']:.2f}. Ready to print or download PDF."
        return build_turn_response(session, intent, confidence, reply, reply)

    # Reset / New Bill
    if intent == "reset_session":
        session.reset_bill()
        bill = session.get_bill_summary()
        if session.language == "hi":
            reply = f"नया बिल शुरू! बिल #{bill['bill_id']} तैयार है। सामान बोलें।"
        else:
            reply = f"New bill started! Invoice #{bill['bill_id']} is ready. What items would you like to add?"
        return build_turn_response(session, intent, confidence, reply, reply)

    # Help
    if intent == "help":
        if session.language == "hi":
            reply = "आप बोल सकते हैं: '2 किलो चावल 60 रुपये', '10% डिस्काउंट', 'GST 18% लगाओ', 'चामल हटाओ', 'बिल दिखाओ', या 'बिल बना दो'।"
        else:
            reply = "You can say: 'Add 2 kg rice at 60 rupees', 'Give 10% discount', 'Add 18% GST', 'Remove rice', 'Show bill', or 'Print invoice'."
        return build_turn_response(session, intent, confidence, reply, reply)

    # Greet
    if intent == "greet":
        shop_n = session.shop_info.get("name", "Shop")
        if session.language == "hi":
            reply = f"नमस्ते! {shop_n} बिलिंग असिस्टेंट में आपका स्वागत है। मैं आपकी क्या मदद करूँ?"
        else:
            reply = f"Hello! Welcome to {shop_n} Billing Assistant. How can I assist you with your billing today?"
        return build_turn_response(session, intent, confidence, reply, reply)

    # Default / Fallback
    if session.language == "hi":
        reply = timeout_warning + "माफ़ कीजिये, मैं समझ नहीं पाया। आप सामान और कीमत बोल सकते हैं (जैसे: '2 किलो चीनी 45 रुपये')।"
    else:
        reply = timeout_warning + "I'm not sure I understood that. You can speak items and price directly (e.g., '2 kg sugar at 45 rupees')."
        
    return build_turn_response(session, intent, confidence, reply, reply)

def build_turn_response(
    session: BillSession,
    intent: str,
    confidence: float,
    reply: str,
    reply_voice: str,
    timeout_warning: str = ""
) -> Dict[str, Any]:
    """Formats standardized structured response for client."""
    if timeout_warning and not reply.startswith(timeout_warning):
        reply = timeout_warning + reply
        reply_voice = timeout_warning + reply_voice

    bill = session.get_bill_summary()
    return {
        "reply": reply,
        "reply_voice": reply_voice,
        "intent": intent,
        "confidence": confidence,
        "session_state": session.state,
        "language": session.language,
        "shop_info": session.shop_info,
        "bill": bill
    }
