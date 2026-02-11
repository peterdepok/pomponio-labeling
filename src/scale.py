"""Brecknell 6710U scale communication via USB virtual COM port.

Protocol:
    Send: W\\r (0x57 0x0D)
    Response: <LF>[8-char weight][unit]<CR><LF>[H status byte]<CR><ETX>

Connection: 9600 baud, 8N1, via pyserial.
Stability: 3 consecutive stable readings = locked weight.
"""

import logging
import re
import threading
import time
from typing import Callable, Optional

import serial

logger = logging.getLogger(__name__)

BAUD_RATE = 9600
BYTE_SIZE = serial.EIGHTBITS
PARITY = serial.PARITY_NONE
STOP_BITS = serial.STOPBITS_ONE
TIMEOUT = 1.0
POLL_INTERVAL = 0.2  # 200ms per PRD
STABILITY_COUNT = 3  # consecutive stable readings required


class ScaleError(Exception):
    """Raised on scale communication failure."""


class ScaleReading:
    """A single weight reading from the scale."""

    def __init__(self, weight_lb: float, stable: bool, unit: str = "lb", raw: str = ""):
        self.weight_lb = weight_lb
        self.stable = stable
        self.unit = unit
        self.raw = raw

    def __repr__(self) -> str:
        status = "stable" if self.stable else "motion"
        return f"ScaleReading({self.weight_lb:.3f} {self.unit}, {status})"


class Scale:
    """Interface to the Brecknell 6710U USB scale."""

    def __init__(self, port: str, baud_rate: int = BAUD_RATE):
        self.port = port
        self.baud_rate = baud_rate
        self._serial: Optional[serial.Serial] = None
        self._polling = False
        self._poll_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._stable_count = 0
        self._last_weight: Optional[float] = None
        self._locked_weight: Optional[float] = None
        self._on_weight: Optional[Callable[[ScaleReading], None]] = None
        self._on_lock: Optional[Callable[[float], None]] = None

    @property
    def connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    def connect(self) -> None:
        """Open serial connection to the scale."""
        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=BYTE_SIZE,
                parity=PARITY,
                stopbits=STOP_BITS,
                timeout=TIMEOUT,
            )
            logger.info("Scale connected on %s", self.port)
        except serial.SerialException as e:
            raise ScaleError(f"Failed to connect to scale on {self.port}: {e}") from e

    def disconnect(self) -> None:
        """Close serial connection."""
        self.stop_polling()
        if self._serial and self._serial.is_open:
            self._serial.close()
            logger.info("Scale disconnected")
        self._serial = None

    def request_weight(self) -> ScaleReading:
        """Send W\\r command and parse the response.

        Returns:
            ScaleReading with weight and stability status.

        Raises:
            ScaleError: If not connected or communication fails.
        """
        if not self.connected:
            raise ScaleError("Scale not connected")

        try:
            self._serial.reset_input_buffer()
            self._serial.write(b"W\r")
            response = self._serial.read(50)  # read up to 50 bytes
            if not response:
                raise ScaleError("No response from scale")
            return self._parse_response(response.decode("ascii", errors="replace"))
        except serial.SerialException as e:
            raise ScaleError(f"Scale communication error: {e}") from e

    def _parse_response(self, raw: str) -> ScaleReading:
        """Parse Brecknell 6710U response into a ScaleReading.

        Expected format: <LF>[8-char weight][unit]<CR><LF>[H byte]<CR><ETX>
        Over capacity: underscores with spaces
        Under capacity: dashes with spaces
        """
        # Check for over/under capacity
        if "_ _ _ _" in raw:
            raise ScaleError("Scale over capacity")
        if "- - - -" in raw:
            raise ScaleError("Scale under capacity")

        # Extract weight field: 8 characters, right-justified, space-padded
        # Look for a numeric pattern (possibly with decimal and leading spaces)
        weight_match = re.search(r"([\s\d.+-]{1,8})(lb|kg|oz)", raw, re.IGNORECASE)
        if not weight_match:
            raise ScaleError(f"Cannot parse weight from response: {raw!r}")

        weight_str = weight_match.group(1).strip()
        unit = weight_match.group(2).lower()

        try:
            weight = float(weight_str)
        except ValueError:
            raise ScaleError(f"Invalid weight value: {weight_str!r}")

        # Parse stability from H status byte
        # The H byte follows the weight line; bit 5 (0x20) indicates motion
        # Response has: <LF>weight_field<CR><LF>H<CR><ETX>
        # The H byte is a single byte after the second LF, before CR+ETX
        stable = True
        lines = raw.split("\n")
        for line in lines:
            # Strip CR, ETX, and whitespace to isolate the H byte
            cleaned = line.replace("\r", "").replace("\x03", "").strip()
            if len(cleaned) == 1 and not cleaned.isdigit() and not cleaned.isspace():
                h_byte = ord(cleaned)
                # Bit 5 (0x20) = motion detected when set
                stable = not bool(h_byte & 0x20)
                break

        return ScaleReading(weight_lb=weight, stable=stable, unit=unit, raw=raw)

    def start_polling(
        self,
        on_weight: Optional[Callable[[ScaleReading], None]] = None,
        on_lock: Optional[Callable[[float], None]] = None,
    ) -> None:
        """Start background polling of the scale.

        Args:
            on_weight: Called on every reading with the ScaleReading.
            on_lock: Called when weight locks (3 consecutive stable readings).
        """
        if self._polling:
            return

        self._on_weight = on_weight
        self._on_lock = on_lock
        self._stable_count = 0
        self._locked_weight = None
        self._polling = True
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()
        logger.info("Scale polling started")

    def stop_polling(self) -> None:
        """Stop background polling."""
        self._polling = False
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=2.0)
        self._poll_thread = None
        logger.info("Scale polling stopped")

    def reset_lock(self) -> None:
        """Reset the weight lock for re-weighing."""
        with self._lock:
            self._stable_count = 0
            self._locked_weight = None
            self._last_weight = None

    @property
    def locked_weight(self) -> Optional[float]:
        """The locked weight, or None if not yet locked."""
        with self._lock:
            return self._locked_weight

    def _poll_loop(self) -> None:
        """Background thread: poll scale at POLL_INTERVAL."""
        while self._polling:
            try:
                reading = self.request_weight()

                if self._on_weight:
                    self._on_weight(reading)

                with self._lock:
                    if self._locked_weight is not None:
                        # Already locked, skip stability tracking
                        pass
                    elif reading.stable and reading.weight_lb > 0:
                        if (
                            self._last_weight is not None
                            and abs(reading.weight_lb - self._last_weight) < 0.01
                        ):
                            self._stable_count += 1
                        else:
                            self._stable_count = 1
                        self._last_weight = reading.weight_lb

                        if self._stable_count >= STABILITY_COUNT:
                            self._locked_weight = reading.weight_lb
                            logger.info("Weight locked: %.3f lb", reading.weight_lb)
                            if self._on_lock:
                                self._on_lock(reading.weight_lb)
                    else:
                        self._stable_count = 0
                        self._last_weight = None

            except ScaleError as e:
                logger.warning("Scale poll error: %s", e)

            time.sleep(POLL_INTERVAL)
