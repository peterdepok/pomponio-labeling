"""Comprehensive tests for EAN-13 barcode generation.

Tests cover:
    - EAN-13 check digit calculation against hand-verified values
    - SKU validation and normalization
    - Weight encoding edge cases
    - Full barcode generation (13-digit EAN-13)
    - Barcode parsing and round-trip verification
    - Verified processor barcodes (NY Strip 0000101000855, Flat Iron 0000125001494)
    - All active beef SKUs from pomponio_skus.csv
    - Error conditions and boundary values
"""

import csv
import os
import pytest

from src.barcode import (
    BarcodeError,
    calculate_ean13_check_digit,
    encode_weight,
    generate_barcode,
    generate_box_barcode,
    parse_barcode,
    validate_sku,
)


# ---------------------------------------------------------------------------
# EAN-13 check digit calculation
# ---------------------------------------------------------------------------

class TestCheckDigit:
    """Test the EAN-13 modulo 10 check digit algorithm."""

    def test_processor_ny_strip(self):
        """Verified processor barcode: SKU 101, 0.85 lb -> check digit 5."""
        assert calculate_ean13_check_digit("000010100085") == 5

    def test_processor_flat_iron(self):
        """Verified processor barcode: SKU 125, 1.49 lb -> check digit 4."""
        assert calculate_ean13_check_digit("000012500149") == 4

    def test_all_zeros(self):
        """All zeros -> sum=0, check=0."""
        assert calculate_ean13_check_digit("000000000000") == 0

    def test_known_check_1(self):
        """Hand-calculated: 100000000000.
        Weights: 1,3,1,3,1,3,1,3,1,3,1,3
        Products: 1,0,0,0,0,0,0,0,0,0,0,0 = 1
        check = (10 - 1) % 10 = 9
        """
        assert calculate_ean13_check_digit("100000000000") == 9

    def test_sequential_digits(self):
        """012345678901: hand-calculated.
        Positions: 0,1,2,3,4,5,6,7,8,9,0,1
        Weights:   1,3,1,3,1,3,1,3,1,3,1,3
        Products:  0,3,2,9,4,15,6,21,8,27,0,3 = 98
        check = (10 - 8) % 10 = 2
        """
        assert calculate_ean13_check_digit("012345678901") == 2

    def test_all_ones(self):
        """111111111111: sum = 6*1 + 6*3 = 6+18 = 24, check = 6."""
        assert calculate_ean13_check_digit("111111111111") == 6

    def test_all_nines(self):
        """999999999999: sum = 6*9 + 6*27 = 54+162 = 216, check = 4."""
        assert calculate_ean13_check_digit("999999999999") == 4

    def test_wrong_length_short_raises(self):
        with pytest.raises(BarcodeError):
            calculate_ean13_check_digit("00001010008")  # 11 digits

    def test_wrong_length_long_raises(self):
        with pytest.raises(BarcodeError):
            calculate_ean13_check_digit("0000101000850")  # 13 digits

    def test_non_digit_raises(self):
        with pytest.raises(BarcodeError):
            calculate_ean13_check_digit("00001010008A")

    def test_empty_raises(self):
        with pytest.raises(BarcodeError):
            calculate_ean13_check_digit("")


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

    def test_processor_ny_strip_0_85(self):
        assert encode_weight(0.85) == "00085"

    def test_processor_flat_iron_1_49(self):
        assert encode_weight(1.49) == "00149"

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

    def test_processor_ny_strip(self):
        """Verified processor barcode: SKU 00101, 0.85 lb -> 0000101000855."""
        barcode = generate_barcode("00101", 0.85)
        assert barcode == "0000101000855"
        assert len(barcode) == 13
        assert barcode.isdigit()

    def test_processor_flat_iron(self):
        """Verified processor barcode: SKU 00125, 1.49 lb -> 0000125001494."""
        barcode = generate_barcode("00125", 1.49)
        assert barcode == "0000125001494"
        assert len(barcode) == 13

    def test_starts_with_zero(self):
        barcode = generate_barcode("00100", 1.0)
        assert barcode[0] == "0"

    def test_sku_embedded(self):
        """SKU occupies positions 1-6 (zero-padded to 6 digits)."""
        barcode = generate_barcode("00143", 2.5)
        assert barcode[1:7] == "000143"

    def test_weight_embedded(self):
        """Weight occupies positions 7-11."""
        barcode = generate_barcode("00100", 2.5)
        assert barcode[7:12] == "00250"

    def test_check_digit_valid(self):
        barcode = generate_barcode("00100", 1.52)
        expected = calculate_ean13_check_digit(barcode[:12])
        assert int(barcode[12]) == expected

    def test_minimum_weight_barcode(self):
        barcode = generate_barcode("00100", 0.01)
        assert len(barcode) == 13
        assert barcode[7:12] == "00001"

    def test_heavy_cut(self):
        """A 14.5 lb prime rib roast."""
        barcode = generate_barcode("00156", 14.5)
        assert barcode[1:7] == "000156"
        assert barcode[7:12] == "01450"

    def test_short_sku_auto_padded(self):
        barcode = generate_barcode("100", 1.0)
        assert barcode[1:7] == "000100"

    def test_invalid_sku_raises(self):
        with pytest.raises(BarcodeError):
            generate_barcode("ABCDE", 1.0)

    def test_invalid_weight_raises(self):
        with pytest.raises(BarcodeError):
            generate_barcode("00100", 0.0)


# ---------------------------------------------------------------------------
# Box barcode generation
# ---------------------------------------------------------------------------

class TestGenerateBoxBarcode:

    def test_box_barcode_same_format(self):
        """Box barcode uses same EAN-13 format, count is not encoded."""
        barcode = generate_box_barcode("00101", 5, 4.25)
        assert len(barcode) == 13
        assert barcode[0] == "0"
        assert barcode[1:7] == "000101"
        assert barcode[7:12] == "00425"

    def test_box_barcode_count_not_in_barcode(self):
        """Different counts with same SKU and weight produce identical barcodes."""
        b1 = generate_box_barcode("00101", 3, 2.55)
        b2 = generate_box_barcode("00101", 7, 2.55)
        assert b1 == b2

    def test_box_barcode_check_digit(self):
        barcode = generate_box_barcode("00125", 4, 5.96)
        expected = calculate_ean13_check_digit(barcode[:12])
        assert int(barcode[12]) == expected


# ---------------------------------------------------------------------------
# Barcode parsing
# ---------------------------------------------------------------------------

class TestParseBarcode:

    def test_round_trip(self):
        """Generate, then parse, then verify all fields match."""
        barcode = generate_barcode("00101", 0.85)
        parsed = parse_barcode(barcode)
        assert parsed["sku"] == "000101"
        assert parsed["weight_lb"] == 0.85
        assert parsed["check_digit"] == 5

    def test_processor_ny_strip(self):
        """Parse the known processor barcode."""
        parsed = parse_barcode("0000101000855")
        assert parsed["sku"] == "000101"
        assert parsed["weight_lb"] == 0.85
        assert parsed["check_digit"] == 5

    def test_processor_flat_iron(self):
        """Parse the known processor barcode."""
        parsed = parse_barcode("0000125001494")
        assert parsed["sku"] == "000125"
        assert parsed["weight_lb"] == 1.49
        assert parsed["check_digit"] == 4

    def test_invalid_check_digit(self):
        """Manually corrupt the check digit."""
        barcode = generate_barcode("00100", 1.52)
        corrupted = barcode[:12] + str((int(barcode[12]) + 1) % 10)
        with pytest.raises(BarcodeError, match="Invalid check digit"):
            parse_barcode(corrupted)

    def test_parse_wrong_length_short(self):
        with pytest.raises(BarcodeError):
            parse_barcode("000010100085")  # 12 digits

    def test_parse_wrong_length_long(self):
        with pytest.raises(BarcodeError):
            parse_barcode("00001010008550")  # 14 digits

    def test_parse_non_digit(self):
        with pytest.raises(BarcodeError):
            parse_barcode("000010100085X")

    def test_weight_extraction(self):
        barcode = generate_barcode("00100", 12.5)
        parsed = parse_barcode(barcode)
        assert parsed["weight_lb"] == 12.5

    def test_sku_extraction(self):
        barcode = generate_barcode("00145", 3.0)
        parsed = parse_barcode(barcode)
        assert parsed["sku"] == "000145"


# ---------------------------------------------------------------------------
# All active beef SKUs
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
        assert len(barcode) == 13
        assert barcode.isdigit()
        assert barcode[0] == "0"
        parsed = parse_barcode(barcode)
        assert parsed["sku"] == sku.zfill(5).zfill(6)

    @pytest.mark.parametrize("sku", BEEF_SKUS)
    def test_barcode_generation_typical_weight(self, sku):
        """Typical retail cut weight: 1.52 lbs."""
        barcode = generate_barcode(sku, 1.52)
        parsed = parse_barcode(barcode)
        assert parsed["weight_lb"] == 1.52

    @pytest.mark.parametrize("sku", BEEF_SKUS)
    def test_barcode_generation_heavy(self, sku):
        """Heavy cut: 8.75 lbs."""
        barcode = generate_barcode(sku, 8.75)
        parsed = parse_barcode(barcode)
        assert parsed["weight_lb"] == 8.75

    @pytest.mark.parametrize("sku", BEEF_SKUS)
    def test_barcode_round_trip(self, sku):
        """Full round-trip: generate then parse, verify all fields."""
        weight = 3.33
        barcode = generate_barcode(sku, weight)
        parsed = parse_barcode(barcode)
        assert parsed["sku"] == sku.zfill(5).zfill(6)
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
            assert parsed["weight_lb"] == round(w * 100) / 100

    def test_every_check_digit_value(self):
        """Ensure we can produce barcodes with each check digit 0-9."""
        seen_checks = set()
        for sku_num in range(100, 200):
            for weight_hundredths in range(1, 50):
                barcode = generate_barcode(str(sku_num), weight_hundredths / 100.0)
                seen_checks.add(int(barcode[12]))
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
        weight = 0.1 + 0.2
        encoded = encode_weight(weight)
        assert encoded == "00030"

    def test_sku_leading_zeros_preserved(self):
        barcode = generate_barcode("00001", 1.0)
        assert barcode[1:7] == "000001"
