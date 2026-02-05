"""
Barcode scanner input module.
Handles Bluetooth HID keyboard wedge scanners.

Scanner operates as keyboard input - scanned barcodes are typed as keystrokes.
This module captures that input and routes it to the appropriate handler.
"""

import threading
import time
from typing import Callable, Optional
from dataclasses import dataclass


@dataclass
class ScanEvent:
    """Barcode scan event."""
    barcode: str
    timestamp: float
    scan_time_ms: int  # Time to receive full barcode


class ScannerBuffer:
    """
    Buffer for keyboard wedge scanner input.

    Keyboard wedge scanners type characters rapidly with a terminator.
    This buffer collects characters and detects when a barcode is complete.

    Detection criteria:
    - Characters arrive rapidly (< 50ms between chars for scanner)
    - Terminated by Enter key or configurable suffix
    - Minimum length to avoid false positives
    """

    def __init__(
        self,
        on_scan: Optional[Callable[[ScanEvent], None]] = None,
        min_length: int = 8,
        max_gap_ms: int = 50,
        terminator: str = "\n"
    ):
        self.on_scan = on_scan
        self.min_length = min_length
        self.max_gap_ms = max_gap_ms
        self.terminator = terminator

        self._buffer = ""
        self._last_char_time = 0.0
        self._scan_start_time = 0.0
        self._lock = threading.Lock()

    def add_char(self, char: str):
        """
        Add character to buffer.
        Call this from keyboard event handler.
        """
        now = time.time()
        now_ms = int(now * 1000)

        with self._lock:
            # Check if this is start of new scan or continuation
            if self._buffer and (now - self._last_char_time) * 1000 > self.max_gap_ms:
                # Gap too long, reset buffer
                self._buffer = ""

            if not self._buffer:
                self._scan_start_time = now

            self._last_char_time = now

            # Check for terminator
            if char in self.terminator:
                if len(self._buffer) >= self.min_length:
                    barcode = self._buffer
                    scan_time = int((now - self._scan_start_time) * 1000)
                    self._buffer = ""

                    if self.on_scan:
                        event = ScanEvent(
                            barcode=barcode,
                            timestamp=now,
                            scan_time_ms=scan_time
                        )
                        self.on_scan(event)
                else:
                    # Too short, probably manual typing
                    self._buffer = ""
            else:
                self._buffer += char

    def clear(self):
        """Clear the buffer."""
        with self._lock:
            self._buffer = ""

    @property
    def current_buffer(self) -> str:
        """Get current buffer contents."""
        with self._lock:
            return self._buffer


class TkinterScannerHandler:
    """
    Scanner handler for Tkinter applications.

    Binds to root window keyboard events and routes
    scanner input to callback while allowing normal typing.
    """

    def __init__(
        self,
        root,
        on_scan: Callable[[ScanEvent], None],
        min_length: int = 8
    ):
        """
        Initialize scanner handler.

        Args:
            root: Tkinter root window
            on_scan: Callback for completed scans
            min_length: Minimum barcode length to recognize
        """
        self.root = root
        self.buffer = ScannerBuffer(
            on_scan=on_scan,
            min_length=min_length
        )
        self._enabled = True
        self._bound = False

    def bind(self):
        """Bind to keyboard events."""
        if not self._bound:
            self.root.bind('<Key>', self._on_key, add='+')
            self._bound = True

    def unbind(self):
        """Unbind from keyboard events."""
        if self._bound:
            self.root.unbind('<Key>')
            self._bound = False

    def enable(self):
        """Enable scanner input processing."""
        self._enabled = True

    def disable(self):
        """Disable scanner input processing."""
        self._enabled = False
        self.buffer.clear()

    def _on_key(self, event):
        """Handle keyboard event."""
        if not self._enabled:
            return

        # Get the character
        char = event.char
        if not char:
            # Special key (shift, ctrl, etc.)
            if event.keysym == 'Return':
                char = '\n'
            else:
                return

        self.buffer.add_char(char)


class MockScanner:
    """
    Mock scanner for testing without hardware.
    Simulates barcode scans programmatically.
    """

    def __init__(self, on_scan: Callable[[ScanEvent], None]):
        self.on_scan = on_scan

    def simulate_scan(self, barcode: str):
        """Simulate a barcode scan."""
        event = ScanEvent(
            barcode=barcode,
            timestamp=time.time(),
            scan_time_ms=50
        )
        if self.on_scan:
            self.on_scan(event)


# Audio feedback for scans (Windows-focused)
def play_success_beep():
    """Play success beep sound."""
    try:
        import winsound
        winsound.Beep(1000, 100)  # 1000 Hz, 100ms
    except ImportError:
        # Not on Windows or no audio
        print('\a')  # Terminal bell


def play_error_beep():
    """Play error beep sound."""
    try:
        import winsound
        winsound.Beep(400, 300)   # 400 Hz, 300ms
        winsound.Beep(300, 300)   # 300 Hz, 300ms
    except ImportError:
        print('\a\a')  # Double terminal bell


if __name__ == "__main__":
    def test_scan(event: ScanEvent):
        print(f"Scanned: {event.barcode} (took {event.scan_time_ms}ms)")

    buffer = ScannerBuffer(on_scan=test_scan)

    # Simulate fast input (scanner)
    test_barcode = "000123002455\n"
    for char in test_barcode:
        buffer.add_char(char)
        time.sleep(0.01)  # 10ms between chars (scanner speed)

    print()

    # Simulate slow input (human typing) - should not trigger
    buffer.clear()
    for char in "hello\n":
        buffer.add_char(char)
        time.sleep(0.2)  # 200ms between chars (human speed)

    print("Slow typing test complete - should not have triggered scan")
