"""Code 128 barcode generation for Pomponio Ranch weight-embedded labels.

Barcode format (14 digits):
    [4-digit count][5-digit SKU][5-digit weight x 100]

Positions 1-4:   Piece count (0001 for individual packages, actual count for boxes)
Positions 5-9:   SKU from Pomponio price sheet (e.g., 00100)
Positions 10-14: Weight in hundredths of a pound (1.52 lbs = 00152)

No application-level check digit; Code 128 symbology provides its own.
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


def encode_count(count: int) -> str:
    """Encode a piece count to a 4-digit string.

    Args:
        count: Number of pieces (1-9999).

    Returns:
        Zero-padded 4-digit string.

    Raises:
        BarcodeError: If count is out of range.
    """
    if count < 1 or count > 9999:
        raise BarcodeError(f"Count must be 1-9999, got: {count}")
    return str(count).zfill(4)


def generate_barcode(sku: str, weight_lb: float) -> str:
    """Generate a 14-digit barcode for an individual package label.

    Format: 0001 + SKU(5) + weight_encoded(5)

    Args:
        sku: Pomponio SKU code (numeric, up to 5 digits).
        weight_lb: Net weight in pounds.

    Returns:
        14-digit barcode string.

    Raises:
        BarcodeError: If SKU or weight is invalid.
    """
    sku_5 = validate_sku(sku)
    weight_5 = encode_weight(weight_lb)
    barcode = "0001" + sku_5 + weight_5

    logger.debug(
        "Generated barcode: %s (SKU=%s, weight=%.2f lb)", barcode, sku, weight_lb
    )
    return barcode


def generate_box_barcode(sku: str, count: int, total_weight_lb: float) -> str:
    """Generate a 14-digit barcode for a box summary label.

    Format: count(4) + SKU(5) + weight_encoded(5)

    Args:
        sku: Pomponio SKU code (numeric, up to 5 digits).
        count: Number of pieces in the box for this SKU (1-9999).
        total_weight_lb: Total weight in pounds for this SKU group.

    Returns:
        14-digit barcode string.

    Raises:
        BarcodeError: If any input is invalid.
    """
    count_4 = encode_count(count)
    sku_5 = validate_sku(sku)
    weight_5 = encode_weight(total_weight_lb)
    barcode = count_4 + sku_5 + weight_5

    logger.debug(
        "Generated box barcode: %s (SKU=%s, count=%d, weight=%.2f lb)",
        barcode, sku, count, total_weight_lb,
    )
    return barcode


def parse_barcode(barcode: str) -> dict:
    """Parse a 14-digit barcode into its components.

    Args:
        barcode: 14-digit barcode string.

    Returns:
        Dict with keys: count, sku, weight_encoded, weight_lb.

    Raises:
        BarcodeError: If barcode is not exactly 14 digits.
    """
    if len(barcode) != 14 or not barcode.isdigit():
        raise BarcodeError(f"Barcode must be exactly 14 digits, got: '{barcode}'")

    count = int(barcode[0:4])
    weight_hundredths = int(barcode[9:14])
    weight_lb = weight_hundredths / 100.0

    return {
        "count": count,
        "sku": barcode[4:9],
        "weight_encoded": barcode[9:14],
        "weight_lb": weight_lb,
    }
