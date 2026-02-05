"""
Database module for Pomponio Ranch Labeling System.
SQLite database with models for products, packages, boxes, and orders.
"""

import sqlite3
from pathlib import Path
from datetime import datetime, date
from typing import Optional
from dataclasses import dataclass


DB_PATH = Path(__file__).parent.parent / "data" / "pomponio.db"


@dataclass
class Product:
    id: int
    sku: str
    name: str
    category: str
    price_per_lb: float
    active: bool = True


@dataclass
class Package:
    id: int
    product_id: int
    weight_lbs: float
    barcode: str
    box_id: Optional[int]
    created_at: datetime
    verified: bool = False

    # Joined fields
    product_name: Optional[str] = None
    product_sku: Optional[str] = None


@dataclass
class Box:
    id: int
    box_number: str
    total_weight: float
    package_count: int
    qr_data: str
    order_id: Optional[int]
    created_at: datetime
    closed_at: Optional[datetime]
    verified: bool = False


@dataclass
class Order:
    id: int
    customer_name: str
    order_date: date
    pickup_date: Optional[date]
    status: str
    created_at: datetime
    completed_at: Optional[datetime]


@dataclass
class ScanLog:
    id: int
    scan_type: str
    reference_id: int
    barcode_data: str
    success: bool
    scanned_at: datetime


def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            price_per_lb REAL NOT NULL,
            active INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            weight_lbs REAL NOT NULL,
            barcode TEXT UNIQUE NOT NULL,
            box_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            verified INTEGER DEFAULT 0,
            FOREIGN KEY (product_id) REFERENCES products(id),
            FOREIGN KEY (box_id) REFERENCES boxes(id)
        );

        CREATE TABLE IF NOT EXISTS boxes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            box_number TEXT UNIQUE NOT NULL,
            total_weight REAL DEFAULT 0,
            package_count INTEGER DEFAULT 0,
            qr_data TEXT,
            order_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            closed_at DATETIME,
            verified INTEGER DEFAULT 0,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            order_date DATE NOT NULL,
            pickup_date DATE,
            status TEXT DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME
        );

        CREATE TABLE IF NOT EXISTS scan_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_type TEXT NOT NULL,
            reference_id INTEGER NOT NULL,
            barcode_data TEXT NOT NULL,
            success INTEGER NOT NULL,
            scanned_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_packages_box_id ON packages(box_id);
        CREATE INDEX IF NOT EXISTS idx_packages_barcode ON packages(barcode);
        CREATE INDEX IF NOT EXISTS idx_boxes_order_id ON boxes(order_id);
        CREATE INDEX IF NOT EXISTS idx_boxes_box_number ON boxes(box_number);
        CREATE INDEX IF NOT EXISTS idx_scan_log_type ON scan_log(scan_type, reference_id);
    """)

    conn.commit()
    conn.close()


# Product operations

def get_active_products() -> list[Product]:
    """Get all active products."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sku, name, category, price_per_lb, active
        FROM products
        WHERE active = 1
        ORDER BY category, name
    """)
    products = [Product(**dict(row)) for row in cursor.fetchall()]
    conn.close()
    return products


def get_products_by_category() -> dict[str, list[Product]]:
    """Get active products grouped by category."""
    products = get_active_products()
    by_category = {}
    for p in products:
        if p.category not in by_category:
            by_category[p.category] = []
        by_category[p.category].append(p)
    return by_category


def get_product_by_sku(sku: str) -> Optional[Product]:
    """Get product by SKU."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sku, name, category, price_per_lb, active
        FROM products WHERE sku = ?
    """, (sku,))
    row = cursor.fetchone()
    conn.close()
    return Product(**dict(row)) if row else None


def get_product_by_id(product_id: int) -> Optional[Product]:
    """Get product by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, sku, name, category, price_per_lb, active
        FROM products WHERE id = ?
    """, (product_id,))
    row = cursor.fetchone()
    conn.close()
    return Product(**dict(row)) if row else None


def import_products_from_csv(csv_path: str):
    """Import products from CSV file. Format: sku,name,category,price_per_lb"""
    import csv

    conn = get_connection()
    cursor = conn.cursor()

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT OR REPLACE INTO products (sku, name, category, price_per_lb, active)
                VALUES (?, ?, ?, ?, 1)
            """, (
                row['sku'].zfill(5),
                row['name'],
                row['category'],
                float(row['price_per_lb'])
            ))

    conn.commit()
    conn.close()


# Package operations

def create_package(product_id: int, weight_lbs: float, barcode: str) -> int:
    """Create a new package. Returns package ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO packages (product_id, weight_lbs, barcode)
        VALUES (?, ?, ?)
    """, (product_id, weight_lbs, barcode))
    package_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return package_id


def verify_package(package_id: int):
    """Mark package as verified."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE packages SET verified = 1 WHERE id = ?", (package_id,))
    conn.commit()
    conn.close()


def get_package_by_barcode(barcode: str) -> Optional[Package]:
    """Get package by barcode."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.product_id, p.weight_lbs, p.barcode, p.box_id,
               p.created_at, p.verified, pr.name as product_name, pr.sku as product_sku
        FROM packages p
        JOIN products pr ON p.product_id = pr.id
        WHERE p.barcode = ?
    """, (barcode,))
    row = cursor.fetchone()
    conn.close()
    return Package(**dict(row)) if row else None


def assign_package_to_box(package_id: int, box_id: int):
    """Assign a package to a box."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE packages SET box_id = ? WHERE id = ?", (box_id, package_id))
    conn.commit()
    conn.close()


def get_unboxed_packages() -> list[Package]:
    """Get all packages not yet assigned to a box."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.product_id, p.weight_lbs, p.barcode, p.box_id,
               p.created_at, p.verified, pr.name as product_name, pr.sku as product_sku
        FROM packages p
        JOIN products pr ON p.product_id = pr.id
        WHERE p.box_id IS NULL
        ORDER BY p.created_at DESC
    """)
    packages = [Package(**dict(row)) for row in cursor.fetchall()]
    conn.close()
    return packages


# Box operations

def create_box() -> int:
    """Create a new box. Returns box ID."""
    conn = get_connection()
    cursor = conn.cursor()

    today = date.today().strftime("%Y%m%d")
    cursor.execute("""
        SELECT COUNT(*) + 1 as seq FROM boxes
        WHERE box_number LIKE ?
    """, (f"{today}-%",))
    seq = cursor.fetchone()['seq']

    box_number = f"{today}-{seq:03d}"

    cursor.execute("""
        INSERT INTO boxes (box_number, total_weight, package_count)
        VALUES (?, 0, 0)
    """, (box_number,))
    box_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return box_id


def get_current_box() -> Optional[Box]:
    """Get the current open box (most recent unclosed)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, box_number, total_weight, package_count, qr_data,
               order_id, created_at, closed_at, verified
        FROM boxes
        WHERE closed_at IS NULL
        ORDER BY created_at DESC
        LIMIT 1
    """)
    row = cursor.fetchone()
    conn.close()
    return Box(**dict(row)) if row else None


def get_box_by_id(box_id: int) -> Optional[Box]:
    """Get box by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, box_number, total_weight, package_count, qr_data,
               order_id, created_at, closed_at, verified
        FROM boxes WHERE id = ?
    """, (box_id,))
    row = cursor.fetchone()
    conn.close()
    return Box(**dict(row)) if row else None


def get_box_by_number(box_number: str) -> Optional[Box]:
    """Get box by box number."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, box_number, total_weight, package_count, qr_data,
               order_id, created_at, closed_at, verified
        FROM boxes WHERE box_number = ?
    """, (box_number,))
    row = cursor.fetchone()
    conn.close()
    return Box(**dict(row)) if row else None


def get_packages_in_box(box_id: int) -> list[Package]:
    """Get all packages in a box."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.id, p.product_id, p.weight_lbs, p.barcode, p.box_id,
               p.created_at, p.verified, pr.name as product_name, pr.sku as product_sku
        FROM packages p
        JOIN products pr ON p.product_id = pr.id
        WHERE p.box_id = ?
        ORDER BY p.created_at
    """, (box_id,))
    packages = [Package(**dict(row)) for row in cursor.fetchall()]
    conn.close()
    return packages


def update_box_totals(box_id: int):
    """Recalculate box totals from packages."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE boxes SET
            total_weight = (SELECT COALESCE(SUM(weight_lbs), 0) FROM packages WHERE box_id = ?),
            package_count = (SELECT COUNT(*) FROM packages WHERE box_id = ?)
        WHERE id = ?
    """, (box_id, box_id, box_id))
    conn.commit()
    conn.close()


def close_box(box_id: int, qr_data: str):
    """Close a box with QR data."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE boxes SET closed_at = CURRENT_TIMESTAMP, qr_data = ?
        WHERE id = ?
    """, (qr_data, box_id))
    conn.commit()
    conn.close()


def verify_box(box_id: int):
    """Mark box as verified."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE boxes SET verified = 1 WHERE id = ?", (box_id,))
    conn.commit()
    conn.close()


def assign_box_to_order(box_id: int, order_id: int):
    """Assign a box to an order."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE boxes SET order_id = ? WHERE id = ?", (order_id, box_id))
    conn.commit()
    conn.close()


# Order operations

def create_order(customer_name: str) -> int:
    """Create a new order. Returns order ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO orders (customer_name, order_date)
        VALUES (?, DATE('now'))
    """, (customer_name,))
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return order_id


def get_pending_orders() -> list[Order]:
    """Get all pending orders."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, customer_name, order_date, pickup_date, status,
               created_at, completed_at
        FROM orders
        WHERE status IN ('pending', 'ready')
        ORDER BY order_date
    """)
    orders = [Order(**dict(row)) for row in cursor.fetchall()]
    conn.close()
    return orders


def get_order_by_id(order_id: int) -> Optional[Order]:
    """Get order by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, customer_name, order_date, pickup_date, status,
               created_at, completed_at
        FROM orders WHERE id = ?
    """, (order_id,))
    row = cursor.fetchone()
    conn.close()
    return Order(**dict(row)) if row else None


def get_boxes_for_order(order_id: int) -> list[Box]:
    """Get all boxes assigned to an order."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, box_number, total_weight, package_count, qr_data,
               order_id, created_at, closed_at, verified
        FROM boxes
        WHERE order_id = ?
        ORDER BY box_number
    """, (order_id,))
    boxes = [Box(**dict(row)) for row in cursor.fetchall()]
    conn.close()
    return boxes


def update_order_status(order_id: int, status: str):
    """Update order status."""
    conn = get_connection()
    cursor = conn.cursor()
    if status == 'picked_up':
        cursor.execute("""
            UPDATE orders SET status = ?, completed_at = CURRENT_TIMESTAMP,
                             pickup_date = DATE('now')
            WHERE id = ?
        """, (status, order_id))
    else:
        cursor.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
    conn.commit()
    conn.close()


# Scan logging

def log_scan(scan_type: str, reference_id: int, barcode_data: str, success: bool):
    """Log a scan event."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO scan_log (scan_type, reference_id, barcode_data, success)
        VALUES (?, ?, ?, ?)
    """, (scan_type, reference_id, barcode_data, 1 if success else 0))
    conn.commit()
    conn.close()


def get_scan_history(scan_type: str = None, limit: int = 100) -> list[ScanLog]:
    """Get scan history, optionally filtered by type."""
    conn = get_connection()
    cursor = conn.cursor()
    if scan_type:
        cursor.execute("""
            SELECT id, scan_type, reference_id, barcode_data, success, scanned_at
            FROM scan_log
            WHERE scan_type = ?
            ORDER BY scanned_at DESC
            LIMIT ?
        """, (scan_type, limit))
    else:
        cursor.execute("""
            SELECT id, scan_type, reference_id, barcode_data, success, scanned_at
            FROM scan_log
            ORDER BY scanned_at DESC
            LIMIT ?
        """, (limit,))
    logs = [ScanLog(**dict(row)) for row in cursor.fetchall()]
    conn.close()
    return logs


if __name__ == "__main__":
    init_database()
    print(f"Database initialized at {DB_PATH}")
