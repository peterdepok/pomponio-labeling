@echo off
REM Pomponio Ranch Labeling System Launcher
REM Double-click to run with settings from config.ini

cd /d "%~dp0"

REM Check if config.ini exists
if exist config.ini (
    echo Loading configuration from config.ini...
    python run.py
) else (
    echo No config.ini found - running in mock hardware mode
    echo To use real hardware, copy config.ini.example to config.ini
    echo.
    python run.py --mock
)

if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)
