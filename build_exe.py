#!/usr/bin/env python3
"""
Build standalone Windows executable for Pomponio Ranch Labeling System.

Run this on a Windows machine:
    python build_exe.py

Output: dist/PomponioRanch.exe (single file, ~50MB)
"""

import subprocess
import sys
import shutil
from pathlib import Path

def main():
    # Ensure PyInstaller is installed
    print("Installing/updating PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"], check=True)

    # Get paths
    root = Path(__file__).parent

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                          # Single .exe file
        "--windowed",                         # No console window
        "--name", "PomponioRanch",            # Output name
        "--icon", "NONE",                     # No icon (add later if needed)
        "--add-data", f"data;data",           # Include data folder
        "--add-data", f"config.ini.example;.", # Include config template
        "--hidden-import", "customtkinter",
        "--hidden-import", "PIL",
        "--hidden-import", "qrcode",
        "--collect-all", "customtkinter",     # Get all customtkinter assets
        str(root / "run.py"),                 # Entry point
    ]

    print("\nBuilding executable...")
    print(" ".join(cmd))
    subprocess.run(cmd, cwd=root, check=True)

    print("\n" + "=" * 50)
    print("BUILD COMPLETE")
    print("=" * 50)
    print(f"\nExecutable: {root / 'dist' / 'PomponioRanch.exe'}")
    print("\nTo deploy:")
    print("  1. Copy PomponioRanch.exe to the target machine")
    print("  2. Double-click to run")
    print("\nThe app will run in mock mode by default.")
    print("To configure hardware, create config.ini next to the .exe")

if __name__ == "__main__":
    main()
