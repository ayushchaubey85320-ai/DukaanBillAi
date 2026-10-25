"""
ESC/POS Thermal Receipt Formatter for Indian Retail
Formats text and standard ESC/POS control byte sequences for 80mm (48 columns) and 58mm (32 columns) printers.
"""
from typing import Dict, Any

# ESC/POS standard control sequences
ESC = b'\x1b'
GS = b'\x1d'
CMD_INIT = ESC + b'@'
CMD_ALIGN_CENTER = ESC + b'a\x01'
CMD_ALIGN_LEFT = ESC + b'a\x00'
CMD_ALIGN_RIGHT = ESC + b'a\x02'
CMD_BOLD_ON = ESC + b'E\x01'
CMD_BOLD_OFF = ESC + b'E\x00'
CMD_CUT_PAPER = GS + b'V\x41\x00'

def format_thermal_receipt_text(
    bill_data: Dict[str, Any],
    shop_info: Dict[str, Any],
    columns: int = 48
) -> str:
    """
    Produces clean monospaced receipt text strictly formatted to fit
    standard 80mm (48 chars wide) or 58mm (32 chars wide) thermal printers.
    """
    col = columns
    sep_line = "=" * col
    dash_line = "-" * col

    shop_name = (shop_info.get("name") or "INDIAN RETAIL STORE").upper()
    address = shop_info.get("address") or "Main Market, India"
    phone = shop_info.get("phone") or ""
    gstin = shop_info.get("gstin") or ""
    
    bill_id = bill_data.get("bill_id", "001")
    date_str = bill_data.get("date", "")
    customer_name = bill_data.get("customer_name") or "Cash Customer"
    customer_phone = bill_data.get("customer_phone_masked") or ""

    lines = []
    
    # Header
    lines.append(shop_name.center(col))
    if address:
        lines.append(address.center(col))
    contact_parts = []
    if phone:
        contact_parts.append(f"Ph: {phone}")
    if gstin:
        contact_parts.append(f"GST: {gstin}")
    if contact_parts:
        lines.append(" | ".join(contact_parts).center(col))
        
    lines.append(sep_line)
    lines.append("TAX INVOICE".center(col))
    lines.append(sep_line)

    # Metadata
    lines.append(f"Invoice #: {bill_id:<15} Date: {date_str:>16}"[:col])
    lines.append(f"Customer: {customer_name[:18]:<18} {customer_phone:>15}"[:col])
    lines.append(dash_line)

    # Item Column Headers
    if col >= 48:
        # Item (20) | HSN (6) | Qty (6) | Rate (7) | Total (9)
        lines.append(f"{'Item':<19}{'HSN':<6}{'Qty':<6}{'Rate':<8}{'Amount':>9}")
    else:
        # 32 columns: Item(14) Qty(4) Rate(6) Total(8)
        lines.append(f"{'Item':<14}{'Qty':<4}{'Rate':<6}{'Total':>8}")
    lines.append(dash_line)

    # Items
    for item in bill_data.get("items", []):
        name = str(item.get("name", ""))
        hsn = str(item.get("hsn", ""))
        qty = float(item.get("quantity", 1))
        unit = str(item.get("unit", ""))
        rate = float(item.get("rate", 0))
        total = float(item.get("total_amount", 0))
        
        qty_str = f"{qty:g}{unit}"[:5]
        rate_str = f"{rate:.1f}"
        tot_str = f"Rs.{total:.2f}"

        if col >= 48:
            lines.append(f"{name[:18]:<19}{hsn[:5]:<6}{qty_str:<6}{rate_str:<8}{tot_str:>9}")
        else:
            lines.append(f"{name[:13]:<14}{qty_str:<4}{rate_str:<6}{tot_str:>8}")

    lines.append(dash_line)

    # Totals
    subtotal = bill_data.get("items_subtotal", 0.0)
    discount = bill_data.get("discount_applied", 0.0)
    cgst = bill_data.get("total_cgst", 0.0)
    sgst = bill_data.get("total_sgst", 0.0)
    igst = bill_data.get("total_igst", 0.0)
    round_off = bill_data.get("round_off", 0.0)
    grand_total = bill_data.get("grand_total", 0.0)

    lines.append(f"{'Subtotal:':<24}{f'Rs.{subtotal:.2f}':>{col-24}}")
    if discount > 0:
        lines.append(f"{'Discount:':<24}{f'-Rs.{discount:.2f}':>{col-24}}")
    if cgst > 0:
        lines.append(f"{'CGST:':<24}{f'Rs.{cgst:.2f}':>{col-24}}")
    if sgst > 0:
        lines.append(f"{'SGST:':<24}{f'Rs.{sgst:.2f}':>{col-24}}")
    if igst > 0:
        lines.append(f"{'IGST:':<24}{f'Rs.{igst:.2f}':>{col-24}}")
    if round_off != 0.0:
        sign = "+" if round_off > 0 else ""
        lines.append(f"{'Round Off:':<24}{f'{sign}Rs.{round_off:.2f}':>{col-24}}")

    lines.append(sep_line)
    grand_str = f"TOTAL: Rs.{grand_total:.2f}"
    lines.append(grand_str.center(col))
    lines.append(sep_line)

    # Footer
    lines.append("Scan QR on screen to Pay via UPI".center(col))
    lines.append("Thank you for shopping with us!".center(col))
    lines.append("Please visit again".center(col))
    lines.append("\n" * 3)

    return "\n".join(lines)

def generate_escpos_bytes(receipt_text: str) -> bytes:
    """Converts receipt string into raw bytes with standard ESC/POS paper cut."""
    raw = CMD_INIT + receipt_text.encode("latin-1", errors="replace") + CMD_CUT_PAPER
    return raw
