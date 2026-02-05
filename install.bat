@echo off
REM Pomponio Ranch Labeling System - Windows Installer
REM Run this script as Administrator for best results

echo.
echo ============================================
echo  Pomponio Ranch Labeling System Installer
echo ============================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.11+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo [1/4] Python found:
python --version
echo.

REM Get the directory where this script is located
set INSTALL_DIR=%~dp0
cd /d "%INSTALL_DIR%"

echo [2/4] Installing Python dependencies...
echo.
pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install dependencies
    echo Try running this script as Administrator
    pause
    exit /b 1
)
echo.

echo [3/4] Initializing database and importing products...
echo.
python scripts/import_products.py data/beef_cuts.csv
if errorlevel 1 (
    echo.
    echo WARNING: Could not import products. You can do this manually later.
)
echo.

echo [4/4] Creating desktop shortcut...
echo.

REM Create a VBS script to make the shortcut
echo Set oWS = WScript.CreateObject("WScript.Shell") > "%TEMP%\CreateShortcut.vbs"
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\Pomponio Ranch.lnk" >> "%TEMP%\CreateShortcut.vbs"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "%TEMP%\CreateShortcut.vbs"
echo oLink.TargetPath = "pythonw.exe" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Arguments = """%INSTALL_DIR%run.py"" --mock" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.WorkingDirectory = "%INSTALL_DIR%" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Description = "Pomponio Ranch Labeling System" >> "%TEMP%\CreateShortcut.vbs"
echo oLink.Save >> "%TEMP%\CreateShortcut.vbs"

cscript //nologo "%TEMP%\CreateShortcut.vbs"
del "%TEMP%\CreateShortcut.vbs"

echo.
echo ============================================
echo  Installation Complete
echo ============================================
echo.
echo A shortcut "Pomponio Ranch" has been created on your desktop.
echo.
echo NEXT STEPS:
echo   1. Copy config.ini.example to config.ini
echo   2. Edit config.ini with your hardware settings:
echo      - Scale COM port (e.g., COM3)
echo      - Printer IP address or COM port
echo   3. Double-click the desktop shortcut to run
echo.
echo To run with mock hardware (testing):
echo   python run.py --mock
echo.
echo To run with real hardware:
echo   python run.py --scale-port COM3 --printer-host 192.168.1.100
echo.
pause
