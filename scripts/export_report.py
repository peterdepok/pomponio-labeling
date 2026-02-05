#!/usr/bin/env python3
"""
Export reports from the Pomponio database.

Usage:
    python scripts/export_report.py daily           # Today's activity
    python scripts/export_report.py daily 2026-02-04  # Specific date
    python scripts/export_report.py inventory       # Current inventory by box
    python scripts/export_report.py orders          # Pending orders summary
"""

import argparse
import csv
import sys
from pathlib import Path
from datetime import datetime, date, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import (
    init_database, get_connection,
    get_pending_orders, get_boxes_for_order, get_packages_in_box
)


REPORTS_DIR = Path(__file__).parent.parent / "data" / "reports"


def daily_report(report_date: date = None):
    """Generate daily activity report."""
    report_date = report_date or date.today()
    date_str = report_date.strftime("%Y-%m-%d")

    conn = get_connection()
    cursor = conn.cursor()

    # Packages created today
    cursor.execute("""
        SELECT p.id, pr.sku, pr.name, p.weight_lbs, p.barcode, p.verified,
               p.created_at, b.box_number
        FROM packages p
        JOIN products pr ON p.product_id = pr.id
        LEFT JOIN boxes b ON p.box_id = b.id
        WHERE DATE(p.created_at) = ?
        ORDER BY p.created_at
    """, (date_str,))
    packages = cursor.fetchall()

    # Boxes created today
    cursor.execute("""
        SELECT id, box_number, package_count, total_weight, closed_at, verified
        FROM boxes
        WHERE DATE(created_at) = ?
        ORDER BY created_at
    """, (date_str,))
    boxes = cursor.fetchall()

    # Orders completed today
    cursor.execute("""
        SELECT id, customer_name, status, completed_at
        FROM orders
        WHERE DATE(pickup_date) = ?
        ORDER BY completed_at
    """, (date_str,))
    orders = cursor.fetchall()

    conn.close()

    # Print report
    print(f"\n{'=' * 60}")
    print(f"DAILY REPORT: {date_str}")
    print(f"{'=' * 60}\n")

    print(f"PACKAGES LABELED: {len(packages)}")
    print("-" * 40)
    total_weight = 0
    for pkg in packages:
        verified = "OK" if pkg['verified'] else "--"
        box = pkg['box_number'] or "unboxed"
        print(f"  {pkg['sku']} {pkg['name'][:20]:<20} {pkg['weight_lbs']:>6.2f} lb  [{verified}] {box}")
        total_weight += pkg['weight_lbs']
    print(f"  {'TOTAL':<28} {total_weight:>6.2f} lb")

    print(f"\nBOXES CLOSED: {sum(1 for b in boxes if b['closed_at'])}/{len(boxes)}")
    print("-" * 40)
    for box in boxes:
        status = "CLOSED" if box['closed_at'] else "OPEN"
        verified = "OK" if box['verified'] else "--"
        print(f"  {box['box_number']}  {box['package_count']:>3} pkgs  {box['total_weight']:>6.2f} lb  {status} [{verified}]")

    print(f"\nORDERS PICKED UP: {len(orders)}")
    print("-" * 40)
    for order in orders:
        print(f"  {order['customer_name']}")

    # Export to CSV
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = REPORTS_DIR / f"daily_{date_str}.csv"

    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['SKU', 'Product', 'Weight', 'Barcode', 'Verified', 'Box', 'Time'])
        for pkg in packages:
            writer.writerow([
                pkg['sku'], pkg['name'], pkg['weight_lbs'], pkg['barcode'],
                'Yes' if pkg['verified'] else 'No', pkg['box_number'] or '',
                pkg['created_at']
            ])

    print(f"\nExported to: {csv_path}")


def inventory_report():
    """Generate current inventory report by box."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get all open boxes
    cursor.execute("""
        SELECT id, box_number, package_count, total_weight, order_id
        FROM boxes
        WHERE closed_at IS NOT NULL AND order_id IS NULL
        ORDER BY box_number
    """)
    boxes = cursor.fetchall()

    print(f"\n{'=' * 60}")
    print("INVENTORY REPORT: Boxes Ready for Orders")
    print(f"{'=' * 60}\n")

    total_boxes = 0
    total_packages = 0
    total_weight = 0.0

    for box in boxes:
        print(f"\nBox: {box['box_number']}")
        print(f"  Packages: {box['package_count']}")
        print(f"  Weight: {box['total_weight']:.2f} lb")

        # Get packages in box
        cursor.execute("""
            SELECT pr.sku, pr.name, p.weight_lbs
            FROM packages p
            JOIN products pr ON p.product_id = pr.id
            WHERE p.box_id = ?
            ORDER BY pr.name
        """, (box['id'],))
        packages = cursor.fetchall()

        for pkg in packages:
            print(f"    {pkg['sku']} {pkg['name'][:25]:<25} {pkg['weight_lbs']:>6.2f} lb")

        total_boxes += 1
        total_packages += box['package_count']
        total_weight += box['total_weight']

    print(f"\n{'=' * 60}")
    print(f"TOTALS: {total_boxes} boxes, {total_packages} packages, {total_weight:.2f} lb")

    conn.close()


def orders_report():
    """Generate pending orders report."""
    orders = get_pending_orders()

    print(f"\n{'=' * 60}")
    print("PENDING ORDERS REPORT")
    print(f"{'=' * 60}\n")

    for order in orders:
        boxes = get_boxes_for_order(order.id)
        total_weight = sum(b.total_weight for b in boxes)

        print(f"\nOrder: {order.customer_name}")
        print(f"  Date: {order.order_date}")
        print(f"  Status: {order.status.upper()}")
        print(f"  Boxes: {len(boxes)}")
        print(f"  Total Weight: {total_weight:.2f} lb")

        for box in boxes:
            verified = "OK" if box.verified else "--"
            print(f"    {box.box_number}  {box.package_count} pkgs  {box.total_weight:.2f} lb  [{verified}]")

    if not orders:
        print("No pending orders")


def main():
    parser = argparse.ArgumentParser(description='Export Pomponio reports')
    parser.add_argument('report', choices=['daily', 'inventory', 'orders'],
                        help='Report type to generate')
    parser.add_argument('date', nargs='?', help='Date for daily report (YYYY-MM-DD)')
    args = parser.parse_args()

    init_database()

    if args.report == 'daily':
        report_date = None
        if args.date:
            try:
                report_date = datetime.strptime(args.date, "%Y-%m-%d").date()
            except ValueError:
                print(f"Invalid date format: {args.date}. Use YYYY-MM-DD")
                sys.exit(1)
        daily_report(report_date)
    elif args.report == 'inventory':
        inventory_report()
    elif args.report == 'orders':
        orders_report()


if __name__ == '__main__':
    main()
