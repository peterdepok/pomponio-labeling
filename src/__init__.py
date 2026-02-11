"""Pomponio Ranch Labeling & Inventory System"""

import sys
from pathlib import Path

__version__ = "1.0.0"


def get_app_dir() -> Path:
    """
    Get the application root directory.

    - Frozen (PyInstaller EXE): directory containing the executable
    - Script mode (dev): project root (parent of src/)
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def get_resource_dir() -> Path:
    """
    Get the directory for bundled read-only resources (data files shipped with the app).

    - Frozen (PyInstaller --onefile): sys._MEIPASS temp extraction dir
    - Frozen (PyInstaller --onedir): directory containing the executable
    - Script mode (dev): project root (parent of src/)
    """
    if getattr(sys, 'frozen', False):
        return Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
    return Path(__file__).parent.parent
