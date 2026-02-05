"""
USB Scale integration module.
Handles serial communication with weight scales.
Supports common protocols used by shipping/food scales.
"""

import threading
import time
from typing import Callable, Optional
from dataclasses import dataclass

try:
    import serial
    import serial.tools.list_ports
    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False


@dataclass
class WeightReading:
    """Weight reading from scale."""
    weight_lbs: float
    stable: bool
    unit: str = "LB"
    raw: str = ""


class ScaleError(Exception):
    """Scale communication error."""
    pass


class Scale:
    """
    USB Scale interface.

    Supports common serial scale protocols:
    - Continuous output: Scale sends weight continuously
    - Poll mode: Send command to request weight

    Most food/shipping scales use 9600 baud, 8N1.
    """

    def __init__(
        self,
        port: Optional[str] = None,
        baudrate: int = 9600,
        timeout: float = 1.0
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: Optional[serial.Serial] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._current_weight: Optional[WeightReading] = None
        self._weight_callback: Optional[Callable[[WeightReading], None]] = None
        self._stable_callback: Optional[Callable[[WeightReading], None]] = None
        self._last_stable_weight: Optional[float] = None

    @staticmethod
    def list_ports() -> list[str]:
        """List available serial ports."""
        if not SERIAL_AVAILABLE:
            return []
        ports = serial.tools.list_ports.comports()
        return [p.device for p in ports]

    @staticmethod
    def find_scale_port() -> Optional[str]:
        """Attempt to auto-detect scale port."""
        if not SERIAL_AVAILABLE:
            return None
        ports = serial.tools.list_ports.comports()
        for p in ports:
            desc = (p.description or "").lower()
            if any(kw in desc for kw in ["scale", "usb serial", "ch340", "ftdi", "prolific"]):
                return p.device
        return None

    def connect(self) -> bool:
        """Connect to scale. Returns True on success."""
        if not SERIAL_AVAILABLE:
            raise ScaleError("pyserial not installed")

        if self.port is None:
            self.port = self.find_scale_port()
            if self.port is None:
                raise ScaleError("No scale port found. Specify port manually.")

        try:
            self._serial = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            return True
        except serial.SerialException as e:
            raise ScaleError(f"Failed to connect to {self.port}: {e}")

    def disconnect(self):
        """Disconnect from scale."""
        self.stop_continuous()
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None

    def is_connected(self) -> bool:
        """Check if connected to scale."""
        return self._serial is not None and self._serial.is_open

    def read_weight(self) -> Optional[WeightReading]:
        """
        Read single weight from scale.
        Parses common scale output formats.
        """
        if not self.is_connected():
            raise ScaleError("Not connected to scale")

        try:
            self._serial.reset_input_buffer()
            line = self._serial.readline().decode('ascii', errors='ignore').strip()
            if line:
                return self._parse_weight(line)
            return None
        except serial.SerialException as e:
            raise ScaleError(f"Read error: {e}")

    def _parse_weight(self, line: str) -> Optional[WeightReading]:
        """
        Parse weight from scale output.

        Common formats:
        - "  12.34 LB" (spaces, weight, unit)
        - "S  12.34 LB" (S=stable, U=unstable)
        - "ST,GS,  12.34,LB" (CSV format)
        - "12.34" (just the number)
        """
        raw = line
        stable = True
        unit = "LB"
        weight = 0.0

        line = line.upper().strip()

        # Check stability indicator
        if line.startswith('U') or 'UNSTABLE' in line:
            stable = False
            line = line.lstrip('U').strip()
        elif line.startswith('S'):
            stable = True
            line = line.lstrip('S').strip()

        # Handle CSV format
        if ',' in line:
            parts = [p.strip() for p in line.split(',')]
            for part in parts:
                if part.replace('.', '').replace('-', '').isdigit():
                    weight = float(part)
                elif part in ('LB', 'KG', 'OZ', 'G'):
                    unit = part
        else:
            # Handle space-separated format
            parts = line.split()
            for part in parts:
                clean = part.replace('.', '').replace('-', '').lstrip('0') or '0'
                if clean.isdigit() or (part.startswith('-') and clean.isdigit()):
                    try:
                        weight = float(part)
                    except ValueError:
                        continue
                elif part in ('LB', 'KG', 'OZ', 'G'):
                    unit = part

        # Convert to pounds if needed
        if unit == 'KG':
            weight *= 2.20462
            unit = 'LB'
        elif unit == 'OZ':
            weight /= 16.0
            unit = 'LB'
        elif unit == 'G':
            weight *= 0.00220462
            unit = 'LB'

        return WeightReading(
            weight_lbs=round(weight, 2),
            stable=stable,
            unit=unit,
            raw=raw
        )

    def on_weight(self, callback: Callable[[WeightReading], None]):
        """Set callback for weight updates (all readings)."""
        self._weight_callback = callback

    def on_stable(self, callback: Callable[[WeightReading], None]):
        """Set callback for stable weight readings only."""
        self._stable_callback = callback

    def start_continuous(self):
        """Start continuous weight reading in background thread."""
        if self._running:
            return
        if not self.is_connected():
            raise ScaleError("Not connected to scale")

        self._running = True
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def stop_continuous(self):
        """Stop continuous weight reading."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _read_loop(self):
        """Background thread for continuous reading."""
        while self._running and self.is_connected():
            try:
                reading = self.read_weight()
                if reading:
                    self._current_weight = reading
                    if self._weight_callback:
                        self._weight_callback(reading)

                    # Fire stable callback only when weight stabilizes
                    if reading.stable and reading.weight_lbs > 0:
                        if self._last_stable_weight != reading.weight_lbs:
                            self._last_stable_weight = reading.weight_lbs
                            if self._stable_callback:
                                self._stable_callback(reading)
                    elif not reading.stable:
                        self._last_stable_weight = None

            except ScaleError:
                time.sleep(0.5)
            except Exception:
                time.sleep(0.1)

    @property
    def current_weight(self) -> Optional[WeightReading]:
        """Get most recent weight reading."""
        return self._current_weight

    def zero(self):
        """Send zero/tare command to scale."""
        if not self.is_connected():
            raise ScaleError("Not connected to scale")
        # Common zero commands
        for cmd in [b'Z\r\n', b'T\r\n', b'ZERO\r\n']:
            try:
                self._serial.write(cmd)
                time.sleep(0.1)
            except serial.SerialException:
                pass


class MockScale(Scale):
    """
    Mock scale for testing without hardware.
    Simulates weight readings.
    """

    def __init__(self):
        super().__init__()
        self._mock_weight = 0.0
        self._mock_stable = True

    def connect(self) -> bool:
        return True

    def disconnect(self):
        self.stop_continuous()

    def is_connected(self) -> bool:
        return True

    def read_weight(self) -> Optional[WeightReading]:
        return WeightReading(
            weight_lbs=self._mock_weight,
            stable=self._mock_stable,
            unit="LB",
            raw=f"S  {self._mock_weight:.2f} LB"
        )

    def set_weight(self, weight: float, stable: bool = True):
        """Set mock weight for testing."""
        self._mock_weight = weight
        self._mock_stable = stable

    def zero(self):
        self._mock_weight = 0.0


if __name__ == "__main__":
    print("Available ports:", Scale.list_ports())
    auto_port = Scale.find_scale_port()
    print("Auto-detected port:", auto_port)
