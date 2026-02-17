@echo off
setlocal enabledelayedexpansion
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
REM  Exit code 42 = intentional operator shutdown. Watchdog stops.
REM  Any other exit code = crash or update restart. Watchdog relaunches.
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

REM --- SCORCHED EARTH: kill everything from previous session ---
REM   Chrome's multi-process architecture (browser, GPU, renderer, crashpad)
REM   survives partial kills. Python daemon threads can hold the port after
REM   os._exit. The only reliable approach on a kiosk: kill all Chrome and
REM   Python processes, free the port, wait for the OS to release handles,
REM   then nuke the Chrome profile to prevent session restore.

echo [%date% %time%] Cleanup: killing all Chrome and Python processes... >> kiosk.log
taskkill /F /IM chrome.exe >nul 2>&1
taskkill /F /IM python.exe >nul 2>&1

REM Kill any process holding port 8000 (catches edge cases)
for /f "tokens=5" %%P in ('netstat -aon ^| findstr ":8000.*LISTENING" 2^>nul') do (
    echo [%date% %time%] Killing leftover process on port 8000 ^(PID %%P^) >> kiosk.log
    taskkill /F /PID %%P >nul 2>&1
)

REM Let Windows fully release all handles, sockets, and file locks.
REM 3 seconds is enough for TIME_WAIT recycling when combined with
REM SO_REUSEADDR in the Python code.
echo [%date% %time%] Waiting 3s for OS cleanup... >> kiosk.log
timeout /t 3 /nobreak >nul

REM Delete the Chrome kiosk profile entirely. Forces a completely clean
REM browser state: no session restore, no cached error pages, no stale
REM lock files. Chrome recreates the profile on next launch.
if exist ".kiosk-profile" (
    echo [%date% %time%] Deleting Chrome kiosk profile... >> kiosk.log
    rmdir /s /q ".kiosk-profile" >nul 2>&1
)

REM --- Log rotation: keep kiosk.log under 10 MB ---
REM   If the file exceeds 10 485 760 bytes, archive the old log with
REM   a timestamp suffix and start fresh. Uses wmic for a locale-
REM   independent timestamp (YYYYMMDDHHmmss) to avoid collisions.
REM   Requires delayed expansion (set at top of script) so variables
REM   set inside parenthesized blocks expand correctly.
if exist kiosk.log (
    for %%A in (kiosk.log) do (
        if %%~zA GTR 10485760 (
            for /f "tokens=2 delims==" %%T in ('wmic os get localdatetime /value 2^>nul ^| find "="') do set "STAMP=%%T"
            copy kiosk.log "kiosk_!STAMP:~0,14!.log" >nul 2>&1
            echo. > kiosk.log
            echo [%date% %time%] Log rotated ^(exceeded 10 MB^). Previous log archived. >> kiosk.log
        )
    )
)

if %RESTART_COUNT% GEQ %MAX_RESTARTS% (
    echo [%date% %time%] Max restarts (%MAX_RESTARTS%^) reached. Stopping watchdog. >> kiosk.log
    exit /b 1
)

echo [%date% %time%] Starting kiosk (restart #%RESTART_COUNT%^) using %PYTHON_EXE% >> kiosk.log

%PYTHON_EXE% run_production.py >> kiosk.log 2>&1
set EXIT_CODE=%ERRORLEVEL%

REM --- Exit code 42 = operator pressed Exit. Stop the watchdog. ---
if %EXIT_CODE% EQU 42 (
    echo [%date% %time%] Operator shutdown (exit code 42^). Watchdog stopping. >> kiosk.log
    taskkill /F /IM chrome.exe >nul 2>&1
    taskkill /F /IM python.exe >nul 2>&1
    for /f "tokens=5" %%P in ('netstat -aon ^| findstr ":8000.*LISTENING" 2^>nul') do (
        taskkill /F /PID %%P >nul 2>&1
    )
    exit /b 0
)

echo [%date% %time%] Process exited (code %EXIT_CODE%^). Restarting... >> kiosk.log
set /a RESTART_COUNT=%RESTART_COUNT%+1

REM The :loop target handles all cleanup (kill Chrome, kill Python,
REM free port, wait 3s, delete profile). Just go there.
goto loop
