# Product Requirements Document
# Pomponio Ranch Labeling & Inventory System

**Version 1.0 | February 4, 2026**

**Prepared for:** Sinton & Sons Local Meat and Provisions
**Prepared by:** Westco LLC

---

## Overview

Desktop labeling application for Pomponio Ranch meat processing operations. Handles package labeling, box tracking, and order fulfillment with verification checkpoints throughout.

## Technical Stack

- **Language:** Python 3.11+
- **UI Framework:** Tkinter with ttk (touch-optimized)
- **Database:** SQLite
- **Scale:** USB serial, 9600 baud
- **Printer:** Zebra ZPL over USB
- **Scanner:** Bluetooth HID keyboard wedge

## Hardware Requirements

- Windows 10/11 touchscreen PC
- USB scale (serial interface)
- Zebra label printer (ZPL compatible)
- Bluetooth barcode scanner

## UI Requirements

- Minimum 60px touch targets
- Glove-friendly spacing
- High contrast colors
- Large fonts (18pt minimum)
- Audible feedback on scan success/failure

---

## Core Workflows

### 1. Package Labeling

1. Select product from grid (touch)
2. Place package on scale, weight captures automatically
3. Press PRINT to generate and print label
4. Scan printed label to verify
5. Package added to current box

### 2. Box Management

1. System auto-creates box on first package
2. Display running count and total weight
3. When box complete, press CLOSE BOX
4. Print box QR label
5. Scan QR to verify and seal box

### 3. Order Completion (Pickup)

1. Select customer order
2. Generate master manifest
3. Print manifest
4. Scan each box QR at pickup
5. Mark order complete when all boxes scanned

---

## Data Formats

### Package Barcode (UPC-A style, 12 digits)

```
[0][5-digit SKU][5-digit weight×100][check digit]
```

Example: SKU 00123, weight 2.45 lbs → `0001230024505` (check digit calculated)

### Box QR Code

```
BOX|DATE-SEQ|TOTAL_WT
SKU|WT
SKU|WT
...
```

Example:
```
BOX|20260204-001|24.50
00123|2.45
00124|3.20
00125|5.10
```

---

## Verification Checkpoints

| Checkpoint | Trigger | Success | Failure |
|------------|---------|---------|---------|
| Label print | After printing | Green flash, beep | Red flash, error tone |
| Box close | After box QR print | Green flash, beep | Red flash, error tone |
| Pickup | Scanning box at pickup | Green check, beep | Red X, error tone |

---

## Database Schema

### products
- id (INTEGER PRIMARY KEY)
- sku (TEXT UNIQUE, 5 digits)
- name (TEXT)
- category (TEXT)
- price_per_lb (REAL)
- active (INTEGER DEFAULT 1)

### packages
- id (INTEGER PRIMARY KEY)
- product_id (INTEGER FK)
- weight_lbs (REAL)
- barcode (TEXT UNIQUE)
- box_id (INTEGER FK, nullable)
- created_at (DATETIME)
- verified (INTEGER DEFAULT 0)

### boxes
- id (INTEGER PRIMARY KEY)
- box_number (TEXT UNIQUE, format: YYYYMMDD-SEQ)
- total_weight (REAL)
- package_count (INTEGER)
- qr_data (TEXT)
- order_id (INTEGER FK, nullable)
- created_at (DATETIME)
- closed_at (DATETIME, nullable)
- verified (INTEGER DEFAULT 0)

### orders
- id (INTEGER PRIMARY KEY)
- customer_name (TEXT)
- order_date (DATE)
- pickup_date (DATE, nullable)
- status (TEXT: pending, ready, picked_up)
- created_at (DATETIME)
- completed_at (DATETIME, nullable)

### scan_log
- id (INTEGER PRIMARY KEY)
- scan_type (TEXT: package, box, pickup)
- reference_id (INTEGER)
- barcode_data (TEXT)
- success (INTEGER)
- scanned_at (DATETIME)

---

## File Structure

```
pomponio-labeling/
├── PRD.md
├── requirements.txt
├── run.py
├── src/
│   ├── __init__.py
│   ├── database.py      # SQLite models and queries
│   ├── scale.py         # USB scale serial communication
│   ├── printer.py       # Zebra ZPL label generation
│   ├── barcode.py       # Barcode generation and validation
│   ├── scanner.py       # Keyboard wedge input handling
│   └── ui/
│       ├── __init__.py
│       ├── app.py       # Main application window
│       ├── labeling.py  # Package labeling screen
│       ├── boxes.py     # Box management screen
│       ├── orders.py    # Order/pickup screen
│       └── widgets.py   # Touch-optimized custom widgets
├── data/
│   ├── pomponio.db      # SQLite database
│   └── products.csv     # SKU import file
└── tests/
    └── test_barcode.py
```

---

## Implementation Phases

### Phase 1: Core Labeling (Current)
- Database schema
- Product grid UI
- Scale integration
- Barcode generation
- Label printing
- Scan verification

### Phase 2: Box Management
- Box creation and tracking
- QR code generation
- Box close workflow

### Phase 3: Order Fulfillment
- Order creation
- Manifest generation
- Pickup verification
