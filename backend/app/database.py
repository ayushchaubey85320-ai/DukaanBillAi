"""
SQLite Database Layer for Indian Retail Billing Agent
Persists shopkeeper accounts, Super Admin credentials, customer bills, and system metrics.
"""
import sqlite3
import json
import os
import time
from typing import Dict, Any, List, Optional
from backend.app.auth import hash_password

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "billing.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite schema and ensures user authentication and role tables exist."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table (Shopkeepers & Super Admin)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE NOT NULL,
        email TEXT,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        full_name TEXT NOT NULL,
        shop_name TEXT NOT NULL,
        shop_type TEXT DEFAULT 'kirana',
        gstin TEXT,
        address TEXT,
        upi_id TEXT,
        role TEXT DEFAULT 'shopkeeper', -- 'shopkeeper' or 'super_admin'
        is_active INTEGER DEFAULT 1,
        created_at REAL,
        last_login REAL
    );
    """)

    # 2. Shops Table (Legacy compatibility / cached shop settings)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        gstin TEXT,
        phone TEXT,
        address TEXT,
        upi_id TEXT,
        created_at REAL
    );
    """)

    # 3. Bills Table (Linked to user_id)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        bill_number TEXT NOT NULL UNIQUE,
        customer_name TEXT,
        customer_phone TEXT,
        items_count INTEGER,
        items_json TEXT NOT NULL,
        subtotal REAL,
        discount REAL,
        total_tax REAL,
        round_off REAL,
        grand_total REAL,
        created_at REAL
    );
    """)

    # Check and add user_id column to bills if table existed from an older version
    cursor.execute("PRAGMA table_info(bills);")
    columns = [col[1] for col in cursor.fetchall()]
    if "user_id" not in columns:
        try:
            cursor.execute("ALTER TABLE bills ADD COLUMN user_id INTEGER DEFAULT 1;")
        except Exception as e:
            print(f"Notice on bills table migration: {e}")

    # 4. Seed Super Admin Account if not exists
    super_admin_phone = os.getenv("SUPER_ADMIN_PHONE", "9999999999")
    super_admin_pass = os.getenv("SUPER_ADMIN_PASSWORD", "SuperAdmin@2026")
    super_admin_name = os.getenv("SUPER_ADMIN_NAME", "DukaanAI Owner")

    cursor.execute("SELECT id FROM users WHERE role = 'super_admin' LIMIT 1;")
    admin_row = cursor.fetchone()
    if not admin_row:
        p_hash, salt = hash_password(super_admin_pass)
        now = time.time()
        cursor.execute("""
            INSERT OR IGNORE INTO users (
                phone, password_hash, salt, full_name, shop_name, shop_type, role, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            super_admin_phone,
            p_hash,
            salt,
            super_admin_name,
            "DukaanAI Master Portal",
            "super_admin",
            "super_admin",
            1,
            now
        ))

    # 5. Seed default shopkeeper demo account if no shopkeepers exist
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'shopkeeper';")
    if cursor.fetchone()[0] == 0:
        demo_hash, demo_salt = hash_password("Shop@1234")
        cursor.execute("""
            INSERT INTO users (
                phone, password_hash, salt, full_name, shop_name, shop_type, gstin, address, upi_id, role, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            "9876543210",
            demo_hash,
            demo_salt,
            "Ramesh Sharma",
            "Apna Super Store",
            "kirana",
            "07AAACB1234D1Z5",
            "Shop #12, Central Market, Delhi - 110001",
            "apnastore@upi",
            "shopkeeper",
            1,
            time.time()
        ))

    conn.commit()
    conn.close()

# --- User Management Operations ---

def create_user(
    phone: str,
    password: str,
    full_name: str,
    shop_name: str,
    shop_type: str = "kirana",
    gstin: str = "",
    address: str = "",
    upi_id: str = "",
    email: str = "",
    role: str = "shopkeeper"
) -> Dict[str, Any]:
    """Registers a new shopkeeper account with salted password hash."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM users WHERE phone = ?", (phone,))
    if cursor.fetchone():
        conn.close()
        raise ValueError(f"An account with mobile number {phone} already exists")

    p_hash, salt = hash_password(password)
    now = time.time()

    cursor.execute("""
        INSERT INTO users (
            phone, email, password_hash, salt, full_name, shop_name, shop_type,
            gstin, address, upi_id, role, is_active, created_at, last_login
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        phone, email, p_hash, salt, full_name, shop_name, shop_type,
        gstin, address, upi_id, role, 1, now, now
    ))
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return {
        "id": user_id,
        "phone": phone,
        "full_name": full_name,
        "shop_name": shop_name,
        "shop_type": shop_type,
        "role": role,
        "gstin": gstin,
        "upi_id": upi_id,
        "address": address
    }

def get_user_by_phone(phone: str) -> Optional[Dict[str, Any]]:
    """Fetches user record by mobile phone number."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE phone = ?", (phone,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetches user record by numeric ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_user_last_login(user_id: int):
    """Updates user last login timestamp."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (time.time(), user_id))
    conn.commit()
    conn.close()

def update_user_profile(user_id: int, data: Dict[str, Any]):
    """Updates shopkeeper profile and store attributes."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users SET
            full_name = COALESCE(?, full_name),
            shop_name = COALESCE(?, shop_name),
            shop_type = COALESCE(?, shop_type),
            gstin = COALESCE(?, gstin),
            address = COALESCE(?, address),
            upi_id = COALESCE(?, upi_id)
        WHERE id = ?
    """, (
        data.get("full_name"),
        data.get("shop_name"),
        data.get("shop_type"),
        data.get("gstin"),
        data.get("address"),
        data.get("upi_id"),
        user_id
    ))
    conn.commit()
    conn.close()

def toggle_user_active(user_id: int, is_active: bool):
    """Enables or disables a shopkeeper user account."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (1 if is_active else 0, user_id))
    conn.commit()
    conn.close()

# --- Super Admin Analytics & Tracking Operations ---

def get_all_shopkeepers() -> List[Dict[str, Any]]:
    """Returns list of all registered shopkeepers with aggregate metrics for Super Admin."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            u.id, u.phone, u.full_name, u.shop_name, u.shop_type, u.gstin,
            u.address, u.upi_id, u.role, u.is_active, u.created_at, u.last_login,
            COUNT(b.id) as total_bills,
            COALESCE(SUM(b.grand_total), 0.0) as total_revenue
        FROM users u
        LEFT JOIN bills b ON u.id = b.user_id
        WHERE u.role != 'super_admin'
        GROUP BY u.id
        ORDER BY u.created_at DESC;
    """)
    rows = cursor.fetchall()
    conn.close()

    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "phone": r["phone"],
            "full_name": r["full_name"],
            "shop_name": r["shop_name"],
            "shop_type": r["shop_type"],
            "gstin": r["gstin"] or "N/A",
            "address": r["address"] or "",
            "upi_id": r["upi_id"] or "",
            "is_active": bool(r["is_active"]),
            "created_date": time.strftime("%d-%b-%Y %I:%M %p", time.localtime(r["created_at"])) if r["created_at"] else "-",
            "last_active": time.strftime("%d-%b-%Y %I:%M %p", time.localtime(r["last_login"])) if r["last_login"] else "Never",
            "total_bills": r["total_bills"],
            "total_revenue": round(r["total_revenue"], 2)
        })
    return result

def get_admin_metrics() -> Dict[str, Any]:
    """Computes global platform metrics across all shopkeepers for the Super Admin dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Total registered shopkeepers
    cursor.execute("SELECT COUNT(*) FROM users WHERE role != 'super_admin';")
    total_users = cursor.fetchone()[0]

    # Active shopkeepers
    cursor.execute("SELECT COUNT(*) FROM users WHERE role != 'super_admin' AND is_active = 1;")
    active_users = cursor.fetchone()[0]

    # Total bills across all shops
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(grand_total), 0.0) FROM bills;")
    bill_row = cursor.fetchone()
    total_bills = bill_row[0]
    total_gmv = round(bill_row[1], 2)

    # Bills generated in the last 24 hours
    day_ago = time.time() - 86400
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(grand_total), 0.0) FROM bills WHERE created_at >= ?;", (day_ago,))
    today_row = cursor.fetchone()
    today_bills = today_row[0]
    today_gmv = round(today_row[1], 2)

    conn.close()

    return {
        "total_shopkeepers": total_users,
        "active_shopkeepers": active_users,
        "total_bills_generated": total_bills,
        "total_platform_gmv": total_gmv,
        "today_bills": today_bills,
        "today_gmv": today_gmv,
        "timestamp": time.time()
    }

# --- Billing Operations ---

def save_bill_record(bill_data: Dict[str, Any], user_id: int = 1) -> int:
    """Saves a finalized bill to the database linked to the specific shopkeeper user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    bill_number = bill_data.get("bill_id", f"INV-{int(time.time())}")
    # Handle duplicate bill id safely
    cursor.execute("SELECT id FROM bills WHERE bill_number = ?", (bill_number,))
    existing = cursor.fetchone()
    if existing:
        bill_number = f"{bill_number}-{int(time.time()) % 1000}"

    items_json = json.dumps(bill_data.get("items", []))
    
    cursor.execute("""
        INSERT INTO bills (
            user_id, bill_number, customer_name, customer_phone, items_count,
            items_json, subtotal, discount, total_tax, round_off, grand_total, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        bill_number,
        bill_data.get("customer_name", "Cash Customer"),
        bill_data.get("customer_phone_masked", ""),
        bill_data.get("items_count", len(bill_data.get("items", []))),
        items_json,
        bill_data.get("items_subtotal", 0.0),
        bill_data.get("discount_applied", 0.0),
        bill_data.get("total_tax", 0.0),
        bill_data.get("round_off", 0.0),
        bill_data.get("grand_total", 0.0),
        time.time()
    ))
    
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

def get_bills_history(limit: int = 50, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves bills history, filtered by user_id if provided."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if user_id is not None:
        cursor.execute("""
            SELECT * FROM bills WHERE user_id = ? ORDER BY created_at DESC LIMIT ?
        """, (user_id, limit))
    else:
        cursor.execute("""
            SELECT * FROM bills ORDER BY created_at DESC LIMIT ?
        """, (limit,))

    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "user_id": r["user_id"] if "user_id" in r.keys() else 1,
            "bill_number": r["bill_number"],
            "customer_name": r["customer_name"],
            "customer_phone": r["customer_phone"],
            "items_count": r["items_count"],
            "items": json.loads(r["items_json"]),
            "subtotal": r["subtotal"],
            "discount": r["discount"],
            "total_tax": r["total_tax"],
            "round_off": r["round_off"],
            "grand_total": r["grand_total"],
            "date": time.strftime("%d-%b-%Y %I:%M %p", time.localtime(r["created_at"]))
        })
    return result

def get_shop_profile(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Retrieves shop configuration for the specified user or default shop."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if user_id:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        u = cursor.fetchone()
        conn.close()
        if u:
            return {
                "id": u["id"],
                "name": u["shop_name"],
                "owner_name": u["full_name"],
                "type": u["shop_type"],
                "gstin": u["gstin"] or "",
                "phone": u["phone"],
                "address": u["address"] or "",
                "upi_id": u["upi_id"] or ""
            }

    cursor.execute("SELECT * FROM shops ORDER BY id DESC LIMIT 1;")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {
        "name": "Apna Retail Store",
        "type": "kirana",
        "gstin": "07AAACB1234D1Z5",
        "phone": "+91 9876543210",
        "address": "Main Market, Delhi",
        "upi_id": "apnastore@upi"
    }

def update_shop_profile(data: Dict[str, Any], user_id: Optional[int] = None):
    """Updates shop configuration details."""
    conn = get_db_connection()
    cursor = conn.cursor()

    if user_id:
        cursor.execute("""
            UPDATE users SET
                shop_name = ?, shop_type = ?, gstin = ?, address = ?, upi_id = ?
            WHERE id = ?
        """, (
            data.get("name", "Apna Retail Store"),
            data.get("type", "kirana"),
            data.get("gstin", ""),
            data.get("address", ""),
            data.get("upi_id", ""),
            user_id
        ))
    else:
        cursor.execute("""
            UPDATE shops SET
                name = ?, type = ?, gstin = ?, phone = ?, address = ?, upi_id = ?
            WHERE id = (SELECT id FROM shops ORDER BY id DESC LIMIT 1);
        """, (
            data.get("name", "Apna Retail Store"),
            data.get("type", "kirana"),
            data.get("gstin", ""),
            data.get("phone", ""),
            data.get("address", ""),
            data.get("upi_id", "")
        ))

    conn.commit()
    conn.close()
