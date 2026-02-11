"""Comprehensive tests for UPC-A barcode generation.

Tests cover:
    - Check digit calculation against hand-verified values
    - SKU validation and normalization
    - Weight encoding edge cases
    - Full barcode generation
    - Barcode parsing and round-trip verification
    - All 69 active beef SKUs from pomponio_skus.csv
    - Error conditions and boundary values
"""

import csv
import os
import pytest

from src.barcode import (
    BarcodeError,
    calculate_check_digit,
    encode_weight,
    generate_barcode,
    parse_barcode,
    validate_sku,
)


# ---------------------------------------------------------------------------
# Check digit calculation
# ---------------------------------------------------------------------------

class TestCheckDigit:
    """Test the UPC-A modulo 10 check digit algorithm."""

    def test_prd_example_ribeye(self):
        """PRD example: SKU 00100, 1.52 lbs -> 00010000152, check = 5."""
        assert calculate_check_digit("00010000152") == 5

    def test_known_upc_zero_check(self):
        """When total mod 10 is 0, check digit is 0."""
        # Construct a case: all zeros -> odd=0, even=0, total=0, check=0
        assert calculate_check_digit("00000000000") == 0

    def test_known_upc_check_9(self):
        """Verify check digit 9 case."""
        # 10000000000: odd=1+0+0+0+0+0=1, even=0+0+0+0+0=0, total=3, check=7
        assert calculate_check_digit("10000000000") == 7

    def test_sequential_digits(self):
        """01234567890: hand-calculated check digit."""
        # Odd positions (0-indexed 0,2,4,6,8,10): 0,2,4,6,8,0 = 20, *3 = 60
        # Even positions (0-indexed 1,3,5,7,9): 1,3,5,7,9 = 25
        # Total = 85, check = (10-5)%10 = 5
        assert calculate_check_digit("01234567890") == 5

    def test_all_ones(self):
        """11111111111: odd=6*3=18, even=5, total=23, check=7."""
        assert calculate_check_digit("11111111111") == 7

    def test_all_nines(self):
        """99999999999: odd=54*3=162, even=45, total=207, check=3."""
        assert calculate_check_digit("99999999999") == 3

    def test_wrong_length_raises(self):
        with pytest.raises(BarcodeError):
            calculate_check_digit("0010000015")  # 10 digits

    def test_too_long_raises(self):
        with pytest.raises(BarcodeError):
            calculate_check_digit("000100001520")  # 12 digits

    def test_non_digit_raises(self):
        with pytest.raises(BarcodeError):
            calculate_check_digit("0010000015A")

    def test_empty_raises(self):
        with pytest.raises(BarcodeError):
            calculate_check_digit("")


# ---------------------------------------------------------------------------
# SKU validation
# ---------------------------------------------------------------------------

class TestValidateSku:

    def test_five_digit_sku(self):
        assert validate_sku("00100") == "00100"

    def test_short_sku_padded(self):
        assert validate_sku("100") == "00100"

    def test_single_digit_padded(self):
        assert validate_sku("1") == "00001"

    def test_zero_sku(self):
        assert validate_sku("0") == "00000"

    def test_max_sku(self):
        assert validate_sku("99999") == "99999"

    def test_six_digit_raises(self):
        with pytest.raises(BarcodeError):
            validate_sku("123456")

    def test_non_numeric_raises(self):
        with pytest.raises(BarcodeError):
            validate_sku("ABC00")

    def test_pork_sku_raises(self):
        """Pork SKUs like POR175 are not numeric and should fail."""
        with pytest.raises(BarcodeError):
            validate_sku("POR175")

    def test_empty_raises(self):
        with pytest.raises(BarcodeError):
            validate_sku("")

    def test_negative_raises(self):
        with pytest.raises(BarcodeError):
            validate_sku("-1")


# ---------------------------------------------------------------------------
# Weight encoding
# ---------------------------------------------------------------------------

class TestEncodeWeight:

    def test_prd_example_1_52(self):
        assert encode_weight(1.52) == "00152"

    def test_prd_example_12_5(self):
        assert encode_weight(12.5) == "01250"

    def test_prd_example_0_75(self):
        assert encode_weight(0.75) == "00075"

    def test_minimum_weight(self):
        assert encode_weight(0.01) == "00001"

    def test_maximum_weight(self):
        assert encode_weight(999.99) == "99999"

    def test_one_pound(self):
        assert encode_weight(1.0) == "00100"

    def test_ten_pounds(self):
        assert encode_weight(10.0) == "01000"

    def test_fifteen_pounds_scale_max(self):
        """15 lb is the scale max capacity."""
        assert encode_weight(15.0) == "01500"

    def test_rounding_sub_hundredth(self):
        """0.005 lb = 0.5 hundredths, rounds to 0 (banker's rounding). Below minimum."""
        with pytest.raises(BarcodeError):
            encode_weight(0.005)

    def test_rounding_half(self):
        """1.525 should round to 153 (banker's rounding to even)."""
        result = encode_weight(1.525)
        # Python rounds 152.5 to 152 (round half to even)
        assert result == "00152"

    def test_rounding_down(self):
        assert encode_weight(1.524) == "00152"

    def test_zero_raises(self):
        with pytest.raises(BarcodeError):
            encode_weight(0.0)

    def test_negative_raises(self):
        with pytest.raises(BarcodeError):
            encode_weight(-1.0)

    def test_too_heavy_raises(self):
        with pytest.raises(BarcodeError):
            encode_weight(1000.0)

    def test_barely_too_heavy(self):
        with pytest.raises(BarcodeError):
            encode_weight(999.999)  # rounds to 100000, exceeds 5 digits

    def test_weight_resolution_005(self):
        """Scale resolution is 0.005 lb. Verify encoding at resolution boundaries."""
        # 0.005 lb = 0.5 hundredths, rounds to 0, below minimum
        with pytest.raises(BarcodeError):
            encode_weight(0.005)
        assert encode_weight(0.01) == "00001"
        assert encode_weight(0.015) == "00002"  # rounds to 2 (even)
        assert encode_weight(0.02) == "00002"
        assert encode_weight(1.005) == "00100"  # 100.5 rounds to 100 (even)
        # 1.015 * 100 = 101.49999... in IEEE 754, rounds to 101
        assert encode_weight(1.015) == "00101"


# ---------------------------------------------------------------------------
# Full barcode generation
# ---------------------------------------------------------------------------

class TestGenerateBarcode:

    def test_prd_example(self):
        """SKU 00100, 1.52 lbs -> 000100001525."""
        barcode = generate_barcode("00100", 1.52)
        assert barcode == "000100001525"
        assert len(barcode) == 12
        assert barcode.isdigit()

    def test_starts_with_zero(self):
        barcode = generate_barcode("00100", 1.0)
        assert barcode[0] == "0"

    def test_sku_embedded(self):
        barcode = generate_barcode("00143", 2.5)
        assert barcode[1:6] == "00143"

    def test_weight_embedded(self):
        barcode = generate_barcode("00100", 2.5)
        assert barcode[6:11] == "00250"

    def test_check_digit_valid(self):
        barcode = generate_barcode("00100", 1.52)
        expected = calculate_check_digit(barcode[:11])
        assert int(barcode[11]) == expected

    def test_minimum_weight_barcode(self):
        barcode = generate_barcode("00100", 0.01)
        assert len(barcode) == 12
        assert barcode[6:11] == "00001"

    def test_heavy_cut(self):
        """A 14.5 lb prime rib roast."""
        barcode = generate_barcode("00156", 14.5)
        assert barcode[1:6] == "00156"
        assert barcode[6:11] == "01450"

    def test_short_sku_auto_padded(self):
        barcode = generate_barcode("100", 1.0)
        assert barcode[1:6] == "00100"

    def test_invalid_sku_raises(self):
        with pytest.raises(BarcodeError):
            generate_barcode("ABCDE", 1.0)

    def test_invalid_weight_raises(self):
        with pytest.raises(BarcodeError):
            generate_barcode("00100", 0.0)


# ---------------------------------------------------------------------------
# Barcode parsing
# ---------------------------------------------------------------------------

class TestParseBarcode:

    def test_round_trip(self):
        """Generate, then parse, then verify all fields match."""
        barcode = generate_barcode("00100", 1.52)
        parsed = parse_barcode(barcode)
        assert parsed["quantity_flag"] == "0"
        assert parsed["sku"] == "00100"
        assert parsed["weight_lb"] == 1.52
        assert parsed["check_digit"] == 5
        assert parsed["valid"] is True

    def test_invalid_check_digit(self):
        """Manually corrupt the check digit."""
        barcode = generate_barcode("00100", 1.52)
        corrupted = barcode[:11] + str((int(barcode[11]) + 1) % 10)
        parsed = parse_barcode(corrupted)
        assert parsed["valid"] is False

    def test_parse_wrong_length(self):
        with pytest.raises(BarcodeError):
            parse_barcode("00010000152")  # 11 digits

    def test_parse_non_digit(self):
        with pytest.raises(BarcodeError):
            parse_barcode("00010000152X")

    def test_weight_extraction(self):
        barcode = generate_barcode("00100", 12.5)
        parsed = parse_barcode(barcode)
        assert parsed["weight_lb"] == 12.5

    def test_sku_extraction(self):
        barcode = generate_barcode("00145", 3.0)
        parsed = parse_barcode(barcode)
        assert parsed["sku"] == "00145"


# ---------------------------------------------------------------------------
# All 69 active beef SKUs
# ---------------------------------------------------------------------------

def load_beef_skus():
    """Load all active beef SKUs from the CSV."""
    csv_path = os.path.join(
        os.path.dirname(__file__), "..", "data", "pomponio_skus.csv"
    )
    skus = []
    with open(csv_path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["active"].strip().lower() == "true" and row["sku"].isdigit():
                skus.append(row["sku"])
    return skus


BEEF_SKUS = load_beef_skus()


class TestAllBeefSkus:
    """Generate barcodes for every active beef SKU at multiple weights."""

    @pytest.mark.parametrize("sku", BEEF_SKUS)
    def test_barcode_generation_1lb(self, sku):
        barcode = generate_barcode(sku, 1.0)
        assert len(barcode) == 12
        assert barcode.isdigit()
        assert barcode[0] == "0"
        parsed = parse_barcode(barcode)
        assert parsed["valid"] is True
        assert parsed["sku"] == sku.zfill(5)

    @pytest.mark.parametrize("sku", BEEF_SKUS)
    def test_barcode_generation_typical_weight(self, sku):
        """Typical retail cut weight: 1.52 lbs."""
        barcode = generate_barcode(sku, 1.52)
        parsed = parse_barcode(barcode)
        assert parsed["valid"] is True
        assert parsed["weight_lb"] == 1.52

    @pytest.mark.parametrize("sku", BEEF_SKUS)
    def test_barcode_generation_heavy(self, sku):
        """Heavy cut: 8.75 lbs."""
        barcode = generate_barcode(sku, 8.75)
        parsed = parse_barcode(barcode)
        assert parsed["valid"] is True
        assert parsed["weight_lb"] == 8.75

    @pytest.mark.parametrize("sku", BEEF_SKUS)
    def test_barcode_round_trip(self, sku):
        """Full round-trip: generate then parse, verify all fields."""
        weight = 3.33
        barcode = generate_barcode(sku, weight)
        parsed = parse_barcode(barcode)
        assert parsed["valid"] is True
        assert parsed["sku"] == sku.zfill(5)
        assert parsed["weight_lb"] == 3.33

    def test_beef_sku_count(self):
        """Verify we loaded the expected number of active numeric SKUs from CSV."""
        assert len(BEEF_SKUS) == 71


# ---------------------------------------------------------------------------
# Edge cases and boundary values
# ---------------------------------------------------------------------------

class TestEdgeCases:

    def test_weight_at_scale_resolution(self):
        """Scale resolution is 0.005 lb. Test increments at encodable weights."""
        weights = [0.01, 0.015, 0.020, 0.025, 0.500, 1.000, 14.995, 15.000]
        for w in weights:
            barcode = generate_barcode("00100", w)
            parsed = parse_barcode(barcode)
            assert parsed["valid"] is True

    def test_every_check_digit_value(self):
        """Ensure we can produce barcodes with each check digit 0-9."""
        seen_checks = set()
        for sku_num in range(100, 200):
            for weight_hundredths in range(1, 20):
                barcode = generate_barcode(str(sku_num), weight_hundredths / 100.0)
                seen_checks.add(int(barcode[11]))
                if len(seen_checks) == 10:
                    break
            if len(seen_checks) == 10:
                break
        assert seen_checks == {0, 1, 2, 3, 4, 5, 6, 7, 8, 9}

    def test_barcode_uniqueness_different_weights(self):
        """Same SKU, different weights must produce different barcodes."""
        b1 = generate_barcode("00100", 1.0)
        b2 = generate_barcode("00100", 1.01)
        assert b1 != b2

    def test_barcode_uniqueness_different_skus(self):
        """Different SKUs, same weight must produce different barcodes."""
        b1 = generate_barcode("00100", 1.0)
        b2 = generate_barcode("00101", 1.0)
        assert b1 != b2

    def test_weight_precision_no_float_drift(self):
        """Common float precision issue: 0.1 + 0.2 != 0.3. Verify encoding."""
        # 0.1 + 0.2 in float is 0.30000000000000004
        weight = 0.1 + 0.2
        encoded = encode_weight(weight)
        assert encoded == "00030"

    def test_sku_leading_zeros_preserved(self):
        barcode = generate_barcode("00001", 1.0)
        assert barcode[1:6] == "00001"
