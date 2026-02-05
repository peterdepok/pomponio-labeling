@echo off
REM ============================================
REM  Build PomponioRanch.exe
REM  Run this ONCE on a Windows machine
REM ============================================

echo.
echo Building Pomponio Ranch executable...
echo.

REM Install dependencies
pip install -r requirements.txt
pip install pyinstaller

REM Build the exe
pyinstaller --onefile --windowed --name PomponioRanch ^
    --add-data "data;data" ^
    --add-data "config.ini.example;." ^
    --hidden-import customtkinter ^
    --hidden-import PIL ^
    --hidden-import qrcode ^
    --collect-all customtkinter ^
    run.py

echo.
echo ============================================
echo  BUILD COMPLETE
echo ============================================
echo.
echo Your executable is at: dist\PomponioRanch.exe
echo.
echo Copy that single file to any Windows PC and double-click to run.
echo.
pause
