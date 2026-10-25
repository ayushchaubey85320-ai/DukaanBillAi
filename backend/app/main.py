"""
FastAPI Backend Application for Indian Shopkeeper Billing Agent
Provides conversational REST endpoints, PDF downloads, thermal receipt output,
UPI QR generation, SQLite history, and automated test runners.
"""
import io
import os
import time
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.app.ml.dialogue_manager import process_dialogue_turn, get_session
from backend.app.ml.train import train_intent_model
from backend.app.billing.pdf_generator import generate_invoice_pdf
from backend.app.billing.thermal_printer import format_thermal_receipt_text, generate_escpos_bytes
from backend.app.billing.qr_generator import generate_upi_payment_url, generate_qr_base64
from backend.app.database import (
    init_db, save_bill_record, get_bills_history, get_shop_profile, update_shop_profile
)
from backend.app.tests.test_scenarios import run_all_scenarios_report

app = FastAPI(
    title="Indian Retail Conversational Billing API",
    description="Offline AI/ML Conversational Billing Agent for Indian Shopkeepers",
    version="1.0.0"
)

# Enable CORS for local Vite and mobile development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
def startup_event():
    init_db()

# Request schemas
class ChatRequest(BaseModel):
    session_id: str = "default_counter"
    message: str

class ShopProfileRequest(BaseModel):
    name: str
    type: str
    gstin: Optional[str] = ""
    phone: Optional[str] = ""
    address: Optional[str] = ""
    upi_id: Optional[str] = ""

class SaveBillRequest(BaseModel):
    session_id: str

# API Endpoints
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "engine": "Offline ML & Dialogue State Machine",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    """Processes user voice/text message and returns assistant response with live bill."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    result = process_dialogue_turn(req.session_id, req.message)
    return result

@app.get("/api/bill/current/{session_id}")
def get_current_bill(session_id: str):
    """Retrieves current in-progress bill for a session."""
    session = get_session(session_id)
    return session.get_bill_summary()

@app.post("/api/bill/save")
def save_bill_endpoint(req: SaveBillRequest):
    """Saves the current bill in the database and resets session for the next customer."""
    session = get_session(req.session_id)
    if not session.items:
        raise HTTPException(status_code=400, detail="Cannot save an empty bill")
    
    bill_data = session.get_bill_summary()
    bill_id = save_bill_record(bill_data)
    
    # Reset for next customer
    session.reset_bill()
    return {
        "success": True,
        "saved_bill_id": bill_id,
        "invoice_number": bill_data.get("bill_id"),
        "message": "Bill successfully saved to history"
    }

@app.get("/api/bill/history")
def bill_history_endpoint(limit: int = 50):
    """Returns saved bills history."""
    return get_bills_history(limit=limit)

@app.get("/api/bill/{session_id}/pdf")
def download_pdf_endpoint(session_id: str):
    """Generates and downloads official GST Tax Invoice PDF."""
    session = get_session(session_id)
    if not session.items:
        raise HTTPException(status_code=400, detail="Cannot generate PDF for an empty bill")
    
    bill_data = session.get_bill_summary()
    pdf_bytes = generate_invoice_pdf(bill_data, session.shop_info)
    
    filename = f"{bill_data.get('bill_id', 'Invoice')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@app.get("/api/bill/{session_id}/thermal")
def get_thermal_receipt(session_id: str, cols: int = 48, raw: bool = False):
    """Returns formatted 80mm/58mm thermal receipt text or raw ESC/POS binary."""
    session = get_session(session_id)
    bill_data = session.get_bill_summary()
    receipt_text = format_thermal_receipt_text(bill_data, session.shop_info, columns=cols)
    
    if raw:
        esc_bytes = generate_escpos_bytes(receipt_text)
        return Response(content=esc_bytes, media_type="application/octet-stream")
    
    return {"receipt_text": receipt_text, "columns": cols}

@app.get("/api/bill/{session_id}/qr")
def get_bill_qr(session_id: str):
    """Returns base64 data URL for NPCI UPI QR code."""
    session = get_session(session_id)
    bill_data = session.get_bill_summary()
    upi_uri = generate_upi_payment_url(
        upi_id=session.shop_info.get("upi_id", "shopkeeper@upi"),
        payee_name=session.shop_info.get("name", "Retail Store"),
        amount=bill_data.get("grand_total", 0.0),
        bill_id=bill_data.get("bill_id", "INV-1001")
    )
    b64_qr = generate_qr_base64(upi_uri)
    return {
        "upi_uri": upi_uri,
        "qr_image_base64": b64_qr,
        "amount": bill_data.get("grand_total", 0.0)
    }

@app.get("/api/shop")
def get_shop():
    """Retrieves current shop configuration profile."""
    return get_shop_profile()

@app.post("/api/shop")
def update_shop(req: ShopProfileRequest):
    """Updates shop details."""
    update_shop_profile(req.dict())
    return {"success": True, "message": "Shop profile updated successfully"}

@app.post("/api/train")
def train_model_endpoint():
    """Triggers offline model retraining."""
    metrics = train_intent_model()
    return {"success": True, "metrics": metrics}

@app.get("/api/test-scenarios")
def run_tests_endpoint():
    """Executes all 21 scenario tests and returns comprehensive report."""
    report = run_all_scenarios_report()
    return report

@app.get("/api/download-apk")
def download_apk_endpoint():
    """Serves the compiled native Android APK for direct phone installation."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    apk_candidates = [
        os.path.join(root_dir, "apk", "DukaanAI.apk"),
        os.path.join(root_dir, "frontend", "android", "app", "build", "outputs", "apk", "debug", "app-debug.apk")
    ]
    for apk_path in apk_candidates:
        if os.path.exists(apk_path):
            return FileResponse(
                apk_path,
                media_type="application/vnd.android.package-archive",
                filename="DukaanAI.apk"
            )
    raise HTTPException(status_code=404, detail="APK build is still compiling or not found")

# Mount frontend/dist static files if available (Single full-stack service on Render)
frontend_dist_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend", "dist"
)
if os.path.exists(frontend_dist_dir):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="static")
