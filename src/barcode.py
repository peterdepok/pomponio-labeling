"""UPC-A barcode generation for Pomponio Ranch weight-embedded labels.

Barcode format (12 digits):
    [0][5-digit SKU][5-digit weight x 100][check digit]

Position 1:     Always 0 (Shopify reads as quantity 1)
Positions 2-6:  SKU from Pomponio price sheet (e.g., 00100)
Positions 7-11: Weight in hundredths of a pound (1.52 lbs = 00152)
Position 12:    Standard UPC-A modulo 10 check digit
"""

import logging

logger = logging.getLogger(__name__)


class BarcodeError(Exception):
    """Raised when barcode generation fails due to invalid input."""


def calculate_check_digit(digits_11: str) -> int:
    """Calculate UPC-A modulo 10 check digit from the first 11 digits.

    Algorithm:
        1. Sum digits in odd positions (1, 3, 5, 7, 9, 11), multiply by 3
        2. Sum digits in even positions (2, 4, 6, 8, 10)
        3. Add the two sums
        4. Check digit = (10 - (total mod 10)) mod 10

    Args:
        digits_11: String of exactly 11 digits.

    Returns:
        Check digit as integer 0-9.

    Raises:
        BarcodeError: If input is not exactly 11 digits.
    """
    if len(digits_11) != 11 or not digits_11.isdigit():
        raise BarcodeError(
            f"Check digit input must be exactly 11 digits, got: '{digits_11}'"
        )

    odd_sum = sum(int(digits_11[i]) for i in range(0, 11, 2))
    even_sum = sum(int(digits_11[i]) for i in range(1, 11, 2))
    total = odd_sum * 3 + even_sum
    return (10 - (total % 10)) % 10


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


def generate_barcode(sku: str, weight_lb: float) -> str:
    """Generate a 12-digit UPC-A barcode for a Pomponio label.

    Format: 0 + SKU(5) + weight_encoded(5) + check_digit(1)

    Args:
        sku: Pomponio SKU code (numeric, up to 5 digits).
        weight_lb: Net weight in pounds.

    Returns:
        12-digit UPC-A barcode string.

    Raises:
        BarcodeError: If SKU or weight is invalid.
    """
    sku_5 = validate_sku(sku)
    weight_5 = encode_weight(weight_lb)

    first_11 = "0" + sku_5 + weight_5
    check = calculate_check_digit(first_11)
    barcode = first_11 + str(check)

    logger.debug(
        "Generated barcode: %s (SKU=%s, weight=%.2f lb)", barcode, sku, weight_lb
    )
    return barcode


def parse_barcode(barcode: str) -> dict:
    """Parse a 12-digit UPC-A barcode into its components.

    Args:
        barcode: 12-digit UPC-A barcode string.

    Returns:
        Dict with keys: quantity_flag, sku, weight_encoded, weight_lb, check_digit, valid.

    Raises:
        BarcodeError: If barcode is not exactly 12 digits.
    """
    if len(barcode) != 12 or not barcode.isdigit():
        raise BarcodeError(f"Barcode must be exactly 12 digits, got: '{barcode}'")

    expected_check = calculate_check_digit(barcode[:11])
    actual_check = int(barcode[11])

    weight_hundredths = int(barcode[6:11])
    weight_lb = weight_hundredths / 100.0

    return {
        "quantity_flag": barcode[0],
        "sku": barcode[1:6],
        "weight_encoded": barcode[6:11],
        "weight_lb": weight_lb,
        "check_digit": actual_check,
        "valid": expected_check == actual_check,
    }
