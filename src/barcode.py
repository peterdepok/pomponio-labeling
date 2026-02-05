"""
Barcode generation and validation module.
Handles UPC-A style barcodes for packages and QR codes for boxes.
"""

from dataclasses import dataclass
from typing import Optional
import io

try:
    import qrcode
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False


@dataclass
class BarcodeData:
    """Parsed barcode data."""
    sku: str
    weight_lbs: float
    check_digit: int
    raw: str


@dataclass
class BoxQRData:
    """Parsed box QR data."""
    box_number: str
    total_weight: float
    items: list[tuple[str, float]]  # List of (sku, weight) tuples
    raw: str


def calculate_upc_check_digit(digits: str) -> int:
    """
    Calculate UPC-A check digit (modulo 10).

    Algorithm:
    1. Sum odd-position digits, multiply by 3
    2. Sum even-position digits
    3. Add the two sums
    4. Check digit = (10 - (sum mod 10)) mod 10
    """
    if len(digits) != 11:
        raise ValueError(f"Expected 11 digits, got {len(digits)}")

    odd_sum = sum(int(digits[i]) for i in range(0, 11, 2))
    even_sum = sum(int(digits[i]) for i in range(1, 11, 2))
    total = odd_sum * 3 + even_sum
    return (10 - (total % 10)) % 10


def generate_package_barcode(sku: str, weight_lbs: float) -> str:
    """
    Generate package barcode in format:
    [0][5-digit SKU][5-digit weight×100][check digit]

    Total: 12 digits (UPC-A compatible)

    Example: SKU 00123, weight 2.45 lbs
    - Leading 0: 0
    - SKU: 00123
    - Weight: 00245 (2.45 * 100)
    - Check digit: calculated
    - Result: 0001230024505 (with check digit 5)
    """
    sku_str = str(sku).zfill(5)
    if len(sku_str) > 5:
        raise ValueError(f"SKU too long: {sku}")

    weight_int = int(round(weight_lbs * 100))
    if weight_int > 99999:
        raise ValueError(f"Weight too large: {weight_lbs} lbs")
    weight_str = str(weight_int).zfill(5)

    partial = f"0{sku_str}{weight_str}"
    check_digit = calculate_upc_check_digit(partial)

    return f"{partial}{check_digit}"


def parse_package_barcode(barcode: str) -> Optional[BarcodeData]:
    """
    Parse package barcode and validate check digit.
    Returns BarcodeData or None if invalid.
    """
    if len(barcode) != 12:
        return None

    if not barcode.isdigit():
        return None

    if barcode[0] != '0':
        return None

    # Validate check digit
    expected_check = calculate_upc_check_digit(barcode[:11])
    actual_check = int(barcode[11])
    if expected_check != actual_check:
        return None

    sku = barcode[1:6]
    weight_int = int(barcode[6:11])
    weight_lbs = weight_int / 100.0

    return BarcodeData(
        sku=sku,
        weight_lbs=weight_lbs,
        check_digit=actual_check,
        raw=barcode
    )


def validate_package_barcode(barcode: str, expected_sku: str = None, expected_weight: float = None) -> tuple[bool, str]:
    """
    Validate barcode format and optionally check against expected values.
    Returns (valid, error_message).
    """
    parsed = parse_package_barcode(barcode)
    if parsed is None:
        return False, "Invalid barcode format or check digit"

    if expected_sku is not None:
        if parsed.sku != expected_sku.zfill(5):
            return False, f"SKU mismatch: expected {expected_sku}, got {parsed.sku}"

    if expected_weight is not None:
        # Allow small tolerance for floating point
        if abs(parsed.weight_lbs - expected_weight) > 0.01:
            return False, f"Weight mismatch: expected {expected_weight}, got {parsed.weight_lbs}"

    return True, ""


def generate_box_qr_data(box_number: str, total_weight: float, items: list[tuple[str, float]]) -> str:
    """
    Generate box QR code data string.

    Format:
    BOX|DATE-SEQ|TOTAL_WT
    SKU|WT
    SKU|WT
    ...
    """
    lines = [f"BOX|{box_number}|{total_weight:.2f}"]
    for sku, weight in items:
        lines.append(f"{sku}|{weight:.2f}")
    return "\n".join(lines)


def parse_box_qr_data(qr_data: str) -> Optional[BoxQRData]:
    """
    Parse box QR code data.
    Returns BoxQRData or None if invalid.
    """
    lines = qr_data.strip().split("\n")
    if not lines:
        return None

    header = lines[0].split("|")
    if len(header) != 3 or header[0] != "BOX":
        return None

    try:
        box_number = header[1]
        total_weight = float(header[2])
    except (IndexError, ValueError):
        return None

    items = []
    for line in lines[1:]:
        parts = line.split("|")
        if len(parts) == 2:
            try:
                items.append((parts[0], float(parts[1])))
            except ValueError:
                continue

    return BoxQRData(
        box_number=box_number,
        total_weight=total_weight,
        items=items,
        raw=qr_data
    )


def validate_box_qr(qr_data: str, expected_box_number: str = None) -> tuple[bool, str]:
    """
    Validate box QR data.
    Returns (valid, error_message).
    """
    parsed = parse_box_qr_data(qr_data)
    if parsed is None:
        return False, "Invalid QR data format"

    if expected_box_number is not None:
        if parsed.box_number != expected_box_number:
            return False, f"Box number mismatch: expected {expected_box_number}, got {parsed.box_number}"

    # Validate weight sum
    items_weight = sum(w for _, w in parsed.items)
    if abs(items_weight - parsed.total_weight) > 0.1:
        return False, f"Weight mismatch: items sum {items_weight:.2f}, header says {parsed.total_weight:.2f}"

    return True, ""


def generate_code128_barcode(data: str) -> str:
    """
    Generate Code 128 barcode representation for manifest printing.
    Returns a string representation suitable for ZPL or display.
    """
    return data  # For ZPL, we just pass the data; printer generates barcode


def generate_qr_image(data: str, box_size: int = 10, border: int = 2) -> bytes:
    """
    Generate QR code image as PNG bytes.
    Requires qrcode and Pillow libraries.
    """
    if not QR_AVAILABLE:
        raise ImportError("qrcode library not installed")

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return buffer.getvalue()


if __name__ == "__main__":
    # Test barcode generation
    bc = generate_package_barcode("00123", 2.45)
    print(f"Generated barcode: {bc}")

    parsed = parse_package_barcode(bc)
    print(f"Parsed: SKU={parsed.sku}, Weight={parsed.weight_lbs}, Check={parsed.check_digit}")

    valid, msg = validate_package_barcode(bc, "00123", 2.45)
    print(f"Valid: {valid}, Message: {msg}")

    # Test QR generation
    qr = generate_box_qr_data("20260204-001", 10.65, [("00123", 2.45), ("00124", 8.20)])
    print(f"\nQR Data:\n{qr}")

    parsed_qr = parse_box_qr_data(qr)
    print(f"\nParsed QR: box={parsed_qr.box_number}, weight={parsed_qr.total_weight}, items={len(parsed_qr.items)}")
