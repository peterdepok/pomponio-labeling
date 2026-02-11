#!/usr/bin/env python3
"""
Build standalone executable for Pomponio Ranch Labeling System.

Works on both Windows and macOS:
    python build_exe.py

Output:
    Windows: dist/PomponioRanch.exe
    macOS:   dist/PomponioRanch
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path

# PyInstaller uses os.pathsep for --add-data: ';' on Windows, ':' on macOS/Linux
SEP = os.pathsep


def main():
    # Ensure PyInstaller is installed
    print("Installing/updating PyInstaller...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pyinstaller"], check=True)

    # Get paths
    root = Path(__file__).parent
    is_windows = sys.platform == "win32"

    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",                                    # Single file
        "--name", "PomponioRanch",                      # Output name
        "--icon", "NONE",                               # No icon (add later if needed)
        "--add-data", f"data{SEP}data",                 # Include data folder
        "--add-data", f"config.ini.example{SEP}.",      # Include config template
        "--hidden-import", "customtkinter",
        "--hidden-import", "PIL",
        "--hidden-import", "qrcode",
        "--collect-all", "customtkinter",               # Get all customtkinter assets
    ]

    # --windowed: suppress console on Windows, skip on macOS dev builds
    # (on macOS this creates a .app bundle which is not what we want for dev)
    if is_windows:
        cmd.append("--windowed")

    cmd.append(str(root / "run.py"))  # Entry point

    print("\nBuilding executable...")
    print(" ".join(cmd))
    subprocess.run(cmd, cwd=root, check=True)

    exe_name = "PomponioRanch.exe" if is_windows else "PomponioRanch"
    print("\n" + "=" * 50)
    print("BUILD COMPLETE")
    print("=" * 50)
    print(f"\nExecutable: {root / 'dist' / exe_name}")
    print("\nTo deploy:")
    print(f"  1. Copy {exe_name} to the target machine")
    print("  2. Double-click to run")
    print("\nThe app will run in mock mode by default.")
    print(f"To configure hardware, create config.ini next to {exe_name}")

if __name__ == "__main__":
    main()
