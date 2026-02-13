# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Pomponio Ranch Labeling System.

Builds a --onedir bundle (faster startup than --onefile on the N95).
Includes the React build (dist/), data files (templates, SKUs),
config.ini, and the Python bridge + hardware drivers.

Build:
    pyinstaller pomponio.spec

Output:
    dist_pyinstaller/PomponioLabel/PomponioLabel.exe
"""

import os

block_cipher = None

a = Analysis(
    ["run_production.py"],
    pathex=[],
    binaries=[],
    datas=[
        ("dist", "dist"),                   # React build output
        ("data", "data"),                   # Templates, SKU CSV
        ("bridge", "bridge"),               # Flask bridge package
        ("src/__init__.py", "src"),          # src package marker
        ("src/scale.py", "src"),             # Scale driver
        ("src/printer.py", "src"),           # Printer driver
        ("src/config.py", "src"),            # Config manager
    ],
    hiddenimports=[
        "win32print",
        "win32api",
        "pywintypes",
        "serial",
        "serial.tools",
        "serial.tools.list_ports",
        "flask",
        "flask.json",
        "flask.json.provider",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "customtkinter",   # Desktop UI not used in production bridge
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "PIL",
    ],
    noarchive=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PomponioLabel",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,  # Keep console window for debugging; set False for kiosk release
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="PomponioLabel",
)
