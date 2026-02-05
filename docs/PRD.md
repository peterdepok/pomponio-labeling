# Pomponio Ranch Labeling System
## Product Requirements Document

### Overview

Desktop application for meat processing operations at Pomponio Ranch. Handles package labeling, box tracking, and order fulfillment with USB scale integration and Zebra thermal printer output.

### Problem Statement

Manual meat labeling is error prone, slow, and creates no digital record. The processor needs:
- Accurate weight capture from USB scale
- Consistent labels with barcodes for traceability
- Box level tracking for order fulfillment
- Manifest generation for back office

### Users

**Primary:** Processing floor staff wearing gloves, operating in cold/wet environment
**Secondary:** Back office receiving manifests and managing orders

### Hardware Requirements

| Device | Connection | Protocol |
|--------|------------|----------|
| USB Scale | Serial (COM port) | 9600 baud, continuous weight stream |
| Zebra Printer | Serial or Network | ZPL (Zebra Programming Language) |
| Barcode Scanner | Bluetooth HID | Keyboard wedge mode |

### Core Features

#### 1. Package Labeling

**Flow:**
1. Select product from list (tap or scan SKU)
2. Place package on scale
3. Weight displays and stabilizes
4. Tap "Lock Weight" or press Enter
5. Label prints automatically
6. Package added to current box

**Label Contents:**
- Product name
- Weight (lb)
- Pack date
- Barcode (SKU + weight encoded)
- Pomponio Ranch branding

**Acceptance Criteria:**
- Weight updates in real time from scale
- Weight lock requires stable reading (no fluctuation > 0.01 lb for 500ms)
- Label prints within 1 second of weight lock
- Barcode scannable by standard readers

#### 2. Box Management

**Flow:**
1. Start new box (generates box ID)
2. Add packages via labeling screen
3. View box contents (running total weight, item count)
4. Close box when full
5. Print box label with manifest barcode

**Box Label Contents:**
- Box ID (scannable barcode)
- Total weight
- Item count
- Contents summary
- Date packed

**Acceptance Criteria:**
- Box persists across app restarts
- Box contents viewable at any time
- Box label includes QR code linking to digital manifest

#### 3. Order Fulfillment

**Flow:**
1. Create order with customer name
2. Assign boxes to order
3. Mark order ready for pickup/delivery
4. Generate manifest (PDF or email)

**Manifest Contents:**
- Order number
- Customer name
- List of boxes with contents
- Total weight
- Pack date

**Acceptance Criteria:**
- Manifest emailed to back office when order marked ready
- Manifest includes all box barcodes for verification

### Technical Architecture

```
pomponio-labeling/
├── run.py                 # Entry point
├── config.ini             # Hardware and app settings
├── data/
│   ├── products.csv       # SKU catalog (250 items)
│   └── pomponio.db        # SQLite database
└── src/
    ├── config.py          # Configuration management
    ├── database.py        # SQLite operations
    ├── scale.py           # USB scale communication
    ├── printer.py         # Zebra ZPL generation
    ├── scanner.py         # Barcode scanner handling
    ├── manifest.py        # Manifest generation and email
    ├── resilience.py      # Auto backup, reconnection, crash recovery
    ├── updater.py         # GitHub release auto-updater
    └── ui/
        ├── app_modern.py      # Main application (CustomTkinter)
        ├── labeling_safe.py   # Labeling screen with safety checks
        ├── boxes_modern.py    # Box management screen
        ├── orders_modern.py   # Order fulfillment screen
        ├── setup_wizard.py    # First run configuration
        ├── update_dialog.py   # Update notification UI
        └── theme.py           # Colors, fonts, sizes
```

### UI Requirements

**General:**
- Dark theme (reduces glare in processing environment)
- Minimum 60px touch targets (glove operation)
- High contrast text
- Large weight display (readable from 3 feet)

**Navigation:**
- Three tabs: LABELING, BOXES, ORDERS
- Status indicators for scale and printer connection
- Settings gear icon for configuration

### Data Model

**Package:**
- id (auto)
- sku
- product_name
- weight_lb
- box_id (foreign key)
- labeled_at (timestamp)
- label_barcode

**Box:**
- id (auto)
- box_number (display ID)
- status (open, closed)
- order_id (foreign key, nullable)
- created_at
- closed_at

**Order:**
- id (auto)
- order_number
- customer_name
- status (pending, ready, delivered)
- created_at
- completed_at

### Resilience Requirements

**Auto Backup:**
- Database backed up every 15 minutes
- Backup on app startup and shutdown
- Keep last 10 backups

**Hardware Reconnection:**
- Monitor scale and printer connection every 5 seconds
- Auto reconnect on disconnect (3 attempts, exponential backoff)
- Visual indicator of connection status

**Crash Recovery:**
- Persist current box state
- Restore on app restart

### Remote Update Requirements

**Auto Updater:**
- Check GitHub releases API on startup
- Compare version tags (semver)
- Download and apply updates preserving config and data
- Prompt user before restart

**Update Flow:**
1. Developer pushes code to GitHub
2. Developer creates release with version tag (v1.x.x)
3. App detects new release on next launch
4. User prompted to download and install
5. App restarts with new version

### Product Catalog

250 SKUs across three categories:
- Beef (110 cuts): BEF001 through BEF110
- Pork (90 cuts): POR001 through POR090
- Lamb (50 cuts): LAM001 through LAM050

No pricing in catalog. Pomponio is the processor; customers set their own retail prices.

### Configuration

All hardware settings stored in config.ini:
- Scale port and baud rate
- Printer type (serial/network) and connection details
- Email settings for manifest delivery
- Update check preferences

Setup wizard runs on first launch for guided configuration.

### Build and Distribution

**Development:**
- Python 3.10+
- CustomTkinter for UI
- pyserial for hardware communication
- SQLite for data storage

**Distribution:**
- PyInstaller creates single folder Windows executable
- No installation required (portable)
- Run from USB drive or network share

**GitHub Repository:**
https://github.com/peterdepok/pomponio-labeling

### Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-02 | Initial release with labeling, boxes, orders |

### Open Questions

1. Do we need offline mode with sync when connection restored?
2. Should manifests include photos of packed boxes?
3. Integration with QuickBooks for invoicing?

### Out of Scope (Future)

- Multi-station support (multiple labeling stations)
- Inventory tracking (quantity on hand)
- Customer portal for order status
- Mobile app for delivery verification
