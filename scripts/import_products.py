#!/usr/bin/env python3
"""
Import products from CSV file into the database.

Usage:
    python scripts/import_products.py data/products.csv
    python scripts/import_products.py --clear data/products.csv  # Clear existing first
"""

import argparse
import csv
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import init_database, get_connection, get_active_products


def clear_products():
    """Clear all products from database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products")
    conn.commit()
    conn.close()
    print("Cleared existing products")


def import_products(csv_path: str, clear_first: bool = False):
    """Import products from CSV file."""
    init_database()

    if clear_first:
        clear_products()

    conn = get_connection()
    cursor = conn.cursor()

    imported = 0
    updated = 0
    errors = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)

        # Validate headers
        required = {'sku', 'name', 'category', 'price_per_lb'}
        if not required.issubset(set(reader.fieldnames or [])):
            print(f"Error: CSV must have columns: {required}")
            print(f"Found: {reader.fieldnames}")
            return

        for i, row in enumerate(reader, start=2):
            try:
                sku = row['sku'].strip().zfill(5)
                name = row['name'].strip()
                category = row['category'].strip()
                price = float(row['price_per_lb'])

                if not name:
                    errors.append(f"Row {i}: Empty name")
                    continue

                if price <= 0:
                    errors.append(f"Row {i}: Invalid price {price}")
                    continue

                # Check if exists
                cursor.execute("SELECT id FROM products WHERE sku = ?", (sku,))
                existing = cursor.fetchone()

                if existing:
                    cursor.execute("""
                        UPDATE products
                        SET name = ?, category = ?, price_per_lb = ?, active = 1
                        WHERE sku = ?
                    """, (name, category, price, sku))
                    updated += 1
                else:
                    cursor.execute("""
                        INSERT INTO products (sku, name, category, price_per_lb, active)
                        VALUES (?, ?, ?, ?, 1)
                    """, (sku, name, category, price))
                    imported += 1

            except Exception as e:
                errors.append(f"Row {i}: {e}")

    conn.commit()
    conn.close()

    print(f"Imported: {imported}")
    print(f"Updated: {updated}")
    if errors:
        print(f"Errors: {len(errors)}")
        for err in errors[:10]:
            print(f"  {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")


def list_products():
    """List all products in database."""
    products = get_active_products()
    if not products:
        print("No products in database")
        return

    print(f"\n{'SKU':<8} {'Name':<30} {'Category':<12} {'Price':>8}")
    print("-" * 60)
    for p in products:
        print(f"{p.sku:<8} {p.name[:28]:<30} {p.category:<12} ${p.price_per_lb:>6.2f}")
    print(f"\nTotal: {len(products)} products")


def main():
    parser = argparse.ArgumentParser(description='Import products from CSV')
    parser.add_argument('csv_file', nargs='?', help='CSV file to import')
    parser.add_argument('--clear', action='store_true', help='Clear existing products first')
    parser.add_argument('--list', action='store_true', help='List current products')
    args = parser.parse_args()

    if args.list:
        init_database()
        list_products()
        return

    if not args.csv_file:
        parser.print_help()
        return

    if not Path(args.csv_file).exists():
        print(f"Error: File not found: {args.csv_file}")
        return

    import_products(args.csv_file, args.clear)
    list_products()


if __name__ == '__main__':
    main()
