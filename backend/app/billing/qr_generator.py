"""
UPI Payment QR Code & Digital Bill Link Generator
Generates standard NPCI UPI payment QR strings and Base64 encoded PNG images.
"""
import io
import base64
import urllib.parse
from typing import Optional
import qrcode
from PIL import Image

def generate_upi_payment_url(
    upi_id: str,
    payee_name: str,
    amount: float,
    bill_id: str,
    currency: str = "INR"
) -> str:
    """
    Builds the standard NPCI UPI payment URI scheme:
    upi://pay?pa=xyz@upi&pn=Shop+Name&am=150.00&cu=INR&tn=Invoice+101
    """
    clean_upi = upi_id.strip() if upi_id else "shopkeeper@upi"
    clean_name = payee_name.strip() if payee_name else "Merchant"
    
    params = {
        "pa": clean_upi,
        "pn": clean_name,
        "am": f"{amount:.2f}",
        "cu": currency,
        "tn": f"Bill {bill_id}"
    }
    return f"upi://pay?{urllib.parse.urlencode(params)}"

def generate_qr_base64(data_string: str) -> str:
    """
    Encodes any text or UPI URI into a Base64-encoded PNG image data URL.
    Returns: 'data:image/png;base64,...'
    """
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(data_string)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    b64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64_str}"

def generate_qr_image_bytes(data_string: str) -> bytes:
    """Returns raw PNG bytes for embedding in PDF reports."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=1,
    )
    qr.add_data(data_string)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()
