# Pomponio Ranch Labeling & Inventory System

Desktop labeling application for meat processing operations at Sinton & Sons.

## Windows Installation (Recommended)

1. Install Python 3.11+ from https://www.python.org/downloads/
   - Check "Add Python to PATH" during installation
2. Copy the `pomponio-labeling` folder to the target machine
3. Double-click `install.bat` (or run `install.ps1` in PowerShell)
4. A desktop shortcut will be created automatically

The installer will:
- Install all Python dependencies
- Import the 136 beef cut SKUs
- Create a desktop shortcut

## Quick Start (Manual)

```bash
# Install dependencies
pip install -r requirements.txt

# Import beef cuts (136 SKUs)
python scripts/import_products.py data/beef_cuts.csv

# Run with mock hardware (testing)
python run.py --mock

# Run with real hardware
python run.py --scale-port COM3 --printer-host 192.168.1.100
```

## Features

- **Package Labeling**: Select product, capture weight, print barcode label, scan to verify
- **Box Management**: Track packages per box, close boxes with QR labels
- **Order Fulfillment**: Assign boxes to orders, print manifests, scan verification at pickup

## Hardware Requirements

| Device | Interface | Protocol |
|--------|-----------|----------|
| USB Scale | Serial (COM port) | 9600 baud, 8N1 |
| Zebra Printer | USB or Network | ZPL |
| Barcode Scanner | Bluetooth HID | Keyboard wedge |

## Project Structure

```
pomponio-labeling/
├── run.py                    # Application entry point
├── requirements.txt          # Python dependencies
├── config.ini.example        # Configuration template
├── PRD.md                    # Product requirements
├── src/
│   ├── config.py             # Configuration management
│   ├── database.py           # SQLite models
│   ├── scale.py              # Scale serial interface
│   ├── printer.py            # Zebra ZPL printing
│   ├── barcode.py            # Barcode/QR generation
│   ├── scanner.py            # Keyboard wedge handling
│   └── ui/
│       ├── app.py            # Main application
│       ├── labeling.py       # Labeling screen
│       ├── boxes.py          # Box management screen
│       ├── orders.py         # Order/pickup screen
│       └── widgets.py        # Touch-optimized widgets
├── scripts/
│   ├── import_products.py    # Import products from CSV
│   ├── backup_db.py          # Database backup/restore
│   └── export_report.py      # Generate reports
├── data/
│   ├── pomponio.db           # SQLite database
│   ├── products_sample.csv   # Sample product data
│   ├── backups/              # Database backups
│   └── reports/              # Exported reports
└── tests/
    ├── test_barcode.py       # Barcode tests (22 tests)
    └── test_database.py      # Database tests (20 tests)
```

## Data Formats

### Package Barcode (UPC-A, 12 digits)

```
[0][5-digit SKU][5-digit weight×100][check digit]
```

Example: SKU 00123, weight 2.45 lbs = `000123002455`

### Box QR Code

```
BOX|YYYYMMDD-SEQ|TOTAL_WEIGHT
SKU|WEIGHT
SKU|WEIGHT
...
```

## Configuration

Copy `config.ini.example` to `config.ini` and customize:

```ini
[hardware]
scale_port = COM3
printer_type = network
printer_host = 192.168.1.100

[application]
window_mode = maximized
touch_target_size = 60
audio_enabled = true
```

## Utility Scripts

```bash
# Import products
python scripts/import_products.py data/products.csv
python scripts/import_products.py --list

# Database backup
python scripts/backup_db.py
python scripts/backup_db.py --list
python scripts/backup_db.py --restore pomponio_20260204_120000.db

# Reports
python scripts/export_report.py daily
python scripts/export_report.py daily 2026-02-04
python scripts/export_report.py inventory
python scripts/export_report.py orders
```

## Development

```bash
# Run all tests (42 tests)
python -m unittest discover tests

# Run specific test module
python -m unittest tests.test_barcode -v
python -m unittest tests.test_database -v
```

## Verification Checkpoints

| Checkpoint | Trigger | Success | Failure |
|------------|---------|---------|---------|
| Label Print | After printing | Green flash, beep | Red flash, error tone |
| Box Close | After QR print | Green flash, beep | Red flash, error tone |
| Pickup | Scanning at pickup | Green check, beep | Red X, error tone |

## Deployment Checklist

### Automated Install
1. Install Python 3.11+ on Windows PC (check "Add Python to PATH")
2. Copy `pomponio-labeling` folder to target machine
3. Double-click `install.bat`
4. Copy `config.ini.example` to `config.ini`, configure hardware
5. Double-click desktop shortcut or `launch.bat`

### Manual Install
1. Install Python 3.11+ on Windows PC
2. Copy application folder to target machine
3. Run `pip install -r requirements.txt`
4. Copy `config.ini.example` to `config.ini`, configure hardware
5. Import product SKU list: `python scripts/import_products.py products.csv`
6. Test with mock hardware: `python run.py --mock`
7. Connect real hardware, update `config.ini`
8. Run: `python run.py`

## Files for Deployment

| File | Purpose |
|------|---------|
| `install.bat` | Windows batch installer (double-click) |
| `install.ps1` | PowerShell installer (alternative) |
| `launch.bat` | Run application (uses config.ini) |
| `config.ini.example` | Configuration template |

## Support

Contact Westco for technical support.
