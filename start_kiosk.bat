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
REM
REM  Uses python.exe (not pythonw) so all errors are captured
REM  in kiosk.log. The console window is minimized automatically.
REM -----------------------------------------------------------

REM --- Set working directory to project root ---
cd /d "%~dp0"

REM --- Boot delay: only when called with --boot flag ---
if "%1"=="--boot" (
    timeout /t 10 /nobreak >nul
)

REM --- Resolve Python interpreter ---
REM Priority: .venv > py launcher > bare python
set PYTHON_EXE=
if exist ".venv\Scripts\python.exe" (
    set "PYTHON_EXE=.venv\Scripts\python.exe"
    echo [%date% %time%] Using .venv Python >> kiosk.log
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=py -3"
        echo [%date% %time%] WARNING: .venv not found, falling back to py launcher >> kiosk.log
    ) else (
        where python >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=python"
            echo [%date% %time%] WARNING: .venv not found, falling back to system python >> kiosk.log
        )
    )
)

if "%PYTHON_EXE%"=="" (
    echo [%date% %time%] FATAL: No Python interpreter found. Cannot start kiosk. >> kiosk.log
    echo No Python interpreter found. Install Python or create .venv.
    pause
    exit /b 1
)

REM --- Watchdog loop ---
set RESTART_COUNT=0
set MAX_RESTARTS=10

:loop
if %RESTART_COUNT% GEQ %MAX_RESTARTS% (
    echo [%date% %time%] Max restarts (%MAX_RESTARTS%^) reached. Stopping watchdog. >> kiosk.log
    exit /b 1
)

echo [%date% %time%] Starting kiosk (restart #%RESTART_COUNT%^) using %PYTHON_EXE% >> kiosk.log

%PYTHON_EXE% run_production.py >> kiosk.log 2>&1

echo [%date% %time%] Process exited (code %ERRORLEVEL%^). Waiting 5s before restart... >> kiosk.log
set /a RESTART_COUNT=%RESTART_COUNT%+1
timeout /t 5 /nobreak >nul
goto loop
