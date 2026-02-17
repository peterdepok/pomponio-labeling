"""Configuration management for the Pomponio Ranch Labeling System.

Reads and writes config.ini for hardware settings, paths, and defaults.
Config.ini survives application updates.
"""

import configparser
import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_CONFIG = {
    "scale": {
        "com_port": "COM3",
        "baud_rate": "9600",
    },
    "printer": {
        "name": "zebra",
        "template_dir": "data/templates",
    },
    "database": {
        "path": "data/pomponio.db",
    },
    "app": {
        "version": "1.0.0",
        "log_level": "INFO",
        "log_file": "pomponio.log",
    },
    "email": {
        "resend_api_key": "",
        "from": "Pomponio Ranch <onboarding@resend.dev>",
    },
}


class Config:
    """Application configuration backed by config.ini."""

    def __init__(self, config_path: str = "config.ini"):
        self.config_path = config_path
        self._config = configparser.ConfigParser()
        self._load_defaults()

    def _load_defaults(self) -> None:
        """Populate config with default values."""
        for section, values in DEFAULT_CONFIG.items():
            if not self._config.has_section(section):
                self._config.add_section(section)
            for key, value in values.items():
                self._config.set(section, key, value)

    def load(self) -> None:
        """Load config from file, merging with defaults."""
        if os.path.exists(self.config_path):
            self._config.read(self.config_path)
            logger.info("Config loaded from %s", self.config_path)
        else:
            logger.info("No config file found, using defaults")

    def save(self) -> None:
        """Write current config to file."""
        with open(self.config_path, "w") as f:
            self._config.write(f)
        logger.info("Config saved to %s", self.config_path)

    def get(self, section: str, key: str, fallback: Optional[str] = None) -> str:
        """Get a config value."""
        return self._config.get(section, key, fallback=fallback)

    def get_int(self, section: str, key: str, fallback: int = 0) -> int:
        """Get a config value as integer."""
        return self._config.getint(section, key, fallback=fallback)

    def set(self, section: str, key: str, value: str) -> None:
        """Set a config value."""
        if not self._config.has_section(section):
            self._config.add_section(section)
        self._config.set(section, key, value)

    # Convenience properties

    @property
    def scale_port(self) -> str:
        return self.get("scale", "com_port")

    @scale_port.setter
    def scale_port(self, value: str) -> None:
        self.set("scale", "com_port", value)

    @property
    def scale_baud_rate(self) -> int:
        return self.get_int("scale", "baud_rate", fallback=9600)

    @property
    def printer_name(self) -> str:
        return self.get("printer", "name")

    @printer_name.setter
    def printer_name(self, value: str) -> None:
        self.set("printer", "name", value)

    @property
    def template_dir(self) -> str:
        return self.get("printer", "template_dir")

    @property
    def db_path(self) -> str:
        return self.get("database", "path")

    @property
    def version(self) -> str:
        return self.get("app", "version")

    @property
    def log_level(self) -> str:
        return self.get("app", "log_level")

    @property
    def log_file(self) -> str:
        return self.get("app", "log_file")

    @property
    def resend_api_key(self) -> str:
        return self.get("email", "resend_api_key")

    @property
    def resend_from(self) -> str:
        return self.get("email", "from", fallback="Pomponio Ranch <onboarding@resend.dev>")

    def validate(self) -> list[str]:
        """Check configuration for common problems.

        Returns a list of human-readable warning strings. An empty list
        means no issues detected. Called by /api/health to surface
        config problems to the operator.
        """
        warnings: list[str] = []

        if not os.path.exists(self.config_path):
            warnings.append("config.ini not found; using defaults. Printer and scale settings may be wrong.")

        # Printer name: default "zebra" is almost certainly wrong
        pn = self.printer_name
        if pn == DEFAULT_CONFIG["printer"]["name"]:
            warnings.append(f"Printer name is still default (\"{pn}\"). Check Settings.")

        # Scale port: verify the COM port is plausible (COMn where n is a digit)
        sp = self.scale_port
        if not (sp.upper().startswith("COM") and sp[3:].isdigit()):
            warnings.append(f"Scale port \"{sp}\" does not look like a valid COM port.")

        # Email API key
        if not self.resend_api_key:
            warnings.append("Email API key is blank. Reports will not send.")

        return warnings
