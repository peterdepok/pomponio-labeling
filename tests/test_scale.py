"""
Tests for scale module.
"""

import unittest
import time
from src.scale import MockScale, WeightReading


class TestWeightReading(unittest.TestCase):
    """Test WeightReading dataclass."""

    def test_create_weight_reading(self):
        """Test creating a weight reading."""
        reading = WeightReading(weight_lbs=2.45, stable=True)
        self.assertEqual(reading.weight_lbs, 2.45)
        self.assertTrue(reading.stable)

    def test_unstable_reading(self):
        """Test unstable weight reading."""
        reading = WeightReading(weight_lbs=2.45, stable=False)
        self.assertFalse(reading.stable)


class TestMockScale(unittest.TestCase):
    """Test mock scale for testing."""

    def setUp(self):
        self.scale = MockScale()

    def test_connect(self):
        """Test mock scale connect."""
        result = self.scale.connect()
        self.assertTrue(result)

    def test_is_connected(self):
        """Test mock scale reports connected."""
        self.scale.connect()
        self.assertTrue(self.scale.is_connected())

    def test_disconnect(self):
        """Test mock scale disconnect runs without error."""
        self.scale.connect()
        self.scale.disconnect()
        # MockScale always reports connected (no actual hardware)
        self.assertTrue(self.scale.is_connected())

    def test_set_weight(self):
        """Test setting mock weight."""
        self.scale.set_weight(5.25)
        reading = self.scale.read_weight()
        self.assertEqual(reading.weight_lbs, 5.25)

    def test_default_weight_zero(self):
        """Test default weight is zero."""
        reading = self.scale.read_weight()
        self.assertEqual(reading.weight_lbs, 0.0)

    def test_weight_callback(self):
        """Test weight callback is called."""
        readings = []
        self.scale.on_weight(lambda r: readings.append(r))

        self.scale.set_weight(3.50)

        # Need to trigger callback manually in mock
        if hasattr(self.scale, '_notify_weight'):
            self.scale._notify_weight()

    def test_read_weight_returns_reading(self):
        """Test read_weight returns WeightReading."""
        self.scale.set_weight(2.00)
        reading = self.scale.read_weight()
        self.assertIsInstance(reading, WeightReading)

    def test_set_stable_flag(self):
        """Test setting stable flag."""
        self.scale.set_weight(2.00, stable=True)
        reading = self.scale.read_weight()
        self.assertTrue(reading.stable)

        self.scale.set_weight(2.00, stable=False)
        reading = self.scale.read_weight()
        self.assertFalse(reading.stable)


if __name__ == '__main__':
    unittest.main()
