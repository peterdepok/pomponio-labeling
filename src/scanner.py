"""Barcode scanner input capture via USB HID keyboard wedge.

The Zebra DS2208 sends scanned barcode data as keyboard input followed by Enter.
This module captures rapid keystroke sequences and extracts 12-digit UPC-A barcodes.
"""

import logging
import threading
import time
from typing import Callable, Optional

logger = logging.getLogger(__name__)

SCAN_TIMEOUT = 0.3  # max seconds between first and last keystroke of a scan
UPC_A_LENGTH = 12


class ScannerError(Exception):
    """Raised on scanner input error."""


class ScanResult:
    """Result of a barcode scan."""

    def __init__(self, scanned: str, expected: Optional[str] = None):
        self.scanned = scanned
        self.expected = expected
        self.matched = expected is not None and scanned == expected

    def __repr__(self) -> str:
        status = "MATCH" if self.matched else "MISMATCH"
        return f"ScanResult({self.scanned}, {status})"


class Scanner:
    """Keyboard wedge barcode scanner interface.

    In the UI, this works by capturing keyboard events on a hidden entry widget.
    This module provides the logic for buffer management, timeout, and verification.
    """

    def __init__(self):
        self._buffer: list[str] = []
        self._buffer_start: Optional[float] = None
        self._expected_barcode: Optional[str] = None
        self._on_scan: Optional[Callable[[ScanResult], None]] = None
        self._lock = threading.Lock()

    def set_expected(self, barcode: str) -> None:
        """Set the expected barcode for verification."""
        self._expected_barcode = barcode
        logger.debug("Expected barcode set: %s", barcode)

    def clear_expected(self) -> None:
        """Clear the expected barcode."""
        self._expected_barcode = None

    def set_callback(self, callback: Callable[[ScanResult], None]) -> None:
        """Set callback for scan events."""
        self._on_scan = callback

    def on_keystroke(self, char: str) -> Optional[ScanResult]:
        """Process a single keystroke from the keyboard wedge.

        Called by the UI event handler for each key press.
        Accumulates digits and triggers scan processing on Enter.

        Args:
            char: Single character from keyboard event.

        Returns:
            ScanResult if a complete barcode was captured, None otherwise.
        """
        with self._lock:
            now = time.time()

            # Enter/Return triggers scan processing
            if char in ("\r", "\n"):
                return self._process_buffer()

            # Start new buffer or check timeout
            if self._buffer_start is None:
                self._buffer_start = now
            elif now - self._buffer_start > SCAN_TIMEOUT:
                # Timeout: clear old buffer, start fresh
                self._buffer.clear()
                self._buffer_start = now

            # Only accumulate digits (UPC-A is all numeric)
            if char.isdigit():
                self._buffer.append(char)

            return None

    def _process_buffer(self) -> Optional[ScanResult]:
        """Process accumulated keystrokes as a barcode."""
        barcode = "".join(self._buffer)
        self._buffer.clear()
        self._buffer_start = None

        if len(barcode) != UPC_A_LENGTH:
            logger.warning(
                "Scan rejected: expected %d digits, got %d (%s)",
                UPC_A_LENGTH, len(barcode), barcode,
            )
            return None

        if not barcode.isdigit():
            logger.warning("Scan rejected: non-numeric input: %s", barcode)
            return None

        result = ScanResult(barcode, self._expected_barcode)
        logger.info(
            "Scan captured: %s (expected: %s, matched: %s)",
            barcode, self._expected_barcode, result.matched,
        )

        if self._on_scan:
            self._on_scan(result)

        return result

    def process_raw_input(self, raw: str) -> Optional[ScanResult]:
        """Process a complete raw input string (e.g., from a hidden text field).

        This is an alternative to keystroke-by-keystroke processing.
        The scanner sends the barcode + Enter; the text field captures the digits.

        Args:
            raw: Complete string from text field (digits only, no Enter).

        Returns:
            ScanResult if valid barcode, None otherwise.
        """
        barcode = raw.strip()
        if len(barcode) != UPC_A_LENGTH or not barcode.isdigit():
            logger.warning("Raw scan rejected: %s", barcode)
            return None

        result = ScanResult(barcode, self._expected_barcode)
        logger.info("Raw scan: %s (matched: %s)", barcode, result.matched)

        if self._on_scan:
            self._on_scan(result)

        return result
