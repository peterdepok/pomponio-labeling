@echo off
REM ───────────────────────────────────────────────────────
REM  Pomponio Ranch Labeling System — Kiosk Launcher
REM
REM  Usage:
REM    start_kiosk.bat          — manual launch (no delay)
REM    start_kiosk.bat --boot   — auto-start on boot (10s delay)
REM
REM  Place a shortcut in shell:startup with --boot flag for
REM  auto-start on login. Desktop shortcut uses no flag.
REM ───────────────────────────────────────────────────────

REM --- Set working directory to project root ---
cd /d "%~dp0"

REM --- Boot delay: only when called with --boot flag ---
if "%1"=="--boot" (
    timeout /t 10 /nobreak >nul
)

REM --- Launch production server (no console window via pythonw) ---
REM    Output goes to kiosk.log so crashes are diagnosable.
if exist ".venv\Scripts\pythonw.exe" (
    ".venv\Scripts\pythonw.exe" run_production.py >kiosk.log 2>&1
) else (
    pythonw run_production.py >kiosk.log 2>&1
)
