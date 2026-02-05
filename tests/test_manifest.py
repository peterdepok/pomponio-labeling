"""
Tests for manifest generation module.
"""

import unittest
import tempfile
from pathlib import Path
from datetime import datetime

from src.manifest import (
    ManifestConfig, OrderManifest, BoxContents,
    manifest_to_text, manifest_to_html, generate_zpl_manifest,
    load_manifest_config
)
from src.database import Package


class TestManifestConfig(unittest.TestCase):
    """Test manifest configuration."""

    def test_default_config(self):
        """Test default config values."""
        config = ManifestConfig()
        self.assertEqual(config.smtp_server, "smtp.gmail.com")
        self.assertEqual(config.smtp_port, 587)
        self.assertFalse(config.enabled)

    def test_load_config_missing_file(self):
        """Test loading config when file doesn't exist."""
        # Should return defaults without error
        config = load_manifest_config()
        self.assertIsInstance(config, ManifestConfig)


class TestBoxContents(unittest.TestCase):
    """Test BoxContents dataclass."""

    def test_create_box_contents(self):
        """Test creating box contents."""
        contents = BoxContents(
            box_number="20260204-001",
            box_id=1,
            total_weight=10.5,
            package_count=3,
            qr_data="BOX|20260204-001|10.50",
            packages=[],
            products_summary={"Ground Beef": {"count": 3, "weight": 10.5, "sku": "00123"}}
        )
        self.assertEqual(contents.box_number, "20260204-001")
        self.assertEqual(contents.package_count, 3)


class TestOrderManifest(unittest.TestCase):
    """Test OrderManifest dataclass."""

    def setUp(self):
        """Create test manifest."""
        self.manifest = OrderManifest(
            order_id=1,
            customer_name="Test Customer",
            order_date="2026-02-04",
            pickup_date="2026-02-05",
            box_count=2,
            total_packages=5,
            total_weight=25.75,
            boxes=[
                BoxContents(
                    box_number="20260204-001",
                    box_id=1,
                    total_weight=12.50,
                    package_count=2,
                    qr_data="BOX|20260204-001|12.50",
                    packages=[],
                    products_summary={
                        "Ground Beef 80/20": {"count": 1, "weight": 5.00, "sku": "00123"},
                        "Ribeye Steak": {"count": 1, "weight": 7.50, "sku": "00124"},
                    }
                ),
                BoxContents(
                    box_number="20260204-002",
                    box_id=2,
                    total_weight=13.25,
                    package_count=3,
                    qr_data="BOX|20260204-002|13.25",
                    packages=[],
                    products_summary={
                        "Brisket": {"count": 2, "weight": 10.00, "sku": "00125"},
                        "Chuck Roast": {"count": 1, "weight": 3.25, "sku": "00126"},
                    }
                ),
            ],
            generated_at=datetime.now()
        )

    def test_manifest_attributes(self):
        """Test manifest has correct attributes."""
        self.assertEqual(self.manifest.customer_name, "Test Customer")
        self.assertEqual(self.manifest.box_count, 2)
        self.assertEqual(self.manifest.total_packages, 5)
        self.assertEqual(self.manifest.total_weight, 25.75)


class TestManifestToText(unittest.TestCase):
    """Test text manifest generation."""

    def setUp(self):
        """Create test manifest."""
        self.manifest = OrderManifest(
            order_id=42,
            customer_name="Smith Family",
            order_date="2026-02-04",
            pickup_date=None,
            box_count=1,
            total_packages=2,
            total_weight=8.50,
            boxes=[
                BoxContents(
                    box_number="20260204-001",
                    box_id=1,
                    total_weight=8.50,
                    package_count=2,
                    qr_data="BOX|20260204-001|8.50",
                    packages=[],
                    products_summary={
                        "Ground Beef": {"count": 2, "weight": 8.50, "sku": "00123"},
                    }
                ),
            ],
            generated_at=datetime(2026, 2, 4, 10, 30)
        )

    def test_text_contains_header(self):
        """Test text manifest contains header."""
        text = manifest_to_text(self.manifest)
        self.assertIn("POMPONIO RANCH", text)
        self.assertIn("ORDER PICKUP MANIFEST", text)

    def test_text_contains_customer(self):
        """Test text manifest contains customer name."""
        text = manifest_to_text(self.manifest)
        self.assertIn("Smith Family", text)

    def test_text_contains_order_id(self):
        """Test text manifest contains order ID."""
        text = manifest_to_text(self.manifest)
        self.assertIn("42", text)

    def test_text_contains_totals(self):
        """Test text manifest contains totals."""
        text = manifest_to_text(self.manifest)
        self.assertIn("Total Boxes: 1", text)
        self.assertIn("Total Packages: 2", text)
        self.assertIn("8.50", text)

    def test_text_contains_box_number(self):
        """Test text manifest contains box number."""
        text = manifest_to_text(self.manifest)
        self.assertIn("20260204-001", text)

    def test_text_contains_products(self):
        """Test text manifest contains product info."""
        text = manifest_to_text(self.manifest)
        self.assertIn("Ground Beef", text)
        self.assertIn("00123", text)

    def test_text_contains_signature_section(self):
        """Test text manifest contains signature section."""
        text = manifest_to_text(self.manifest)
        self.assertIn("Customer Signature", text)
        self.assertIn("Verified By", text)


class TestManifestToHtml(unittest.TestCase):
    """Test HTML manifest generation."""

    def setUp(self):
        """Create test manifest."""
        self.manifest = OrderManifest(
            order_id=99,
            customer_name="Johnson Ranch",
            order_date="2026-02-04",
            pickup_date="2026-02-06",
            box_count=2,
            total_packages=5,
            total_weight=32.00,
            boxes=[
                BoxContents(
                    box_number="20260204-001",
                    box_id=1,
                    total_weight=16.00,
                    package_count=2,
                    qr_data="BOX|20260204-001|16.00",
                    packages=[],
                    products_summary={
                        "Ribeye": {"count": 2, "weight": 16.00, "sku": "00200"},
                    }
                ),
                BoxContents(
                    box_number="20260204-002",
                    box_id=2,
                    total_weight=16.00,
                    package_count=3,
                    qr_data="BOX|20260204-002|16.00",
                    packages=[],
                    products_summary={
                        "Sirloin": {"count": 3, "weight": 16.00, "sku": "00201"},
                    }
                ),
            ],
            generated_at=datetime(2026, 2, 4, 14, 0)
        )

    def test_html_is_valid_document(self):
        """Test HTML manifest is a valid document."""
        html = manifest_to_html(self.manifest)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html>", html)
        self.assertIn("</html>", html)

    def test_html_contains_title(self):
        """Test HTML contains title with customer name."""
        html = manifest_to_html(self.manifest)
        self.assertIn("Johnson Ranch", html)

    def test_html_contains_summary(self):
        """Test HTML contains summary section."""
        html = manifest_to_html(self.manifest)
        self.assertIn("BOXES", html)
        self.assertIn("PACKAGES", html)
        self.assertIn("TOTAL LBS", html)

    def test_html_contains_box_details(self):
        """Test HTML contains box details."""
        html = manifest_to_html(self.manifest)
        self.assertIn("20260204-001", html)
        self.assertIn("20260204-002", html)

    def test_html_contains_product_table(self):
        """Test HTML contains product table."""
        html = manifest_to_html(self.manifest)
        self.assertIn("Ribeye", html)
        self.assertIn("Sirloin", html)

    def test_html_has_checkbox_styles(self):
        """Test HTML has checkbox styles for verification."""
        html = manifest_to_html(self.manifest)
        self.assertIn("checkbox", html)

    def test_html_has_print_styles(self):
        """Test HTML has print media query."""
        html = manifest_to_html(self.manifest)
        self.assertIn("@media print", html)


class TestGenerateZplManifest(unittest.TestCase):
    """Test ZPL manifest label generation."""

    def setUp(self):
        """Create test manifest."""
        self.manifest = OrderManifest(
            order_id=1,
            customer_name="Test",
            order_date="2026-02-04",
            pickup_date=None,
            box_count=3,
            total_packages=10,
            total_weight=50.00,
            boxes=[
                BoxContents(
                    box_number=f"20260204-00{i}",
                    box_id=i,
                    total_weight=16.67,
                    package_count=3,
                    qr_data=f"BOX|20260204-00{i}|16.67",
                    packages=[],
                    products_summary={}
                ) for i in range(1, 4)
            ],
            generated_at=datetime.now()
        )

    def test_zpl_has_start_end(self):
        """Test ZPL has proper start and end commands."""
        zpl = generate_zpl_manifest(self.manifest)
        self.assertIn("^XA", zpl)
        self.assertIn("^XZ", zpl)

    def test_zpl_contains_customer(self):
        """Test ZPL contains customer name."""
        zpl = generate_zpl_manifest(self.manifest)
        self.assertIn("Test", zpl)

    def test_zpl_contains_order_id(self):
        """Test ZPL contains order ID."""
        zpl = generate_zpl_manifest(self.manifest)
        self.assertIn("Order: 1", zpl)

    def test_zpl_contains_counts(self):
        """Test ZPL contains box and package counts."""
        zpl = generate_zpl_manifest(self.manifest)
        self.assertIn("Boxes: 3", zpl)
        self.assertIn("Pkgs: 10", zpl)

    def test_zpl_contains_qr_code(self):
        """Test ZPL contains QR code command."""
        zpl = generate_zpl_manifest(self.manifest)
        self.assertIn("^BQ", zpl)


class TestManifestTruncation(unittest.TestCase):
    """Test manifest handles large data appropriately."""

    def test_zpl_truncates_many_boxes(self):
        """Test ZPL truncates when many boxes."""
        manifest = OrderManifest(
            order_id=1,
            customer_name="Test",
            order_date="2026-02-04",
            pickup_date=None,
            box_count=10,
            total_packages=30,
            total_weight=100.00,
            boxes=[
                BoxContents(
                    box_number=f"20260204-{i:03d}",
                    box_id=i,
                    total_weight=10.00,
                    package_count=3,
                    qr_data=f"BOX|20260204-{i:03d}|10.00",
                    packages=[],
                    products_summary={}
                ) for i in range(1, 11)
            ],
            generated_at=datetime.now()
        )
        zpl = generate_zpl_manifest(manifest)
        # Should mention "more boxes"
        self.assertIn("more boxes", zpl)

    def test_text_handles_long_customer_name(self):
        """Test text manifest handles long customer name."""
        manifest = OrderManifest(
            order_id=1,
            customer_name="A" * 100,
            order_date="2026-02-04",
            pickup_date=None,
            box_count=1,
            total_packages=1,
            total_weight=5.00,
            boxes=[],
            generated_at=datetime.now()
        )
        text = manifest_to_text(manifest)
        # Should not raise, just include the name
        self.assertIn("A" * 50, text)


if __name__ == '__main__':
    unittest.main()
