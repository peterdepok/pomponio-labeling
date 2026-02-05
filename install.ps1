# Pomponio Ranch Labeling System - Windows PowerShell Installer
# Run: powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Pomponio Ranch Labeling System Installer" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check for Python
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[1/5] Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Python 3.11+ from https://www.python.org/downloads/"
    Write-Host "Make sure to check 'Add Python to PATH' during installation"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Get script directory
$InstallDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $InstallDir

Write-Host ""
Write-Host "[2/5] Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

Write-Host ""
Write-Host "[3/5] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    Write-Host "Try running PowerShell as Administrator"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[4/5] Initializing database and importing products..." -ForegroundColor Yellow
python scripts/import_products.py data/beef_cuts.csv
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Could not import products. You can do this manually later." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "[5/5] Creating desktop shortcut..." -ForegroundColor Yellow

# Create desktop shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Desktop = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$Desktop\Pomponio Ranch.lnk")
$Shortcut.TargetPath = "pythonw.exe"
$Shortcut.Arguments = "`"$InstallDir\run.py`" --mock"
$Shortcut.WorkingDirectory = $InstallDir
$Shortcut.Description = "Pomponio Ranch Labeling System"
$Shortcut.Save()

Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host " Installation Complete" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "A shortcut 'Pomponio Ranch' has been created on your desktop."
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Cyan
Write-Host "  1. Copy config.ini.example to config.ini"
Write-Host "  2. Edit config.ini with your hardware settings:"
Write-Host "     - Scale COM port (e.g., COM3)"
Write-Host "     - Printer IP address or COM port"
Write-Host "  3. Double-click the desktop shortcut to run"
Write-Host ""
Write-Host "To run with mock hardware (testing):"
Write-Host "  python run.py --mock" -ForegroundColor White
Write-Host ""
Write-Host "To run with real hardware:"
Write-Host "  python run.py --scale-port COM3 --printer-host 192.168.1.100" -ForegroundColor White
Write-Host ""

# Ask if user wants to run now
$RunNow = Read-Host "Run application now in mock mode? (Y/N)"
if ($RunNow -eq "Y" -or $RunNow -eq "y") {
    Write-Host ""
    Write-Host "Starting Pomponio Ranch..." -ForegroundColor Green
    python run.py --mock
}
