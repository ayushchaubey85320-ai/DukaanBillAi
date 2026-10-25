"""
GST-Compliant PDF Invoice Generator using ReportLab
Produces official Indian GST Tax Invoices with table formatting,
tax breakdowns, UPI QR code, and bilingual headers.
"""
import io
import os
from typing import Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from backend.app.billing.qr_generator import generate_qr_image_bytes, generate_upi_payment_url

def number_to_indian_words(num: float) -> str:
    """Converts a number to Indian currency words (e.g. 145 -> One Hundred Forty-Five Rupees Only)."""
    units = ["", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine", "Ten",
             "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen", "Seventeen", "Eighteen", "Nineteen"]
    tens = ["", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety"]
    
    n = int(round(num))
    if n == 0:
        return "Zero Rupees Only"
    
    def convert_upto_thousand(val: int) -> str:
        res = ""
        if val >= 100:
            res += units[val // 100] + " Hundred "
            val %= 100
        if val >= 20:
            res += tens[val // 10] + " "
            val %= 10
        if val > 0:
            res += units[val] + " "
        return res.strip()

    parts = []
    # Crores (10,000,000)
    crores = n // 10000000
    if crores > 0:
        parts.append(convert_upto_thousand(crores) + " Crore")
        n %= 10000000

    # Lakhs (100,000)
    lakhs = n // 100000
    if lakhs > 0:
        parts.append(convert_upto_thousand(lakhs) + " Lakh")
        n %= 100000

    # Thousands (1,000)
    thousands = n // 1000
    if thousands > 0:
        parts.append(convert_upto_thousand(thousands) + " Thousand")
        n %= 1000

    if n > 0:
        parts.append(convert_upto_thousand(n))

    return "Rupees " + " ".join(parts).strip() + " Only"

def generate_invoice_pdf(bill_data: Dict[str, Any], shop_info: Dict[str, Any]) -> bytes:
    """
    Renders an A4 PDF Tax Invoice and returns the PDF binary data.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'InvoiceTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#0f172a')
    )
    
    subtitle_style = ParagraphStyle(
        'InvoiceSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#475569')
    )

    shop_name_style = ParagraphStyle(
        'ShopName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1e3a8a')
    )

    cell_style = ParagraphStyle(
        'CellText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#1e293b')
    )

    cell_bold = ParagraphStyle(
        'CellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10,
        textColor=colors.HexColor('#0f172a')
    )

    cell_right = ParagraphStyle(
        'CellRight',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        leading=10,
        alignment=TA_RIGHT,
        textColor=colors.HexColor('#1e293b')
    )

    story = []

    # 1. Header Box
    shop_name = shop_info.get("name", "SHARMA RETAIL STORE")
    shop_addr = shop_info.get("address", "Main Market, Sector 12, Delhi - 110001")
    shop_gstin = shop_info.get("gstin", "07AAACB1234D1Z5")
    shop_phone = shop_info.get("phone", "+91 98765 43210")
    shop_upi = shop_info.get("upi_id", "sharmastore@upi")

    story.append(Paragraph(shop_name.upper(), shop_name_style))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(f"{shop_addr} | Phone: {shop_phone}", subtitle_style))
    story.append(Paragraph(f"GSTIN: <b>{shop_gstin}</b> | State: Delhi (07)", subtitle_style))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("TAX INVOICE / कर बीजक", title_style))
    story.append(Spacer(1, 4 * mm))

    # 2. Metadata Grid (Invoice Info & Customer Info)
    bill_id = bill_data.get("bill_id", "INV-1001")
    bill_date = bill_data.get("date", "25-Oct-2026")
    cust_name = bill_data.get("customer_name") or "Cash Customer"
    cust_phone = bill_data.get("customer_phone_masked") or "N/A"
    rcm_text = "Yes" if bill_data.get("reverse_charge") else "No"

    meta_data = [
        [
            Paragraph(f"<b>Invoice No:</b> {bill_id}", cell_style),
            Paragraph(f"<b>Date:</b> {bill_date}", cell_style),
            Paragraph(f"<b>Reverse Charge:</b> {rcm_text}", cell_style)
        ],
        [
            Paragraph(f"<b>Customer Name:</b> {cust_name}", cell_style),
            Paragraph(f"<b>Contact:</b> {cust_phone}", cell_style),
            Paragraph(f"<b>Place of Supply:</b> State (07)", cell_style)
        ]
    ]

    meta_table = Table(meta_data, colWidths=[65 * mm, 55 * mm, 60 * mm])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4 * mm))

    # 3. Item Table Header
    table_headers = [
        Paragraph("<b>#</b>", cell_bold),
        Paragraph("<b>Item Description</b>", cell_bold),
        Paragraph("<b>HSN</b>", cell_bold),
        Paragraph("<b>Qty</b>", cell_bold),
        Paragraph("<b>Rate (₹)</b>", cell_bold),
        Paragraph("<b>Taxable (₹)</b>", cell_bold),
        Paragraph("<b>CGST</b>", cell_bold),
        Paragraph("<b>SGST</b>", cell_bold),
        Paragraph("<b>Total (₹)</b>", cell_bold),
    ]
    table_rows = [table_headers]

    for item in bill_data.get("items", []):
        row = [
            Paragraph(str(item.get("sl_no", 1)), cell_style),
            Paragraph(item.get("name", ""), cell_style),
            Paragraph(item.get("hsn", "9999"), cell_style),
            Paragraph(f"{item.get('quantity', 1)} {item.get('unit', '')}", cell_style),
            Paragraph(f"{item.get('rate', 0):.2f}", cell_right),
            Paragraph(f"{item.get('taxable_value', 0):.2f}", cell_right),
            Paragraph(f"{item.get('cgst_amount', 0):.2f}", cell_right),
            Paragraph(f"{item.get('sgst_amount', 0):.2f}", cell_right),
            Paragraph(f"{item.get('total_amount', 0):.2f}", cell_right),
        ]
        table_rows.append(row)

    item_table = Table(
        table_rows,
        colWidths=[10 * mm, 45 * mm, 18 * mm, 18 * mm, 20 * mm, 22 * mm, 16 * mm, 16 * mm, 22 * mm]
    )
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e0e7ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e1b4b')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#94a3b8')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(item_table)
    story.append(Spacer(1, 4 * mm))

    # 4. Summary & QR Code Block
    grand_total = bill_data.get("grand_total", 0.0)
    upi_uri = generate_upi_payment_url(
        upi_id=shop_upi,
        payee_name=shop_name,
        amount=grand_total,
        bill_id=bill_id
    )
    qr_bytes = generate_qr_image_bytes(upi_uri)
    qr_stream = io.BytesIO(qr_bytes)
    qr_img = RLImage(qr_stream, width=28 * mm, height=28 * mm)

    subtotal = bill_data.get("items_subtotal", 0.0)
    disc = bill_data.get("discount_applied", 0.0)
    cgst_tot = bill_data.get("total_cgst", 0.0)
    sgst_tot = bill_data.get("total_sgst", 0.0)
    round_off = bill_data.get("round_off", 0.0)

    summary_rows = [
        [Paragraph("Items Subtotal:", cell_style), Paragraph(f"₹ {subtotal:.2f}", cell_right)],
        [Paragraph("Discount:", cell_style), Paragraph(f"- ₹ {disc:.2f}" if disc > 0 else "₹ 0.00", cell_right)],
        [Paragraph("CGST Total:", cell_style), Paragraph(f"₹ {cgst_tot:.2f}", cell_right)],
        [Paragraph("SGST Total:", cell_style), Paragraph(f"₹ {sgst_tot:.2f}", cell_right)],
        [Paragraph("Round Off:", cell_style), Paragraph(f"{'+' if round_off > 0 else ''}₹ {round_off:.2f}", cell_right)],
        [Paragraph("<b>GRAND TOTAL:</b>", cell_bold), Paragraph(f"<b>₹ {grand_total:.2f}</b>", cell_right)],
    ]
    summary_table = Table(summary_rows, colWidths=[38 * mm, 32 * mm])
    summary_table.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#dbeafe')),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))

    footer_layout = [
        [
            qr_img,
            Paragraph(
                f"<b>Scan to Pay via UPI</b><br/>"
                f"<font size=7 color='#64748b'>UPI ID: {shop_upi}</font><br/><br/>"
                f"<b>Amount in Words:</b><br/>"
                f"<i>{number_to_indian_words(grand_total)}</i>",
                cell_style
            ),
            summary_table
        ]
    ]

    footer_table = Table(footer_layout, colWidths=[32 * mm, 78 * mm, 70 * mm])
    footer_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#ffffff')),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(KeepTogether(footer_table))

    # 5. Terms & Signatory
    story.append(Spacer(1, 6 * mm))
    sign_data = [
        [
            Paragraph("<b>Terms & Conditions:</b><br/>1. Goods once sold will not be taken back.<br/>2. Subject to local jurisdiction only.", cell_style),
            Paragraph(f"For <b>{shop_name}</b><br/><br/><br/>Authorized Signatory", cell_right)
        ]
    ]
    sign_table = Table(sign_data, colWidths=[105 * mm, 75 * mm])
    sign_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(sign_table)

    doc.build(story)
    return buffer.getvalue()
