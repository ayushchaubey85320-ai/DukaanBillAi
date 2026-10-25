"""
SQLite Database Layer for Indian Retail Billing Agent
Persists shopkeeper profiles, customer bills, line-items, and invoice history.
"""
import sqlite3
import json
import os
import time
from typing import Dict, Any, List, Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "billing.db")

def get_db_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes SQLite schema if not already present."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS shops (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        type TEXT NOT NULL,
        gstin TEXT,
        phone TEXT,
        address TEXT,
        upi_id TEXT,
        created_at REAL
    );
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
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

    # Seed default shop if empty
    cursor.execute("SELECT COUNT(*) FROM shops;")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO shops (name, type, gstin, phone, address, upi_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            "Apna Super Store",
            "kirana",
            "07AAACB1234D1Z5",
            "+91 9876543210",
            "Shop #12, Central Market, Delhi - 110001",
            "apnastore@upi",
            time.time()
        ))

    conn.commit()
    conn.close()

def save_bill_record(bill_data: Dict[str, Any]) -> int:
    """Saves a finalized bill to the database."""
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
            bill_number, customer_name, customer_phone, items_count,
            items_json, subtotal, discount, total_tax, round_off, grand_total, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
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

def get_bills_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves recent bills for history view and reprints."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM bills ORDER BY created_at DESC LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    
    result = []
    for r in rows:
        result.append({
            "id": r["id"],
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
    conn.close()
    return result

def get_shop_profile() -> Dict[str, Any]:
    """Retrieves current shop configuration."""
    conn = get_db_connection()
    cursor = conn.cursor()
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

def update_shop_profile(data: Dict[str, Any]):
    """Updates shop configuration details."""
    conn = get_db_connection()
    cursor = conn.cursor()
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
