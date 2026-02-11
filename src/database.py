"""SQLite database for Pomponio Ranch Labeling System.

Tables: products, animals, boxes, packages, scan_log.
Schema matches PRD Section 8.
"""

import csv
import logging
import os
import sqlite3
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    category TEXT NOT NULL,
    unit TEXT NOT NULL,
    active BOOLEAN DEFAULT 1
);

CREATE TABLE IF NOT EXISTS animals (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    species TEXT DEFAULT 'Beef',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    manifest_path TEXT
);

CREATE TABLE IF NOT EXISTS boxes (
    id INTEGER PRIMARY KEY,
    animal_id INTEGER REFERENCES animals(id),
    box_number INTEGER NOT NULL,
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS packages (
    id INTEGER PRIMARY KEY,
    product_id INTEGER REFERENCES products(id),
    animal_id INTEGER REFERENCES animals(id),
    box_id INTEGER REFERENCES boxes(id),
    weight_lb REAL NOT NULL,
    barcode TEXT NOT NULL,
    label_printed_at TIMESTAMP,
    scan_verified_at TIMESTAMP,
    scan_matched BOOLEAN
);

CREATE TABLE IF NOT EXISTS scan_log (
    id INTEGER PRIMARY KEY,
    scanned_barcode TEXT NOT NULL,
    expected_barcode TEXT,
    matched BOOLEAN,
    scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


class Database:
    """SQLite database manager for the labeling system."""

    def __init__(self, db_path: str = "pomponio.db"):
        self.db_path = db_path
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        """Open database connection and initialize schema."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.executescript(SCHEMA_SQL)
        self.conn.commit()
        logger.info("Database connected: %s", self.db_path)

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def _ensure_connected(self) -> sqlite3.Connection:
        if self.conn is None:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.conn

    # --- Products ---

    def import_products_from_csv(self, csv_path: str) -> int:
        """Import products from CSV into the products table.

        Skips rows with duplicate SKU codes already in the database.
        Rejects CSV rows where the same SKU appears more than once in the file.

        Args:
            csv_path: Path to pomponio_skus.csv.

        Returns:
            Number of products imported.

        Raises:
            FileNotFoundError: If CSV does not exist.
            ValueError: If CSV contains duplicate SKU codes.
        """
        conn = self._ensure_connected()

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"CSV not found: {csv_path}")

        rows = []
        seen_skus: dict[str, str] = {}

        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sku = row["sku"].strip()
                name = row["name"].strip()

                if sku in seen_skus:
                    raise ValueError(
                        f"Duplicate SKU in CSV: {sku} "
                        f"('{seen_skus[sku]}' and '{name}')"
                    )
                seen_skus[sku] = name

                active = row["active"].strip().lower() == "true"
                rows.append((sku, name, row["category"].strip(), row["unit"].strip(), active))

        imported = 0
        for sku, name, category, unit, active in rows:
            try:
                conn.execute(
                    "INSERT INTO products (sku, name, category, unit, active) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (sku, name, category, unit, active),
                )
                imported += 1
            except sqlite3.IntegrityError:
                logger.warning("SKU %s already exists, skipping", sku)

        conn.commit()
        logger.info("Imported %d products from %s", imported, csv_path)
        return imported

    def get_product_by_sku(self, sku: str) -> Optional[dict]:
        """Look up a product by SKU code."""
        conn = self._ensure_connected()
        row = conn.execute(
            "SELECT * FROM products WHERE sku = ?", (sku,)
        ).fetchone()
        return dict(row) if row else None

    def get_products_by_category(self, category: str, active_only: bool = True) -> list[dict]:
        """Get all products in a category."""
        conn = self._ensure_connected()
        if active_only:
            rows = conn.execute(
                "SELECT * FROM products WHERE category = ? AND active = 1 ORDER BY name",
                (category,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM products WHERE category = ? ORDER BY name",
                (category,),
            ).fetchall()
        return [dict(r) for r in rows]

    def get_all_active_products(self) -> list[dict]:
        """Get all active products ordered by category then name."""
        conn = self._ensure_connected()
        rows = conn.execute(
            "SELECT * FROM products WHERE active = 1 ORDER BY category, name"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_categories(self) -> list[str]:
        """Get distinct categories from active products."""
        conn = self._ensure_connected()
        rows = conn.execute(
            "SELECT DISTINCT category FROM products WHERE active = 1 ORDER BY category"
        ).fetchall()
        return [r["category"] for r in rows]

    # --- Animals ---

    def create_animal(self, name: str, species: str = "Beef") -> int:
        """Start tracking a new animal. Returns the animal ID."""
        conn = self._ensure_connected()
        cursor = conn.execute(
            "INSERT INTO animals (name, species) VALUES (?, ?)",
            (name, species),
        )
        conn.commit()
        return cursor.lastrowid

    def close_animal(self, animal_id: int, manifest_path: Optional[str] = None) -> None:
        """Mark an animal as complete."""
        conn = self._ensure_connected()
        conn.execute(
            "UPDATE animals SET closed_at = CURRENT_TIMESTAMP, manifest_path = ? "
            "WHERE id = ?",
            (manifest_path, animal_id),
        )
        conn.commit()

    def get_animal(self, animal_id: int) -> Optional[dict]:
        conn = self._ensure_connected()
        row = conn.execute("SELECT * FROM animals WHERE id = ?", (animal_id,)).fetchone()
        return dict(row) if row else None

    def get_open_animals(self) -> list[dict]:
        """Get all animals that have not been closed."""
        conn = self._ensure_connected()
        rows = conn.execute(
            "SELECT * FROM animals WHERE closed_at IS NULL ORDER BY started_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    # --- Boxes ---

    def create_box(self, animal_id: int) -> int:
        """Open a new box for an animal. Auto-increments box_number within the animal."""
        conn = self._ensure_connected()
        row = conn.execute(
            "SELECT COALESCE(MAX(box_number), 0) + 1 AS next_num "
            "FROM boxes WHERE animal_id = ?",
            (animal_id,),
        ).fetchone()
        next_num = row["next_num"]
        cursor = conn.execute(
            "INSERT INTO boxes (animal_id, box_number) VALUES (?, ?)",
            (animal_id, next_num),
        )
        conn.commit()
        return cursor.lastrowid

    def close_box(self, box_id: int) -> None:
        """Mark a box as closed."""
        conn = self._ensure_connected()
        conn.execute(
            "UPDATE boxes SET closed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (box_id,),
        )
        conn.commit()

    def get_box(self, box_id: int) -> Optional[dict]:
        conn = self._ensure_connected()
        row = conn.execute("SELECT * FROM boxes WHERE id = ?", (box_id,)).fetchone()
        return dict(row) if row else None

    def get_open_boxes(self, animal_id: Optional[int] = None) -> list[dict]:
        """Get open boxes, optionally filtered by animal."""
        conn = self._ensure_connected()
        if animal_id is not None:
            rows = conn.execute(
                "SELECT * FROM boxes WHERE animal_id = ? AND closed_at IS NULL "
                "ORDER BY box_number",
                (animal_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM boxes WHERE closed_at IS NULL ORDER BY opened_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    # --- Packages ---

    def create_package(
        self,
        product_id: int,
        animal_id: int,
        box_id: int,
        weight_lb: float,
        barcode: str,
    ) -> int:
        """Record a new labeled package. Returns the package ID."""
        conn = self._ensure_connected()
        cursor = conn.execute(
            "INSERT INTO packages (product_id, animal_id, box_id, weight_lb, barcode, "
            "label_printed_at) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)",
            (product_id, animal_id, box_id, weight_lb, barcode),
        )
        conn.commit()
        return cursor.lastrowid

    def mark_package_verified(self, package_id: int, matched: bool) -> None:
        """Record scan verification result for a package."""
        conn = self._ensure_connected()
        conn.execute(
            "UPDATE packages SET scan_verified_at = CURRENT_TIMESTAMP, "
            "scan_matched = ? WHERE id = ?",
            (matched, package_id),
        )
        conn.commit()

    def get_packages_for_box(self, box_id: int) -> list[dict]:
        """Get all packages in a box with product details."""
        conn = self._ensure_connected()
        rows = conn.execute(
            "SELECT p.*, pr.sku, pr.name AS product_name, pr.category "
            "FROM packages p "
            "JOIN products pr ON p.product_id = pr.id "
            "WHERE p.box_id = ? ORDER BY p.id",
            (box_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_packages_for_animal(self, animal_id: int) -> list[dict]:
        """Get all packages for an animal with product details."""
        conn = self._ensure_connected()
        rows = conn.execute(
            "SELECT p.*, pr.sku, pr.name AS product_name, pr.category "
            "FROM packages p "
            "JOIN products pr ON p.product_id = pr.id "
            "WHERE p.animal_id = ? ORDER BY p.id",
            (animal_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_box_summary(self, box_id: int) -> list[dict]:
        """Get per-SKU summary for a box (for box label printing).

        Returns list of dicts with: sku, product_name, quantity, total_weight.
        """
        conn = self._ensure_connected()
        rows = conn.execute(
            "SELECT pr.sku, pr.name AS product_name, "
            "COUNT(*) AS quantity, SUM(p.weight_lb) AS total_weight "
            "FROM packages p "
            "JOIN products pr ON p.product_id = pr.id "
            "WHERE p.box_id = ? "
            "GROUP BY pr.sku ORDER BY pr.name",
            (box_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_animal_manifest_data(self, animal_id: int) -> list[dict]:
        """Get per-SKU manifest data for an animal.

        Returns list of dicts with: sku, product_name, quantity, weights (list), total_weight.
        """
        conn = self._ensure_connected()
        rows = conn.execute(
            "SELECT pr.sku, pr.name AS product_name, p.weight_lb "
            "FROM packages p "
            "JOIN products pr ON p.product_id = pr.id "
            "WHERE p.animal_id = ? ORDER BY pr.sku, p.id",
            (animal_id,),
        ).fetchall()

        manifest: dict[str, dict] = {}
        for row in rows:
            sku = row["sku"]
            if sku not in manifest:
                manifest[sku] = {
                    "sku": sku,
                    "product_name": row["product_name"],
                    "quantity": 0,
                    "weights": [],
                    "total_weight": 0.0,
                }
            manifest[sku]["quantity"] += 1
            manifest[sku]["weights"].append(row["weight_lb"])
            manifest[sku]["total_weight"] += row["weight_lb"]

        return sorted(manifest.values(), key=lambda x: x["sku"])

    # --- Scan Log ---

    def log_scan(
        self, scanned_barcode: str, expected_barcode: Optional[str], matched: bool
    ) -> int:
        """Record a barcode scan event. Returns the log entry ID."""
        conn = self._ensure_connected()
        cursor = conn.execute(
            "INSERT INTO scan_log (scanned_barcode, expected_barcode, matched) "
            "VALUES (?, ?, ?)",
            (scanned_barcode, expected_barcode, matched),
        )
        conn.commit()
        return cursor.lastrowid
