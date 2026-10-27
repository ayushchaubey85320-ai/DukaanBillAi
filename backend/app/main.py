"""
FastAPI Backend Application for Indian Shopkeeper Billing Agent
Provides conversational REST endpoints, PDF downloads, thermal receipt output,
UPI QR generation, SQLite history, and automated test runners.
"""
import io
import os
import sys
import time

# Auto-load .env file if available
_proj_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_env_f = os.path.join(_proj_root, ".env")
if os.path.exists(_env_f):
    with open(_env_f, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())
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
from backend.app.auth import (
    hash_password, verify_password, create_access_token, verify_token
)
from backend.app.database import (
    init_db, save_bill_record, get_bills_history, get_shop_profile, update_shop_profile,
    create_user, get_user_by_phone, get_user_by_id, update_user_last_login,
    update_user_profile, toggle_user_active, get_all_shopkeepers, get_admin_metrics,
    ensure_super_admin
)
from backend.app.tests.test_scenarios import run_all_scenarios_report

app = FastAPI(
    title="Indian Retail Conversational Billing API",
    description="Offline AI/ML Conversational Billing Agent for Indian Shopkeepers & Super Admin Portal",
    version="1.0.0"
)

# Enable CORS for local Vite, web browsers, and mobile APKs
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

# --- Request Schemas ---
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

class RegisterRequest(BaseModel):
    phone: str
    password: str
    full_name: str
    shop_name: str
    shop_type: str = "kirana"
    gstin: Optional[str] = ""
    address: Optional[str] = ""
    upi_id: Optional[str] = ""
    email: Optional[str] = ""

class LoginRequest(BaseModel):
    phone: str
    password: str

class UserStatusToggleRequest(BaseModel):
    is_active: bool

# --- Auth Helpers ---
from fastapi import Header

def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    if not authorization:
        return None
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return verify_token(parts[1])
    return None

def require_authenticated_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    user = get_current_user_optional(authorization)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user

def require_super_admin(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    user = require_authenticated_user(authorization)
    if user.get("role") != "super_admin":
        raise HTTPException(status_code=403, detail="Super Admin authorization required")
    return user

# API Endpoints
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "engine": "Offline ML & Dialogue State Machine",
        "timestamp": time.time(),
        "version": "1.0.0"
    }

# --- Authentication Endpoints ---
@app.post("/api/auth/register")
@app.post("/api/auth/register/")
def register_endpoint(req: RegisterRequest):
    """Registers a new shopkeeper account and returns a 30-day JWT token."""
    cleaned_phone = req.phone.strip().replace(" ", "").replace("-", "")
    if len(cleaned_phone) < 10:
        raise HTTPException(status_code=400, detail="Please enter a valid 10-digit mobile number")
    if len(req.password) < 4:
        raise HTTPException(status_code=400, detail="Password must be at least 4 characters")

    try:
        user = create_user(
            phone=cleaned_phone,
            password=req.password,
            full_name=req.full_name.strip(),
            shop_name=req.shop_name.strip(),
            shop_type=req.shop_type.strip(),
            gstin=req.gstin.strip() if req.gstin else "",
            address=req.address.strip() if req.address else "",
            upi_id=req.upi_id.strip() if req.upi_id else "",
            email=req.email.strip() if req.email else ""
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    token = create_access_token({
        "sub": str(user["id"]),
        "user_id": user["id"],
        "phone": user["phone"],
        "role": user["role"],
        "shop_name": user["shop_name"]
    })

    return {
        "success": True,
        "token": token,
        "user": user,
        "message": "Account created successfully"
    }

@app.post("/api/auth/login")
@app.post("/api/auth/login/")
def login_endpoint(req: LoginRequest):
    """Authenticates phone & password for shopkeeper or super admin."""
    cleaned_phone = req.phone.strip().replace(" ", "").replace("-", "")

    # Seamless Super Admin Login for Owner: 7983933436 / Ayush
    if cleaned_phone == "7983933436" and req.password == "Ayush":
        admin_user = ensure_super_admin("7983933436", "Ayush", "Ayush (Owner)")
        update_user_last_login(admin_user["id"])
        token = create_access_token({
            "sub": str(admin_user["id"]),
            "user_id": admin_user["id"],
            "phone": admin_user["phone"],
            "role": "super_admin",
            "shop_name": admin_user.get("shop_name", "DukaanAI Master Portal")
        })
        return {
            "success": True,
            "token": token,
            "user": {
                "id": admin_user["id"],
                "phone": admin_user["phone"],
                "full_name": admin_user["full_name"],
                "shop_name": admin_user.get("shop_name", "DukaanAI Master Portal"),
                "shop_type": "super_admin",
                "role": "super_admin"
            },
            "message": "Namaste Ayush! Welcome to DukaanAI Master Portal."
        }

    user = get_user_by_phone(cleaned_phone)
    if not user:
        raise HTTPException(status_code=401, detail="Mobile number not registered")

    if not verify_password(req.password, user["password_hash"], user["salt"]):
        raise HTTPException(status_code=401, detail="Incorrect password. Please try again.")

    if not user.get("is_active", 1):
        raise HTTPException(status_code=403, detail="Account suspended. Please contact administrator.")

    update_user_last_login(user["id"])

    token = create_access_token({
        "sub": str(user["id"]),
        "user_id": user["id"],
        "phone": user["phone"],
        "role": user["role"],
        "shop_name": user["shop_name"]
    })

    user_info = {
        "id": user["id"],
        "phone": user["phone"],
        "full_name": user["full_name"],
        "shop_name": user["shop_name"],
        "shop_type": user["shop_type"],
        "gstin": user.get("gstin", ""),
        "address": user.get("address", ""),
        "upi_id": user.get("upi_id", ""),
        "role": user["role"]
    }

    return {
        "success": True,
        "token": token,
        "user": user_info,
        "message": f"Welcome back, {user['full_name']}!"
    }

@app.get("/api/auth/me")
def get_current_user_profile(authorization: Optional[str] = Header(None)):
    """Returns profile for currently authenticated user."""
    user_payload = require_authenticated_user(authorization)
    user = get_user_by_id(user_payload["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user["id"],
        "phone": user["phone"],
        "full_name": user["full_name"],
        "shop_name": user["shop_name"],
        "shop_type": user["shop_type"],
        "gstin": user.get("gstin", ""),
        "address": user.get("address", ""),
        "upi_id": user.get("upi_id", ""),
        "role": user["role"],
        "is_impersonated": bool(user_payload.get("impersonated_by"))
    }

# --- Super Admin Monitoring & Impersonation Endpoints ---
@app.get("/api/admin/metrics")
def admin_metrics_endpoint(authorization: Optional[str] = Header(None)):
    """Returns platform-wide metrics for Super Admin dashboard."""
    require_super_admin(authorization)
    return get_admin_metrics()

@app.get("/api/admin/shopkeepers")
def admin_shopkeepers_endpoint(authorization: Optional[str] = Header(None)):
    """Returns list of all registered shopkeepers with total bills & GMV generated."""
    require_super_admin(authorization)
    return get_all_shopkeepers()

@app.get("/api/admin/shopkeepers/{user_id}/bills")
def admin_shopkeeper_bills_endpoint(user_id: int, authorization: Optional[str] = Header(None)):
    """Returns bill history for a specific shopkeeper."""
    require_super_admin(authorization)
    shopkeeper = get_user_by_id(user_id)
    if not shopkeeper:
        raise HTTPException(status_code=404, detail="Shopkeeper not found")
    bills = get_bills_history(limit=100, user_id=user_id)
    return {
        "shopkeeper": {
            "id": shopkeeper["id"],
            "full_name": shopkeeper["full_name"],
            "shop_name": shopkeeper["shop_name"],
            "phone": shopkeeper["phone"]
        },
        "bills": bills
    }

@app.post("/api/admin/shopkeepers/{user_id}/toggle")
def admin_toggle_user_status_endpoint(user_id: int, req: UserStatusToggleRequest, authorization: Optional[str] = Header(None)):
    """Enables or suspends a shopkeeper account."""
    require_super_admin(authorization)
    shopkeeper = get_user_by_id(user_id)
    if not shopkeeper or shopkeeper["role"] == "super_admin":
        raise HTTPException(status_code=400, detail="Cannot toggle status for this user")
    toggle_user_active(user_id, req.is_active)
    return {"success": True, "user_id": user_id, "is_active": req.is_active}

@app.post("/api/admin/impersonate/{user_id}")
def admin_impersonate_user_endpoint(user_id: int, authorization: Optional[str] = Header(None)):
    """
    Super Admin Master Feature:
    Allows Super Admin to log into ANY shopkeeper's account with 1-click
    to view their exact live billing screen, bill history, and store setup.
    """
    admin = require_super_admin(authorization)
    target_user = get_user_by_id(user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Target shopkeeper not found")

    impersonation_token = create_access_token({
        "sub": str(target_user["id"]),
        "user_id": target_user["id"],
        "phone": target_user["phone"],
        "role": target_user["role"],
        "shop_name": target_user["shop_name"],
        "impersonated_by": admin["phone"]
    })

    return {
        "success": True,
        "impersonation_token": impersonation_token,
        "target_user": {
            "id": target_user["id"],
            "phone": target_user["phone"],
            "full_name": target_user["full_name"],
            "shop_name": target_user["shop_name"],
            "shop_type": target_user["shop_type"],
            "gstin": target_user.get("gstin", ""),
            "address": target_user.get("address", ""),
            "upi_id": target_user.get("upi_id", ""),
            "role": target_user["role"]
        },
        "message": f"Successfully logged in as {target_user['shop_name']} ({target_user['phone']})"
    }

# --- Billing Endpoints (User-Aware) ---
@app.post("/api/chat")
def chat_endpoint(req: ChatRequest, authorization: Optional[str] = Header(None)):
    """Processes user voice/text message and returns assistant response with live bill."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    
    session = get_session(req.session_id)
    user = get_current_user_optional(authorization)
    if user:
        # Load this user's shop profile into session if not already done
        user_shop = get_shop_profile(user_id=user["user_id"])
        if user_shop:
            session.shop_info = user_shop

    result = process_dialogue_turn(req.session_id, req.message)
    return result

@app.get("/api/bill/current/{session_id}")
def get_current_bill(session_id: str):
    """Retrieves current in-progress bill for a session."""
    session = get_session(session_id)
    return session.get_bill_summary()

@app.post("/api/bill/save")
@app.post("/api/bill/save/")
def save_bill_endpoint(req: SaveBillRequest, authorization: Optional[str] = Header(None)):
    """Saves the current bill in the database and resets session for the next customer."""
    session = get_session(req.session_id)
    if not session.items:
        raise HTTPException(status_code=400, detail="Cannot save an empty bill")
    
    user = get_current_user_optional(authorization)
    user_id = user["user_id"] if user else 1

    bill_data = session.get_bill_summary()
    bill_id = save_bill_record(bill_data, user_id=user_id)
    
    # Reset for next customer
    session.reset_bill()
    return {
        "success": True,
        "saved_bill_id": bill_id,
        "invoice_number": bill_data.get("bill_id"),
        "message": "Bill successfully saved to history"
    }

@app.get("/api/bill/history")
@app.get("/api/bill/history/")
def bill_history_endpoint(limit: int = 50, authorization: Optional[str] = Header(None)):
    """Returns saved bills history filtered for the current shopkeeper."""
    user = get_current_user_optional(authorization)
    user_id = user["user_id"] if (user and user.get("role") != "super_admin") else None
    return get_bills_history(limit=limit, user_id=user_id)

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
def get_shop(authorization: Optional[str] = Header(None)):
    """Retrieves current shop configuration profile."""
    user = get_current_user_optional(authorization)
    user_id = user["user_id"] if user else None
    return get_shop_profile(user_id=user_id)

@app.post("/api/shop")
def update_shop(req: ShopProfileRequest, authorization: Optional[str] = Header(None)):
    """Updates shop details."""
    user = get_current_user_optional(authorization)
    user_id = user["user_id"] if user else None
    update_shop_profile(req.dict(), user_id=user_id)
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
    """Serves the compiled native Android APK for direct phone installation (Shopkeeper App)."""
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

@app.get("/api/download-super-admin-apk")
def download_super_admin_apk_endpoint():
    """Serves the compiled Super Admin private APK for the owner only."""
    root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    admin_apk_candidates = [
        os.path.join(root_dir, "apk", "DukaanAI-SuperAdmin.apk"),
        os.path.join(root_dir, "super_admin_app", "android", "app", "build", "outputs", "apk", "debug", "app-debug.apk"),
        os.path.join(root_dir, "apk", "DukaanAI.apk")
    ]
    for apk_path in admin_apk_candidates:
        if os.path.exists(apk_path):
            return FileResponse(
                apk_path,
                media_type="application/vnd.android.package-archive",
                filename="DukaanAI-SuperAdmin.apk"
            )
    raise HTTPException(status_code=404, detail="Super Admin APK is not available on this server")

# API Fallback: Catch any unmatched /api route so it never hits StaticFiles with 405 Method Not Allowed
@app.api_route("/api/{full_path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"])
def api_not_found(full_path: str):
    raise HTTPException(status_code=404, detail=f"API endpoint '/api/{full_path}' not found")

# Mount frontend/dist static files if available (Single full-stack service on Render)
frontend_dist_dir = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend", "dist"
)
if os.path.exists(frontend_dist_dir):
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="static")
