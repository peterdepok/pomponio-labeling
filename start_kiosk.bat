@echo off
REM ───────────────────────────────────────────────────────
REM  Pomponio Ranch Labeling System — Kiosk Auto-Start
REM
REM  Place a shortcut to this file in:
REM    shell:startup   (Win+R, type "shell:startup", Enter)
REM
REM  Waits 10 seconds for Windows networking and USB devices
REM  to settle, then launches run_production.py headlessly.
REM  Logs output to kiosk.log for debugging.
REM ───────────────────────────────────────────────────────

REM --- Wait for system to settle after login ---
timeout /t 10 /nobreak >nul

REM --- Set working directory to project root ---
cd /d "%~dp0"

REM --- Launch production server (no console window via pythonw) ---
REM    If pythonw is not on PATH, try the full venv path.
REM    Output goes to kiosk.log so crashes are diagnosable.
if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" run_production.py >kiosk.log 2>&1
) else (
    start "" pythonw run_production.py >kiosk.log 2>&1
)
