# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for Pomponio Ranch Labeling System.

Cross-platform: works on Windows (production) and macOS (development).

Build with:
    pyinstaller PomponioRanch.spec

Or just run:
    python build_exe.py
"""

import sys
import os
from pathlib import Path

block_cipher = None
root = Path(SPECPATH)
is_windows = sys.platform == 'win32'

a = Analysis(
    [str(root / 'run.py')],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / 'data'), 'data'),
        (str(root / 'config.ini.example'), '.'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL._tkinter_finder',
        'qrcode',
        'qrcode.image.pure',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Collect customtkinter assets
from PyInstaller.utils.hooks import collect_all
ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all('customtkinter')
a.datas += ctk_datas
a.binaries += ctk_binaries
a.hiddenimports += ctk_hiddenimports

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='PomponioRanch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=not is_windows,  # Show console on macOS for dev, hide on Windows
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
