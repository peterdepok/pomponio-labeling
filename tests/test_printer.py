"""
Tests for printer and label generation module.
"""

import unittest
import tempfile
from pathlib import Path
from src.printer import LabelGenerator, MockPrinter, ZebraPrinter


class TestLabelGenerator(unittest.TestCase):
    """Test ZPL label generation."""

    def setUp(self):
        self.gen = LabelGenerator()

    def test_package_label_contains_product_name(self):
        """Test package label includes product name."""
        zpl = self.gen.package_label(
            product_name="Ground Beef 80/20",
            sku="00123",
            weight_lbs=2.45,
            price_per_lb=8.99,
            barcode="000123002455"
        )
        self.assertIn("Ground Beef 80/20", zpl)

    def test_package_label_contains_weight(self):
        """Test package label includes weight."""
        zpl = self.gen.package_label(
            product_name="Ribeye Steak",
            sku="00124",
            weight_lbs=1.25,
            price_per_lb=24.99,
            barcode="000124001255"
        )
        self.assertIn("1.25", zpl)

    def test_package_label_contains_barcode(self):
        """Test package label includes barcode."""
        zpl = self.gen.package_label(
            product_name="Brisket",
            sku="00125",
            weight_lbs=10.50,
            price_per_lb=12.99,
            barcode="000125010501"
        )
        self.assertIn("000125010501", zpl)

    def test_package_label_calculates_total_price(self):
        """Test package label calculates correct total price."""
        zpl = self.gen.package_label(
            product_name="Test",
            sku="00001",
            weight_lbs=2.00,
            price_per_lb=10.00,
            barcode="000010020002"
        )
        # 2.00 * 10.00 = 20.00
        self.assertIn("$20.00", zpl)

    def test_package_label_has_zpl_structure(self):
        """Test package label has valid ZPL structure."""
        zpl = self.gen.package_label(
            product_name="Test",
            sku="00001",
            weight_lbs=1.00,
            price_per_lb=5.00,
            barcode="000010010002"
        )
        self.assertTrue(zpl.strip().startswith("^XA"))
        self.assertTrue(zpl.strip().endswith("^XZ"))

    def test_package_label_truncates_long_name(self):
        """Test package label truncates long product names."""
        zpl = self.gen.package_label(
            product_name="A" * 50,
            sku="00001",
            weight_lbs=1.00,
            price_per_lb=5.00,
            barcode="000010010002"
        )
        # Name should be truncated to 25 chars
        self.assertNotIn("A" * 50, zpl)

    def test_box_label_contains_box_number(self):
        """Test box label includes box number."""
        zpl = self.gen.box_label(
            box_number="20260204-001",
            total_weight=24.50,
            package_count=8,
            qr_data="BOX|20260204-001|24.50"
        )
        self.assertIn("20260204-001", zpl)

    def test_box_label_contains_qr_code(self):
        """Test box label includes QR code command."""
        zpl = self.gen.box_label(
            box_number="20260204-001",
            total_weight=24.50,
            package_count=8,
            qr_data="BOX|20260204-001|24.50"
        )
        self.assertIn("^BQ", zpl)  # QR code command

    def test_box_label_contains_package_count(self):
        """Test box label includes package count."""
        zpl = self.gen.box_label(
            box_number="20260204-001",
            total_weight=24.50,
            package_count=12,
            qr_data="BOX|20260204-001|24.50"
        )
        self.assertIn("Packages: 12", zpl)

    def test_box_label_optional_customer(self):
        """Test box label with customer name."""
        zpl = self.gen.box_label(
            box_number="20260204-001",
            total_weight=24.50,
            package_count=8,
            qr_data="BOX|20260204-001|24.50",
            customer_name="Smith Family"
        )
        self.assertIn("Smith Family", zpl)

    def test_manifest_label_contains_customer(self):
        """Test manifest label includes customer name."""
        zpl = self.gen.manifest_label(
            order_id=1,
            customer_name="Johnson Ranch",
            box_count=3,
            total_weight=75.25,
            box_numbers=["20260204-001", "20260204-002", "20260204-003"]
        )
        self.assertIn("Johnson Ranch", zpl)

    def test_manifest_label_contains_box_list(self):
        """Test manifest label includes box numbers."""
        zpl = self.gen.manifest_label(
            order_id=1,
            customer_name="Test",
            box_count=2,
            total_weight=50.00,
            box_numbers=["20260204-001", "20260204-002"]
        )
        self.assertIn("20260204-001", zpl)
        self.assertIn("20260204-002", zpl)

    def test_manifest_label_truncates_many_boxes(self):
        """Test manifest label truncates long box list."""
        boxes = [f"20260204-{i:03d}" for i in range(10)]
        zpl = self.gen.manifest_label(
            order_id=1,
            customer_name="Test",
            box_count=10,
            total_weight=100.00,
            box_numbers=boxes
        )
        self.assertIn("+4 more", zpl)


class TestMockPrinter(unittest.TestCase):
    """Test mock printer for testing."""

    def setUp(self):
        self.printer = MockPrinter()

    def test_connect_always_succeeds(self):
        """Test mock printer connect always succeeds."""
        result = self.printer.connect()
        self.assertTrue(result)

    def test_is_connected_always_true(self):
        """Test mock printer is always connected."""
        self.assertTrue(self.printer.is_connected())

    def test_send_zpl_logs_data(self):
        """Test mock printer logs sent ZPL."""
        self.printer.send_zpl("^XA^FDTest^FS^XZ")
        self.assertEqual(len(self.printer.print_log), 1)

    def test_get_last_label(self):
        """Test retrieving last printed label."""
        self.printer.send_zpl("^XA^FDFirst^FS^XZ")
        self.printer.send_zpl("^XA^FDSecond^FS^XZ")
        self.assertIn("Second", self.printer.get_last_label())

    def test_get_last_label_empty(self):
        """Test get_last_label returns None when empty."""
        self.assertIsNone(self.printer.get_last_label())

    def test_clear_log(self):
        """Test clearing print log."""
        self.printer.send_zpl("^XA^FDTest^FS^XZ")
        self.printer.clear_log()
        self.assertEqual(len(self.printer.print_log), 0)


class TestZebraPrinter(unittest.TestCase):
    """Test Zebra printer class."""

    def test_output_file_mode(self):
        """Test printer writes to file when output_file set."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.zpl') as f:
            temp_path = f.name

        try:
            printer = ZebraPrinter(output_file=temp_path)
            self.assertTrue(printer.connect())
            printer.send_zpl("^XA^FDTest^FS^XZ")

            content = Path(temp_path).read_text()
            self.assertIn("^XA^FDTest^FS^XZ", content)
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_output_file_is_connected(self):
        """Test output file mode reports connected."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.zpl') as f:
            temp_path = f.name

        try:
            printer = ZebraPrinter(output_file=temp_path)
            self.assertTrue(printer.is_connected())
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_no_connection_method_raises(self):
        """Test printer raises when no connection method specified."""
        printer = ZebraPrinter()
        with self.assertRaises(Exception):
            printer.connect()


if __name__ == '__main__':
    unittest.main()
