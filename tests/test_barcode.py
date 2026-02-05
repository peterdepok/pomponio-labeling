"""Tests for barcode generation and validation."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.barcode import (
    calculate_upc_check_digit,
    generate_package_barcode,
    parse_package_barcode,
    validate_package_barcode,
    generate_box_qr_data,
    parse_box_qr_data,
    validate_box_qr
)


class TestUPCCheckDigit(unittest.TestCase):
    """Test UPC check digit calculation."""

    def test_check_digit_zeros(self):
        """Test check digit for all zeros."""
        self.assertEqual(calculate_upc_check_digit("00000000000"), 0)

    def test_check_digit_example(self):
        """Test check digit for known example."""
        # UPC-A for "00123" SKU, weight 2.45 (245 units)
        # 0 00123 00245 -> need check digit
        result = calculate_upc_check_digit("00012300245")
        # Verify it's a valid single digit
        self.assertIn(result, range(10))

    def test_check_digit_another_example(self):
        """Test another check digit calculation."""
        result = calculate_upc_check_digit("01234567890")
        self.assertIn(result, range(10))


class TestPackageBarcode(unittest.TestCase):
    """Test package barcode generation and parsing."""

    def test_generate_basic(self):
        """Test basic barcode generation."""
        barcode = generate_package_barcode("00123", 2.45)
        self.assertEqual(len(barcode), 12)
        self.assertTrue(barcode.startswith("0"))
        self.assertTrue(barcode.isdigit())

    def test_generate_sku_padding(self):
        """Test that SKU is padded to 5 digits."""
        barcode = generate_package_barcode("1", 1.00)
        # SKU should be 00001
        self.assertEqual(barcode[1:6], "00001")

    def test_generate_weight_encoding(self):
        """Test weight encoding."""
        barcode = generate_package_barcode("00001", 2.45)
        # Weight 2.45 * 100 = 245 -> 00245
        self.assertEqual(barcode[6:11], "00245")

    def test_generate_large_weight(self):
        """Test large weight encoding."""
        barcode = generate_package_barcode("00001", 99.99)
        # Weight 99.99 * 100 = 9999 -> 09999
        self.assertEqual(barcode[6:11], "09999")

    def test_generate_weight_rounding(self):
        """Test weight rounding."""
        barcode = generate_package_barcode("00001", 2.456)
        # Should round to 2.46 -> 246 -> 00246
        self.assertEqual(barcode[6:11], "00246")

    def test_parse_valid_barcode(self):
        """Test parsing a valid barcode."""
        barcode = generate_package_barcode("00123", 2.45)
        parsed = parse_package_barcode(barcode)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.sku, "00123")
        self.assertEqual(parsed.weight_lbs, 2.45)
        self.assertEqual(parsed.raw, barcode)

    def test_parse_invalid_length(self):
        """Test parsing barcode with wrong length."""
        result = parse_package_barcode("123456")
        self.assertIsNone(result)

    def test_parse_invalid_prefix(self):
        """Test parsing barcode with wrong prefix."""
        result = parse_package_barcode("100000000000")
        self.assertIsNone(result)

    def test_parse_invalid_check_digit(self):
        """Test parsing barcode with wrong check digit."""
        barcode = generate_package_barcode("00123", 2.45)
        # Corrupt the check digit
        bad_check = str((int(barcode[-1]) + 1) % 10)
        bad_barcode = barcode[:-1] + bad_check
        result = parse_package_barcode(bad_barcode)
        self.assertIsNone(result)

    def test_validate_correct(self):
        """Test validation with correct values."""
        barcode = generate_package_barcode("00123", 2.45)
        valid, msg = validate_package_barcode(barcode, "00123", 2.45)
        self.assertTrue(valid)
        self.assertEqual(msg, "")

    def test_validate_sku_mismatch(self):
        """Test validation with SKU mismatch."""
        barcode = generate_package_barcode("00123", 2.45)
        valid, msg = validate_package_barcode(barcode, "00999", 2.45)
        self.assertFalse(valid)
        self.assertIn("SKU", msg)

    def test_validate_weight_mismatch(self):
        """Test validation with weight mismatch."""
        barcode = generate_package_barcode("00123", 2.45)
        valid, msg = validate_package_barcode(barcode, "00123", 5.00)
        self.assertFalse(valid)
        self.assertIn("Weight", msg)

    def test_roundtrip(self):
        """Test generate and parse roundtrip."""
        test_cases = [
            ("00001", 0.01),
            ("00123", 2.45),
            ("99999", 99.99),
            ("12345", 50.00),
        ]
        for sku, weight in test_cases:
            with self.subTest(sku=sku, weight=weight):
                barcode = generate_package_barcode(sku, weight)
                parsed = parse_package_barcode(barcode)
                self.assertIsNotNone(parsed)
                self.assertEqual(parsed.sku, sku.zfill(5))
                self.assertEqual(parsed.weight_lbs, weight)


class TestBoxQRCode(unittest.TestCase):
    """Test box QR code generation and parsing."""

    def test_generate_qr_data(self):
        """Test QR data generation."""
        qr = generate_box_qr_data(
            "20260204-001",
            10.65,
            [("00123", 2.45), ("00124", 8.20)]
        )
        self.assertIn("BOX|20260204-001|10.65", qr)
        self.assertIn("00123|2.45", qr)
        self.assertIn("00124|8.20", qr)

    def test_parse_qr_data(self):
        """Test QR data parsing."""
        qr = "BOX|20260204-001|10.65\n00123|2.45\n00124|8.20"
        parsed = parse_box_qr_data(qr)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.box_number, "20260204-001")
        self.assertEqual(parsed.total_weight, 10.65)
        self.assertEqual(len(parsed.items), 2)
        self.assertEqual(parsed.items[0], ("00123", 2.45))
        self.assertEqual(parsed.items[1], ("00124", 8.20))

    def test_parse_invalid_header(self):
        """Test parsing invalid QR header."""
        result = parse_box_qr_data("INVALID|DATA")
        self.assertIsNone(result)

    def test_validate_qr_correct(self):
        """Test QR validation with correct data."""
        qr = generate_box_qr_data(
            "20260204-001",
            10.65,
            [("00123", 2.45), ("00124", 8.20)]
        )
        valid, msg = validate_box_qr(qr, "20260204-001")
        self.assertTrue(valid)

    def test_validate_qr_box_mismatch(self):
        """Test QR validation with box number mismatch."""
        qr = generate_box_qr_data(
            "20260204-001",
            10.65,
            [("00123", 2.45), ("00124", 8.20)]
        )
        valid, msg = validate_box_qr(qr, "20260204-999")
        self.assertFalse(valid)
        self.assertIn("mismatch", msg.lower())

    def test_roundtrip(self):
        """Test generate and parse roundtrip."""
        items = [("00123", 2.45), ("00124", 8.20), ("00125", 5.00)]
        total = sum(w for _, w in items)

        qr = generate_box_qr_data("20260204-001", total, items)
        parsed = parse_box_qr_data(qr)

        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.box_number, "20260204-001")
        self.assertAlmostEqual(parsed.total_weight, total, places=2)
        self.assertEqual(len(parsed.items), len(items))


if __name__ == '__main__':
    unittest.main()
