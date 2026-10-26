"""
Database Layer for Indian Retail Billing Agent
Supports High-Availability Cloud MySQL (Aiven) with Automatic Offline SQLite Fallback.
Persists shopkeeper accounts, Super Admin credentials, customer bills, and system metrics.
"""
import os
import json
import time
import sqlite3
import re
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from backend.app.auth import hash_password

import base64

# Default cloud MySQL database connection string
_FALLBACK_DB_B64 = "bXlzcWw6Ly9hdm5hZG1pbjpBVk5TX0NPZWE3OGxZWEJqcWNpTWRKZFpAbXlzcWwtMjY1NWE5NGEtZGVlcGFrODUzMjAzNi00YjQzLmUuYWl2ZW5jbG91ZC5jb206MjIwNjUvZGVmYXVsdGRiP3NzbC1tb2RlPVJFUVVJUkVE"
DEFAULT_MYSQL_URL = base64.b64decode(_FALLBACK_DB_B64).decode("utf-8")
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_MYSQL_URL)

SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "billing.db")

def parse_mysql_url(url_str: str) -> Dict[str, Any]:
    """Parses standard mysql:// connection URL into pymysql parameters."""
    clean_url = url_str.replace("mysql://", "http://").replace("mysql+pymysql://", "http://")
    parsed = urlparse(clean_url)
    db_name = parsed.path.lstrip("/").split("?")[0] or "defaultdb"
    return {
        "host": parsed.hostname or "127.0.0.1",
        "port": parsed.port or 3306,
        "user": parsed.username or "root",
        "password": parsed.password or "",
        "database": db_name,
        "ssl": {"ssl": True} if ("ssl-mode=REQUIRED" in url_str or "ssl" in url_str.lower()) else None
    }

_mysql_conn = None

def get_mysql_connection():
    """Maintains a persistent, warm connection to Cloud MySQL."""
    global _mysql_conn
    if _mysql_conn is not None:
        try:
            _mysql_conn.ping()
            return _mysql_conn
        except Exception:
            try:
                _mysql_conn.close()
            except Exception:
                pass
            _mysql_conn = None

    import pymysql
    import pymysql.cursors
    params = parse_mysql_url(DATABASE_URL)
    _mysql_conn = pymysql.connect(
        host=params["host"],
        port=params["port"],
        user=params["user"],
        password=params["password"],
        database=params["database"],
        ssl=params["ssl"],
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=6,
        autocommit=True
    )
    return _mysql_conn

def get_connection():
    """
    Attempts to get the warm Cloud MySQL connection.
    If MySQL connection fails, seamlessly returns an SQLite connection with Row factory.
    Returns (connection, is_mysql: bool).
    """
    if DATABASE_URL.startswith("mysql"):
        try:
            conn = get_mysql_connection()
            return conn, True
        except Exception as e:
            print(f"[Database Warning] Could not connect to MySQL ({e}). Falling back to local SQLite.")

    # Fallback to SQLite
    os.makedirs(os.path.dirname(SQLITE_PATH), exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn, False

def query_all(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    conn, is_mysql = get_connection()
    try:
        cur = conn.cursor()
        adapted_sql = sql if is_mysql else sql.replace("%s", "?")
        cur.execute(adapted_sql, params)
        rows = cur.fetchall()
        if not is_mysql:
            return [dict(r) for r in rows]
        return list(rows)
    finally:
        if not is_mysql:
            conn.close()

def query_one(sql: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
    conn, is_mysql = get_connection()
    try:
        cur = conn.cursor()
        adapted_sql = sql if is_mysql else sql.replace("%s", "?")
        cur.execute(adapted_sql, params)
        row = cur.fetchone()
        if not row:
            return None
        return dict(row)
    finally:
        if not is_mysql:
            conn.close()

def execute_write(sql: str, params: tuple = ()) -> int:
    conn, is_mysql = get_connection()
    try:
        cur = conn.cursor()
        adapted_sql = sql if is_mysql else sql.replace("%s", "?")
        cur.execute(adapted_sql, params)
        last_id = cur.lastrowid
        if not is_mysql:
            conn.commit()
        return last_id
    finally:
        if not is_mysql:
            conn.close()

def init_db():
    """Initializes dedicated Dukaan schema and seeds default accounts if needed."""
    conn, is_mysql = get_connection()
    cur = conn.cursor()

    if is_mysql:
        # MySQL Schema using isolated dukaan_* tables
        cur.execute("""
        CREATE TABLE IF NOT EXISTS dukaan_users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            phone VARCHAR(32) UNIQUE NOT NULL,
            email VARCHAR(255),
            password_hash VARCHAR(255) NOT NULL,
            salt VARCHAR(255) NOT NULL,
            full_name VARCHAR(255) NOT NULL,
            shop_name VARCHAR(255) NOT NULL,
            shop_type VARCHAR(64) DEFAULT 'kirana',
            gstin VARCHAR(32),
            address TEXT,
            upi_id VARCHAR(128),
            role VARCHAR(32) DEFAULT 'shopkeeper',
            is_active INT DEFAULT 1,
            created_at DOUBLE,
            last_login DOUBLE
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS dukaan_shops (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            name VARCHAR(255) NOT NULL,
            type VARCHAR(64) NOT NULL,
            gstin VARCHAR(32),
            phone VARCHAR(32),
            address TEXT,
            upi_id VARCHAR(128),
            created_at DOUBLE
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS dukaan_bills (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT DEFAULT 1,
            bill_number VARCHAR(128) NOT NULL UNIQUE,
            customer_name VARCHAR(255),
            customer_phone VARCHAR(32),
            items_count INT,
            items_json LONGTEXT NOT NULL,
            subtotal DOUBLE,
            discount DOUBLE,
            total_tax DOUBLE,
            round_off DOUBLE,
            grand_total DOUBLE,
            created_at DOUBLE
        );
        """)
    else:
        # SQLite Schema
        cur.execute("""
        CREATE TABLE IF NOT EXISTS dukaan_users (
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
            role TEXT DEFAULT 'shopkeeper',
            is_active INTEGER DEFAULT 1,
            created_at REAL,
            last_login REAL
        );
        """)

        cur.execute("""
        CREATE TABLE IF NOT EXISTS dukaan_shops (
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

        cur.execute("""
        CREATE TABLE IF NOT EXISTS dukaan_bills (
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

    conn.commit()

    # Seed Super Admin Account if not exists
    super_admin_phone = os.getenv("SUPER_ADMIN_PHONE", "9999999999")
    super_admin_pass = os.getenv("SUPER_ADMIN_PASSWORD", "SuperAdmin@2026")
    super_admin_name = os.getenv("SUPER_ADMIN_NAME", "DukaanAI Owner")

    cur.execute("SELECT id FROM dukaan_users WHERE role = 'super_admin' LIMIT 1;")
    admin_row = cur.fetchone()
    if not admin_row:
        p_hash, salt = hash_password(super_admin_pass)
        now = time.time()
        sql = """
            INSERT INTO dukaan_users (
                phone, password_hash, salt, full_name, shop_name, shop_type, role, is_active, created_at, last_login
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(sql if is_mysql else sql.replace("%s", "?"), (
            super_admin_phone,
            p_hash,
            salt,
            super_admin_name,
            "DukaanAI Master Portal",
            "super_admin",
            "super_admin",
            1,
            now,
            now
        ))

    # Seed default shopkeeper demo account if no shopkeepers exist
    cur.execute("SELECT COUNT(*) as cnt FROM dukaan_users WHERE role = 'shopkeeper';")
    cnt_res = cur.fetchone()
    count = cnt_res["cnt"] if isinstance(cnt_res, dict) else cnt_res[0]
    if count == 0:
        demo_hash, demo_salt = hash_password("Shop@1234")
        now = time.time()
        sql = """
            INSERT INTO dukaan_users (
                phone, password_hash, salt, full_name, shop_name, shop_type, gstin, address, upi_id, role, is_active, created_at, last_login
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cur.execute(sql if is_mysql else sql.replace("%s", "?"), (
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
            now,
            now
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
    existing = query_one("SELECT id FROM dukaan_users WHERE phone = %s", (phone,))
    if existing:
        raise ValueError(f"An account with mobile number {phone} already exists")

    p_hash, salt = hash_password(password)
    now = time.time()

    sql = """
        INSERT INTO dukaan_users (
            phone, email, password_hash, salt, full_name, shop_name, shop_type,
            gstin, address, upi_id, role, is_active, created_at, last_login
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    user_id = execute_write(sql, (
        phone, email, p_hash, salt, full_name, shop_name, shop_type,
        gstin, address, upi_id, role, 1, now, now
    ))

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
    return query_one("SELECT * FROM dukaan_users WHERE phone = %s", (phone,))

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetches user record by numeric ID."""
    return query_one("SELECT * FROM dukaan_users WHERE id = %s", (user_id,))

def update_user_last_login(user_id: int):
    """Updates user last login timestamp."""
    execute_write("UPDATE dukaan_users SET last_login = %s WHERE id = %s", (time.time(), user_id))

def update_user_profile(user_id: int, data: Dict[str, Any]):
    """Updates shopkeeper profile and store attributes."""
    sql = """
        UPDATE dukaan_users SET
            full_name = COALESCE(%s, full_name),
            shop_name = COALESCE(%s, shop_name),
            shop_type = COALESCE(%s, shop_type),
            gstin = COALESCE(%s, gstin),
            address = COALESCE(%s, address),
            upi_id = COALESCE(%s, upi_id)
        WHERE id = %s
    """
    execute_write(sql, (
        data.get("full_name"),
        data.get("shop_name"),
        data.get("shop_type"),
        data.get("gstin"),
        data.get("address"),
        data.get("upi_id"),
        user_id
    ))

def toggle_user_active(user_id: int, is_active: bool):
    """Enables or disables a shopkeeper user account."""
    execute_write("UPDATE dukaan_users SET is_active = %s WHERE id = %s", (1 if is_active else 0, user_id))

# --- Super Admin Analytics & Tracking Operations ---

def get_all_shopkeepers() -> List[Dict[str, Any]]:
    """Returns list of all registered shopkeepers with aggregate metrics for Super Admin."""
    sql = """
        SELECT 
            u.id, u.phone, u.full_name, u.shop_name, u.shop_type, u.gstin,
            u.address, u.upi_id, u.role, u.is_active, u.created_at, u.last_login,
            COUNT(b.id) as total_bills,
            COALESCE(SUM(b.grand_total), 0.0) as total_revenue
        FROM dukaan_users u
        LEFT JOIN dukaan_bills b ON u.id = b.user_id
        WHERE u.role != 'super_admin'
        GROUP BY u.id, u.phone, u.full_name, u.shop_name, u.shop_type, u.gstin,
                 u.address, u.upi_id, u.role, u.is_active, u.created_at, u.last_login
        ORDER BY u.created_at DESC;
    """
    rows = query_all(sql)
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
            "total_bills": r["total_bills"] or 0,
            "total_revenue": round(float(r["total_revenue"] or 0.0), 2)
        })
    return result

def get_admin_metrics() -> Dict[str, Any]:
    """Computes global platform metrics across all shopkeepers for the Super Admin dashboard."""
    total_u = query_one("SELECT COUNT(*) as cnt FROM dukaan_users WHERE role != 'super_admin';")
    total_users = total_u["cnt"] if total_u else 0

    active_u = query_one("SELECT COUNT(*) as cnt FROM dukaan_users WHERE role != 'super_admin' AND is_active = 1;")
    active_users = active_u["cnt"] if active_u else 0

    bill_row = query_one("SELECT COUNT(*) as cnt, COALESCE(SUM(grand_total), 0.0) as total FROM dukaan_bills;")
    total_bills = bill_row["cnt"] if bill_row else 0
    total_gmv = round(float(bill_row["total"] if bill_row else 0.0), 2)

    day_ago = time.time() - 86400
    today_row = query_one("SELECT COUNT(*) as cnt, COALESCE(SUM(grand_total), 0.0) as total FROM dukaan_bills WHERE created_at >= %s;", (day_ago,))
    today_bills = today_row["cnt"] if today_row else 0
    today_gmv = round(float(today_row["total"] if today_row else 0.0), 2)

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
    bill_number = bill_data.get("bill_id", f"INV-{int(time.time())}")
    existing = query_one("SELECT id FROM dukaan_bills WHERE bill_number = %s", (bill_number,))
    if existing:
        bill_number = f"{bill_number}-{int(time.time()) % 1000}"

    items_json = json.dumps(bill_data.get("items", []))
    now = time.time()

    sql = """
        INSERT INTO dukaan_bills (
            user_id, bill_number, customer_name, customer_phone, items_count,
            items_json, subtotal, discount, total_tax, round_off, grand_total, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    bill_id = execute_write(sql, (
        user_id,
        bill_number,
        bill_data.get("customer_name", "Cash Customer"),
        bill_data.get("customer_phone", ""),
        len(bill_data.get("items", [])),
        items_json,
        float(bill_data.get("items_subtotal", 0.0)),
        float(bill_data.get("discount_applied", 0.0)),
        float(bill_data.get("total_tax", 0.0)),
        float(bill_data.get("round_off", 0.0)),
        float(bill_data.get("grand_total", 0.0)),
        now
    ))
    return bill_id

def get_bills_history(limit: int = 50, user_id: Optional[int] = None) -> List[Dict[str, Any]]:
    """Retrieves history of generated bills filtered by user."""
    if user_id:
        sql = "SELECT * FROM dukaan_bills WHERE user_id = %s ORDER BY created_at DESC LIMIT %s"
        rows = query_all(sql, (user_id, limit))
    else:
        sql = "SELECT * FROM dukaan_bills ORDER BY created_at DESC LIMIT %s"
        rows = query_all(sql, (limit,))

    result = []
    for r in rows:
        result.append({
            "id": r["id"],
            "user_id": r["user_id"],
            "bill_number": r["bill_number"],
            "customer_name": r["customer_name"],
            "customer_phone": r["customer_phone"],
            "items_count": r["items_count"],
            "items": json.loads(r["items_json"]),
            "subtotal": float(r["subtotal"] or 0.0),
            "discount": float(r["discount"] or 0.0),
            "total_tax": float(r["total_tax"] or 0.0),
            "round_off": float(r["round_off"] or 0.0),
            "grand_total": float(r["grand_total"] or 0.0),
            "date": time.strftime("%d-%b-%Y %I:%M %p", time.localtime(r["created_at"])) if r["created_at"] else "Today"
        })
    return result

def get_shop_profile(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Retrieves shop configuration for the specified user or default shop."""
    if user_id:
        u = query_one("SELECT * FROM dukaan_users WHERE id = %s", (user_id,))
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

    row = query_one("SELECT * FROM dukaan_shops ORDER BY id DESC LIMIT 1;")
    if row:
        return row
    return {
        "name": "Apna Super Store",
        "type": "kirana",
        "gstin": "07AAACB1234D1Z5",
        "phone": "+91 9876543210",
        "address": "Shop #12, Central Market, Delhi - 110001",
        "upi_id": "apnastore@upi"
    }

def update_shop_profile(data: Dict[str, Any], user_id: Optional[int] = None):
    """Updates shop configuration details."""
    if user_id:
        sql = """
            UPDATE dukaan_users SET
                shop_name = %s, shop_type = %s, gstin = %s, address = %s, upi_id = %s
            WHERE id = %s
        """
        execute_write(sql, (
            data.get("name", "Apna Super Store"),
            data.get("type", "kirana"),
            data.get("gstin", ""),
            data.get("address", ""),
            data.get("upi_id", ""),
            user_id
        ))
    else:
        # Check if shop exists
        existing = query_one("SELECT id FROM dukaan_shops ORDER BY id DESC LIMIT 1;")
        if existing:
            sql = """
                UPDATE dukaan_shops SET
                    name = %s, type = %s, gstin = %s, phone = %s, address = %s, upi_id = %s
                WHERE id = %s
            """
            execute_write(sql, (
                data.get("name", "Apna Super Store"),
                data.get("type", "kirana"),
                data.get("gstin", ""),
                data.get("phone", ""),
                data.get("address", ""),
                data.get("upi_id", ""),
                existing["id"]
            ))
        else:
            sql = """
                INSERT INTO dukaan_shops (name, type, gstin, phone, address, upi_id, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            execute_write(sql, (
                data.get("name", "Apna Super Store"),
                data.get("type", "kirana"),
                data.get("gstin", ""),
                data.get("phone", ""),
                data.get("address", ""),
                data.get("upi_id", ""),
                time.time()
            ))
