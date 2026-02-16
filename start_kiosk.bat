@echo off
REM -----------------------------------------------------------
REM  Pomponio Ranch Labeling System -- Kiosk Launcher
REM
REM  Usage:
REM    start_kiosk.bat          -- manual launch (no delay)
REM    start_kiosk.bat --boot   -- auto-start on boot (10s delay)
REM
REM  Place a shortcut in shell:startup with --boot flag for
REM  auto-start on login. Desktop shortcut uses no flag.
REM
REM  Includes watchdog: if the process exits, waits 5s and
REM  re-launches (up to 10 restarts to prevent infinite loop).
REM -----------------------------------------------------------

REM --- Set working directory to project root ---
cd /d "%~dp0"

REM --- Boot delay: only when called with --boot flag ---
if "%1"=="--boot" (
    timeout /t 10 /nobreak >nul
)

REM --- Watchdog loop ---
set RESTART_COUNT=0
set MAX_RESTARTS=10

:loop
if %RESTART_COUNT% GEQ %MAX_RESTARTS% (
    echo [%date% %time%] Max restarts (%MAX_RESTARTS%) reached. Stopping watchdog. >> kiosk.log
    exit /b 1
)

echo [%date% %time%] Starting kiosk (restart #%RESTART_COUNT%) >> kiosk.log

if exist ".venv\Scripts\pythonw.exe" (
    ".venv\Scripts\pythonw.exe" run_production.py >> kiosk.log 2>&1
) else (
    pythonw run_production.py >> kiosk.log 2>&1
)

echo [%date% %time%] Process exited. Waiting 5s before restart... >> kiosk.log
set /a RESTART_COUNT=%RESTART_COUNT%+1
timeout /t 5 /nobreak >nul
goto loop
