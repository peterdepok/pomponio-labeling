"""Tests for database operations."""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))

# Override DB path for testing
import src.database as db


class TestDatabaseOperations(unittest.TestCase):
    """Test database CRUD operations."""

    @classmethod
    def setUpClass(cls):
        """Create temp database for tests."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.temp_db = Path(cls.temp_dir) / "test.db"
        db.DB_PATH = cls.temp_db
        db.init_database()

    @classmethod
    def tearDownClass(cls):
        """Clean up temp database."""
        import shutil
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    def setUp(self):
        """Clear data between tests."""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM scan_log")
        cursor.execute("DELETE FROM packages")
        cursor.execute("DELETE FROM boxes")
        cursor.execute("DELETE FROM orders")
        cursor.execute("DELETE FROM products")
        conn.commit()
        conn.close()


class TestProducts(TestDatabaseOperations):
    """Test product operations."""

    def test_get_active_products_empty(self):
        """Test getting products when none exist."""
        products = db.get_active_products()
        self.assertEqual(len(products), 0)

    def test_import_and_get_products(self):
        """Test importing products from CSV."""
        # Create temp CSV
        csv_content = "sku,name,category,price_per_lb\n00001,Test Beef,Beef,9.99\n00002,Test Pork,Pork,7.99"
        csv_path = Path(self.temp_dir) / "test_products.csv"
        with open(csv_path, 'w') as f:
            f.write(csv_content)

        db.import_products_from_csv(str(csv_path))
        products = db.get_active_products()

        self.assertEqual(len(products), 2)
        self.assertEqual(products[0].name, "Test Beef")

    def test_get_product_by_sku(self):
        """Test getting product by SKU."""
        # Add product directly
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (sku, name, category, price_per_lb) VALUES (?, ?, ?, ?)",
            ("00123", "Ground Beef", "Beef", 8.99)
        )
        conn.commit()
        conn.close()

        product = db.get_product_by_sku("00123")
        self.assertIsNotNone(product)
        self.assertEqual(product.name, "Ground Beef")
        self.assertEqual(product.price_per_lb, 8.99)

    def test_get_products_by_category(self):
        """Test grouping products by category."""
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO products (sku, name, category, price_per_lb) VALUES (?, ?, ?, ?)",
            [
                ("00001", "Beef 1", "Beef", 9.99),
                ("00002", "Beef 2", "Beef", 10.99),
                ("00003", "Pork 1", "Pork", 7.99),
            ]
        )
        conn.commit()
        conn.close()

        by_cat = db.get_products_by_category()
        self.assertEqual(len(by_cat["Beef"]), 2)
        self.assertEqual(len(by_cat["Pork"]), 1)


class TestPackages(TestDatabaseOperations):
    """Test package operations."""

    def setUp(self):
        super().setUp()
        # Add a product for package tests
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (sku, name, category, price_per_lb) VALUES (?, ?, ?, ?)",
            ("00123", "Test Product", "Test", 9.99)
        )
        conn.commit()
        conn.close()
        self.product = db.get_product_by_sku("00123")

    def test_create_package(self):
        """Test creating a package."""
        package_id = db.create_package(self.product.id, 2.45, "000123002455")
        self.assertIsNotNone(package_id)
        self.assertGreater(package_id, 0)

    def test_get_package_by_barcode(self):
        """Test retrieving package by barcode."""
        db.create_package(self.product.id, 2.45, "000123002455")

        package = db.get_package_by_barcode("000123002455")
        self.assertIsNotNone(package)
        self.assertEqual(package.weight_lbs, 2.45)
        self.assertEqual(package.product_name, "Test Product")

    def test_verify_package(self):
        """Test marking package as verified."""
        package_id = db.create_package(self.product.id, 2.45, "000123002455")

        package = db.get_package_by_barcode("000123002455")
        self.assertFalse(package.verified)

        db.verify_package(package_id)

        package = db.get_package_by_barcode("000123002455")
        self.assertTrue(package.verified)

    def test_get_unboxed_packages(self):
        """Test getting packages not assigned to box."""
        db.create_package(self.product.id, 2.45, "000123002451")
        db.create_package(self.product.id, 3.00, "000123003002")

        unboxed = db.get_unboxed_packages()
        self.assertEqual(len(unboxed), 2)


class TestBoxes(TestDatabaseOperations):
    """Test box operations."""

    def setUp(self):
        super().setUp()
        # Add a product and package
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (sku, name, category, price_per_lb) VALUES (?, ?, ?, ?)",
            ("00123", "Test Product", "Test", 9.99)
        )
        conn.commit()
        conn.close()
        self.product = db.get_product_by_sku("00123")

    def test_create_box(self):
        """Test creating a box."""
        box_id = db.create_box()
        self.assertIsNotNone(box_id)

        box = db.get_box_by_id(box_id)
        self.assertIsNotNone(box)
        self.assertTrue(box.box_number.startswith(date.today().strftime("%Y%m%d")))

    def test_box_numbering(self):
        """Test sequential box numbering."""
        box_id1 = db.create_box()
        box_id2 = db.create_box()

        box1 = db.get_box_by_id(box_id1)
        box2 = db.get_box_by_id(box_id2)

        # Second box should have incremented sequence
        self.assertNotEqual(box1.box_number, box2.box_number)
        self.assertTrue(box1.box_number.endswith("-001"))
        self.assertTrue(box2.box_number.endswith("-002"))

    def test_assign_package_to_box(self):
        """Test assigning package to box."""
        box_id = db.create_box()
        package_id = db.create_package(self.product.id, 2.45, "000123002455")

        db.assign_package_to_box(package_id, box_id)
        db.update_box_totals(box_id)

        packages = db.get_packages_in_box(box_id)
        self.assertEqual(len(packages), 1)

        box = db.get_box_by_id(box_id)
        self.assertEqual(box.package_count, 1)
        self.assertEqual(box.total_weight, 2.45)

    def test_close_box(self):
        """Test closing a box."""
        box_id = db.create_box()
        qr_data = "BOX|20260204-001|2.45\n00123|2.45"

        db.close_box(box_id, qr_data)

        box = db.get_box_by_id(box_id)
        self.assertIsNotNone(box.closed_at)
        self.assertEqual(box.qr_data, qr_data)

    def test_get_current_box(self):
        """Test getting current open box."""
        # No box initially
        self.assertIsNone(db.get_current_box())

        # Create and get
        db.create_box()
        current = db.get_current_box()
        self.assertIsNotNone(current)
        self.assertIsNone(current.closed_at)


class TestOrders(TestDatabaseOperations):
    """Test order operations."""

    def test_create_order(self):
        """Test creating an order."""
        order_id = db.create_order("Test Customer")
        self.assertIsNotNone(order_id)

        order = db.get_order_by_id(order_id)
        self.assertEqual(order.customer_name, "Test Customer")
        self.assertEqual(order.status, "pending")

    def test_get_pending_orders(self):
        """Test getting pending orders."""
        db.create_order("Customer 1")
        db.create_order("Customer 2")

        orders = db.get_pending_orders()
        self.assertEqual(len(orders), 2)

    def test_update_order_status(self):
        """Test updating order status."""
        order_id = db.create_order("Test Customer")

        db.update_order_status(order_id, "ready")
        order = db.get_order_by_id(order_id)
        self.assertEqual(order.status, "ready")

        db.update_order_status(order_id, "picked_up")
        order = db.get_order_by_id(order_id)
        self.assertEqual(order.status, "picked_up")
        self.assertIsNotNone(order.completed_at)

    def test_assign_box_to_order(self):
        """Test assigning box to order."""
        order_id = db.create_order("Test Customer")
        box_id = db.create_box()

        db.assign_box_to_order(box_id, order_id)

        boxes = db.get_boxes_for_order(order_id)
        self.assertEqual(len(boxes), 1)
        self.assertEqual(boxes[0].id, box_id)


class TestScanLog(TestDatabaseOperations):
    """Test scan logging."""

    def test_log_scan_success(self):
        """Test logging successful scan."""
        db.log_scan("package", 1, "000123002455", True)

        logs = db.get_scan_history()
        self.assertEqual(len(logs), 1)
        self.assertTrue(logs[0].success)

    def test_log_scan_failure(self):
        """Test logging failed scan."""
        db.log_scan("package", 1, "invalid", False)

        logs = db.get_scan_history()
        self.assertEqual(len(logs), 1)
        self.assertFalse(logs[0].success)

    def test_filter_by_type(self):
        """Test filtering scan history by type."""
        db.log_scan("package", 1, "000123002455", True)
        db.log_scan("box", 1, "BOX|data", True)
        db.log_scan("pickup", 1, "BOX|data", True)

        package_logs = db.get_scan_history("package")
        self.assertEqual(len(package_logs), 1)

        all_logs = db.get_scan_history()
        self.assertEqual(len(all_logs), 3)


if __name__ == '__main__':
    unittest.main()
