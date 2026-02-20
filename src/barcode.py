"""EAN-13 barcode generation for Pomponio Ranch weight-embedded labels.

Barcode format (13 digits):
    [0][SKU padded to 6][weight*100 padded to 5][EAN-13 check digit]

Position 1:     Always 0 (system prefix)
Positions 2-7:  SKU zero-padded to 6 digits
Positions 8-12: Weight in hundredths of a pound (1.49 lb = 00149)
Position 13:    EAN-13 check digit (auto-calculated)

Matches the processor's barcode system. Each sales channel (Shopify retail,
wholesale, distributor) applies its own per-pound rate against the
weight encoded in the barcode.

Box labels use the same format with aggregate weight. The piece count
is displayed in the printed label text but not encoded in the barcode.
"""

import logging

logger = logging.getLogger(__name__)


class BarcodeError(Exception):
    """Raised when barcode generation fails due to invalid input."""


def validate_sku(sku: str) -> str:
    """Validate and normalize a SKU string to 5 digits.

    Args:
        sku: SKU code. Must be numeric and at most 5 digits.

    Returns:
        Zero-padded 5-digit SKU string.

    Raises:
        BarcodeError: If SKU is not valid.
    """
    if not sku.isdigit():
        raise BarcodeError(f"SKU must be numeric, got: '{sku}'")
    if len(sku) > 5:
        raise BarcodeError(f"SKU must be 5 digits or fewer, got: '{sku}'")
    return sku.zfill(5)


def encode_weight(weight_lb: float) -> str:
    """Encode a weight in pounds to a 5-digit hundredths string.

    Multiplies weight by 100, rounds to nearest integer, zero-pads to 5 digits.

    Args:
        weight_lb: Weight in pounds. Must be between 0.01 and 999.99 inclusive.

    Returns:
        Zero-padded 5-digit string (e.g., 1.52 -> "00152").

    Raises:
        BarcodeError: If weight is out of encodable range.
    """
    if weight_lb <= 0:
        raise BarcodeError(f"Weight must be positive, got: {weight_lb}")

    hundredths = round(weight_lb * 100)

    if hundredths < 1:
        raise BarcodeError(f"Weight too small to encode: {weight_lb} lb")
    if hundredths > 99999:
        raise BarcodeError(
            f"Weight exceeds maximum encodable value (999.99 lb): {weight_lb} lb"
        )

    return str(hundredths).zfill(5)


def calculate_ean13_check_digit(digits_12: str) -> int:
    """Calculate the EAN-13 check digit for a 12-digit data string.

    Algorithm: multiply each of the 12 digits by alternating weights 1,3,1,3...
    Sum the products. Check digit = (10 - (sum mod 10)) mod 10.

    Args:
        digits_12: Exactly 12 numeric digits.

    Returns:
        Single check digit (0-9).

    Raises:
        BarcodeError: If input is not exactly 12 digits.
    """
    if len(digits_12) != 12 or not digits_12.isdigit():
        raise BarcodeError(
            f"Check digit input must be exactly 12 digits, got: '{digits_12}'"
        )

    total = 0
    for i, ch in enumerate(digits_12):
        weight = 1 if i % 2 == 0 else 3
        total += int(ch) * weight

    return (10 - (total % 10)) % 10


def generate_barcode(sku: str, weight_lb: float) -> str:
    """Generate a 13-digit EAN-13 barcode for an individual package label.

    Format: 0 + SKU(6) + weight_encoded(5) + check_digit(1)

    Args:
        sku: Pomponio SKU code (numeric, up to 5 digits).
        weight_lb: Net weight in pounds.

    Returns:
        13-digit EAN-13 barcode string.

    Raises:
        BarcodeError: If SKU or weight is invalid.
    """
    sku_5 = validate_sku(sku)
    sku_6 = sku_5.zfill(6)
    weight_5 = encode_weight(weight_lb)
    data_12 = "0" + sku_6 + weight_5
    check = calculate_ean13_check_digit(data_12)
    barcode = data_12 + str(check)

    logger.debug(
        "Generated barcode: %s (SKU=%s, weight=%.2f lb)", barcode, sku, weight_lb
    )
    return barcode


def generate_box_barcode(sku: str, count: int, total_weight_lb: float) -> str:
    """Generate a 13-digit EAN-13 barcode for a box summary label.

    Same format as individual labels but with aggregate weight.
    The count parameter is accepted for API compatibility but is NOT
    encoded in the barcode (EAN-13 has no room for it). Count is
    displayed in the printed label text instead.

    Args:
        sku: Pomponio SKU code (numeric, up to 5 digits).
        count: Number of pieces in the box for this SKU (not encoded in barcode).
        total_weight_lb: Total weight in pounds for this SKU group.

    Returns:
        13-digit EAN-13 barcode string.

    Raises:
        BarcodeError: If any input is invalid.
    """
    sku_5 = validate_sku(sku)
    sku_6 = sku_5.zfill(6)
    weight_5 = encode_weight(total_weight_lb)
    data_12 = "0" + sku_6 + weight_5
    check = calculate_ean13_check_digit(data_12)
    barcode = data_12 + str(check)

    logger.debug(
        "Generated box barcode: %s (SKU=%s, count=%d, weight=%.2f lb)",
        barcode, sku, count, total_weight_lb,
    )
    return barcode


def parse_barcode(barcode: str) -> dict:
    """Parse a 13-digit EAN-13 barcode into its components.

    Args:
        barcode: 13-digit EAN-13 barcode string.

    Returns:
        Dict with keys: sku, weight_encoded, weight_lb, check_digit.

    Raises:
        BarcodeError: If barcode is not exactly 13 digits or check digit is invalid.
    """
    if len(barcode) != 13 or not barcode.isdigit():
        raise BarcodeError(f"Barcode must be exactly 13 digits, got: '{barcode}'")

    data_12 = barcode[:12]
    expected_check = calculate_ean13_check_digit(data_12)
    actual_check = int(barcode[12])

    if expected_check != actual_check:
        raise BarcodeError(
            f"Invalid check digit: expected {expected_check}, "
            f"got {actual_check} in barcode '{barcode}'"
        )

    weight_hundredths = int(barcode[7:12])
    weight_lb = weight_hundredths / 100.0

    return {
        "sku": barcode[1:7],
        "weight_encoded": barcode[7:12],
        "weight_lb": weight_lb,
        "check_digit": actual_check,
    }
