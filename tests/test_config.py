"""
Tests for configuration module.
"""

import unittest
import tempfile
from pathlib import Path
from src.config import load_config, save_config, Config


class TestConfigLoading(unittest.TestCase):
    """Test configuration loading."""

    def test_load_defaults_when_no_file(self):
        """Test loading defaults when config file doesn't exist."""
        config = load_config(Path("/nonexistent/config.ini"))
        self.assertIsNotNone(config)
        self.assertIsNotNone(config.hardware)
        self.assertIsNotNone(config.app)

    def test_default_hardware_config(self):
        """Test default hardware configuration."""
        config = load_config(Path("/nonexistent/config.ini"))
        self.assertEqual(config.hardware.scale_baudrate, 9600)
        self.assertEqual(config.hardware.printer_type, 'mock')
        self.assertEqual(config.hardware.printer_tcp_port, 9100)

    def test_default_app_config(self):
        """Test default application configuration."""
        config = load_config(Path("/nonexistent/config.ini"))
        self.assertEqual(config.app.window_mode, 'maximized')
        self.assertEqual(config.app.touch_target_size, 60)
        self.assertTrue(config.app.audio_enabled)

    def test_default_label_config(self):
        """Test default label configuration."""
        config = load_config(Path("/nonexistent/config.ini"))
        self.assertEqual(config.labels.printer_dpi, 203)
        self.assertEqual(config.labels.package_label_width, 4)

    def test_load_from_file(self):
        """Test loading from actual config file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as f:
            f.write("""
[hardware]
scale_port = COM5
printer_type = network
printer_host = 192.168.1.100

[application]
window_mode = fullscreen
touch_target_size = 80
audio_enabled = false
""")
            temp_path = Path(f.name)

        try:
            config = load_config(temp_path)
            self.assertEqual(config.hardware.scale_port, 'COM5')
            self.assertEqual(config.hardware.printer_type, 'network')
            self.assertEqual(config.hardware.printer_host, '192.168.1.100')
            self.assertEqual(config.app.window_mode, 'fullscreen')
            self.assertEqual(config.app.touch_target_size, 80)
            self.assertFalse(config.app.audio_enabled)
        finally:
            temp_path.unlink(missing_ok=True)


class TestConfigSaving(unittest.TestCase):
    """Test configuration saving."""

    def test_save_and_reload(self):
        """Test saving config and reloading it."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.ini') as f:
            temp_path = Path(f.name)

        try:
            # Load defaults and modify
            config = load_config(Path("/nonexistent/config.ini"))

            # Save to temp file
            save_config(config, temp_path)

            # Reload and verify
            reloaded = load_config(temp_path)
            self.assertEqual(config.hardware.scale_baudrate, reloaded.hardware.scale_baudrate)
            self.assertEqual(config.app.window_mode, reloaded.app.window_mode)
        finally:
            temp_path.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
