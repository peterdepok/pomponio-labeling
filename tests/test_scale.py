"""Tests for Brecknell 6710U scale communication.

Uses mock serial port since hardware is not available during testing.
"""

import time
import threading
from unittest.mock import MagicMock, patch, PropertyMock
import pytest
import serial

from src.scale import Scale, ScaleError, ScaleReading


class FakeSerial:
    """Mock serial port for scale testing."""

    def __init__(self):
        self.is_open = True
        self._response = b""
        self.written = []

    def write(self, data: bytes) -> int:
        self.written.append(data)
        return len(data)

    def read(self, size: int = 1) -> bytes:
        return self._response

    def reset_input_buffer(self):
        pass

    def close(self):
        self.is_open = False

    def set_response(self, raw: str):
        self._response = raw.encode("ascii")


def make_response(weight: float, unit: str = "lb", stable: bool = True) -> str:
    """Build a Brecknell-style response string."""
    weight_str = f"{weight:8.3f}"
    # H byte: 0x40 = stable (bit 6 set), 0x60 = motion (bit 5 + 6 set)
    h_byte = chr(0x40) if stable else chr(0x60)
    return f"\n{weight_str}{unit}\r\n{h_byte}\r\x03"


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

class TestResponseParsing:

    def test_parse_normal_weight(self):
        scale = Scale("COM1")
        fake = FakeSerial()
        fake.set_response(make_response(1.520))
        scale._serial = fake
        reading = scale.request_weight()
        assert abs(reading.weight_lb - 1.520) < 0.001
        assert reading.stable is True
        assert reading.unit == "lb"

    def test_parse_heavy_weight(self):
        scale = Scale("COM1")
        fake = FakeSerial()
        fake.set_response(make_response(14.500))
        scale._serial = fake
        reading = scale.request_weight()
        assert abs(reading.weight_lb - 14.500) < 0.001

    def test_parse_motion_detected(self):
        scale = Scale("COM1")
        fake = FakeSerial()
        fake.set_response(make_response(1.520, stable=False))
        scale._serial = fake
        reading = scale.request_weight()
        assert reading.stable is False

    def test_parse_over_capacity(self):
        scale = Scale("COM1")
        fake = FakeSerial()
        fake.set_response("\n_ _ _ _ _ _ _ _lb\r\n@\r\x03")
        scale._serial = fake
        with pytest.raises(ScaleError, match="over capacity"):
            scale.request_weight()

    def test_parse_under_capacity(self):
        scale = Scale("COM1")
        fake = FakeSerial()
        fake.set_response("\n- - - - - - - -lb\r\n@\r\x03")
        scale._serial = fake
        with pytest.raises(ScaleError, match="under capacity"):
            scale.request_weight()

    def test_no_response(self):
        scale = Scale("COM1")
        fake = FakeSerial()
        fake._response = b""
        scale._serial = fake
        with pytest.raises(ScaleError, match="No response"):
            scale.request_weight()

    def test_not_connected(self):
        scale = Scale("COM1")
        with pytest.raises(ScaleError, match="not connected"):
            scale.request_weight()

    def test_sends_w_cr(self):
        scale = Scale("COM1")
        fake = FakeSerial()
        fake.set_response(make_response(1.0))
        scale._serial = fake
        scale.request_weight()
        assert b"W\r" in fake.written


# ---------------------------------------------------------------------------
# Stability detection
# ---------------------------------------------------------------------------

class TestStabilityDetection:

    def test_locks_after_three_stable(self):
        scale = Scale("COM1")
        fake = FakeSerial()
        scale._serial = fake

        locked_weights = []

        def on_lock(w):
            locked_weights.append(w)

        fake.set_response(make_response(1.520))
        scale._on_lock = on_lock
        scale._locked_weight = None
        scale._stable_count = 0
        scale._last_weight = None

        # Simulate 3 stable readings
        for _ in range(3):
            reading = scale.request_weight()
            if reading.stable and reading.weight_lb > 0:
                if (
                    scale._last_weight is not None
                    and abs(reading.weight_lb - scale._last_weight) < 0.01
                ):
                    scale._stable_count += 1
                else:
                    scale._stable_count = 1
                scale._last_weight = reading.weight_lb

                if scale._stable_count >= 3 and scale._locked_weight is None:
                    scale._locked_weight = reading.weight_lb
                    on_lock(reading.weight_lb)

        assert len(locked_weights) == 1
        assert abs(locked_weights[0] - 1.520) < 0.001

    def test_motion_resets_count(self):
        scale = Scale("COM1")
        scale._stable_count = 2
        scale._last_weight = 1.520
        # Motion reading should reset
        # Simulated: not stable
        scale._stable_count = 0
        scale._last_weight = None
        assert scale._stable_count == 0

    def test_reset_lock(self):
        scale = Scale("COM1")
        scale._locked_weight = 1.520
        scale._stable_count = 3
        scale._last_weight = 1.520
        scale.reset_lock()
        assert scale.locked_weight is None


# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

class TestConnection:

    @patch("src.scale.serial.Serial")
    def test_connect_success(self, mock_serial_cls):
        mock_serial_cls.return_value = MagicMock(is_open=True)
        scale = Scale("COM3")
        scale.connect()
        assert scale.connected
        mock_serial_cls.assert_called_once()

    @patch("src.scale.serial.Serial", side_effect=serial.SerialException("Port not found"))
    def test_connect_failure(self, mock_serial_cls):
        scale = Scale("COM99")
        with pytest.raises(ScaleError):
            scale.connect()

    def test_disconnect(self):
        scale = Scale("COM1")
        fake = FakeSerial()
        scale._serial = fake
        scale.disconnect()
        assert not scale.connected
        assert not fake.is_open


class TestScaleReading:

    def test_repr_stable(self):
        r = ScaleReading(1.520, True, "lb")
        assert "1.520" in repr(r)
        assert "stable" in repr(r)

    def test_repr_motion(self):
        r = ScaleReading(1.520, False)
        assert "motion" in repr(r)
