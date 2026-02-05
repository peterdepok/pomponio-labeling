"""
Configuration management for Pomponio Ranch Labeling System.
Loads settings from config.ini file.
"""

import configparser
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


CONFIG_FILE = Path(__file__).parent.parent / "config.ini"


@dataclass
class HardwareConfig:
    scale_port: Optional[str]
    scale_baudrate: int
    printer_type: str  # serial, network, mock
    printer_port: Optional[str]
    printer_host: Optional[str]
    printer_tcp_port: int


@dataclass
class AppConfig:
    window_mode: str  # normal, maximized, fullscreen
    touch_target_size: int
    audio_enabled: bool


@dataclass
class DatabaseConfig:
    db_path: str


@dataclass
class LabelConfig:
    printer_dpi: int
    package_label_width: float
    package_label_height: float
    box_label_width: float
    box_label_height: float


@dataclass
class EmailConfig:
    enabled: bool
    smtp_server: str
    smtp_port: int
    smtp_user: str
    smtp_password: str
    from_email: str
    back_office_email: str


@dataclass
class Config:
    hardware: HardwareConfig
    app: AppConfig
    database: DatabaseConfig
    labels: LabelConfig
    email: EmailConfig


def load_config(config_path: Optional[Path] = None) -> Config:
    """
    Load configuration from file.
    Falls back to defaults if file doesn't exist.
    """
    path = config_path or CONFIG_FILE
    parser = configparser.ConfigParser()

    # Set defaults
    parser['hardware'] = {
        'scale_port': '',
        'scale_baudrate': '9600',
        'printer_type': 'mock',
        'printer_port': '',
        'printer_host': '',
        'printer_tcp_port': '9100',
    }
    parser['application'] = {
        'window_mode': 'maximized',
        'touch_target_size': '60',
        'audio_enabled': 'true',
    }
    parser['database'] = {
        'db_path': 'data/pomponio.db',
    }
    parser['labels'] = {
        'printer_dpi': '203',
        'package_label_width': '4',
        'package_label_height': '2',
        'box_label_width': '4',
        'box_label_height': '3',
    }
    parser['email'] = {
        'enabled': 'false',
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': '587',
        'smtp_user': '',
        'smtp_password': '',
        'from_email': '',
        'back_office_email': '',
    }

    # Load from file if exists
    if path.exists():
        parser.read(path)

    # Build config objects
    hw = parser['hardware']
    hardware = HardwareConfig(
        scale_port=hw.get('scale_port') or None,
        scale_baudrate=int(hw.get('scale_baudrate', 9600)),
        printer_type=hw.get('printer_type', 'mock'),
        printer_port=hw.get('printer_port') or None,
        printer_host=hw.get('printer_host') or None,
        printer_tcp_port=int(hw.get('printer_tcp_port', 9100)),
    )

    app_section = parser['application']
    app = AppConfig(
        window_mode=app_section.get('window_mode', 'maximized'),
        touch_target_size=int(app_section.get('touch_target_size', 60)),
        audio_enabled=app_section.getboolean('audio_enabled', True),
    )

    db_section = parser['database']
    database = DatabaseConfig(
        db_path=db_section.get('db_path', 'data/pomponio.db'),
    )

    label_section = parser['labels']
    labels = LabelConfig(
        printer_dpi=int(label_section.get('printer_dpi', 203)),
        package_label_width=float(label_section.get('package_label_width', 4)),
        package_label_height=float(label_section.get('package_label_height', 2)),
        box_label_width=float(label_section.get('box_label_width', 4)),
        box_label_height=float(label_section.get('box_label_height', 3)),
    )

    email_section = parser['email']
    email = EmailConfig(
        enabled=email_section.getboolean('enabled', False),
        smtp_server=email_section.get('smtp_server', 'smtp.gmail.com'),
        smtp_port=int(email_section.get('smtp_port', 587)),
        smtp_user=email_section.get('smtp_user', ''),
        smtp_password=email_section.get('smtp_password', ''),
        from_email=email_section.get('from_email', ''),
        back_office_email=email_section.get('back_office_email', ''),
    )

    return Config(
        hardware=hardware,
        app=app,
        database=database,
        labels=labels,
        email=email,
    )


def save_config(config: Config, config_path: Optional[Path] = None):
    """Save configuration to file."""
    path = config_path or CONFIG_FILE
    parser = configparser.ConfigParser()

    parser['hardware'] = {
        'scale_port': config.hardware.scale_port or '',
        'scale_baudrate': str(config.hardware.scale_baudrate),
        'printer_type': config.hardware.printer_type,
        'printer_port': config.hardware.printer_port or '',
        'printer_host': config.hardware.printer_host or '',
        'printer_tcp_port': str(config.hardware.printer_tcp_port),
    }
    parser['application'] = {
        'window_mode': config.app.window_mode,
        'touch_target_size': str(config.app.touch_target_size),
        'audio_enabled': str(config.app.audio_enabled).lower(),
    }
    parser['database'] = {
        'db_path': config.database.db_path,
    }
    parser['labels'] = {
        'printer_dpi': str(config.labels.printer_dpi),
        'package_label_width': str(config.labels.package_label_width),
        'package_label_height': str(config.labels.package_label_height),
        'box_label_width': str(config.labels.box_label_width),
        'box_label_height': str(config.labels.box_label_height),
    }
    parser['email'] = {
        'enabled': str(config.email.enabled).lower(),
        'smtp_server': config.email.smtp_server,
        'smtp_port': str(config.email.smtp_port),
        'smtp_user': config.email.smtp_user,
        'smtp_password': config.email.smtp_password,
        'from_email': config.email.from_email,
        'back_office_email': config.email.back_office_email,
    }

    with open(path, 'w') as f:
        parser.write(f)


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get global config instance (lazy loaded)."""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config():
    """Reload config from file."""
    global _config
    _config = load_config()


if __name__ == '__main__':
    config = load_config()
    print(f"Hardware: {config.hardware}")
    print(f"App: {config.app}")
    print(f"Database: {config.database}")
    print(f"Labels: {config.labels}")
