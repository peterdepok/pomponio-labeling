# Product Requirements Document: Pomponio Ranch Labeling System

**Version:** 2.0
**Date:** 2026-02-11
**Author:** Peter DePok
**Status:** Active Development
**Repository:** github.com/peterdepok/pomponio-labeling

---

## 1. Business Context

### Problem
Sinton & Sons cannot win Pomponio Ranch as a customer without a labeling system that produces scannable UPC-A barcodes compatible with Pomponio's Shopify storefront. The existing LPA software at the facility cannot generate the required barcode format. This is the single blocking issue to landing Pomponio, which represents 10 to 15 beef per month.

### Solution
A custom Python desktop application running on a dedicated hardware station that: reads weight from a USB scale, generates weight-embedded UPC-A barcodes using Pomponio SKU codes, prints labels via a Zebra thermal printer, tracks all packages per animal, and generates manifests for back-office reporting.

### Success Criteria
1. Printed labels scan correctly in Pomponio's Shopify system
2. Floor workers can operate the system with gloved hands and minimal training
3. Per-animal manifest generation for Daniel's reporting needs
4. System is independently maintainable (auto-updates from GitHub)

---

## 2. Barcode Specification (Confirmed)

**Format:** UPC-A, 12 digits total

| Position | Width | Content | Example |
|----------|-------|---------|---------|
| Digit 1 | 1 digit | Quantity flag. Always `0`. Shopify interprets 0 as quantity 1. | `0` |
| Digits 2-6 | 5 digits | SKU code from Pomponio price sheet | `00100` |
| Digits 7-11 | 5 digits | Weight in hundredths of a pound (weight x 100) | `00152` |
| Digit 12 | 1 digit | UPC-A check digit (calculated) | `7` |

**Example:** Ribeye Steak Bone-In (SKU 00100), 1.52 lbs = `0 00100 00152 [check]`

### Check Digit Calculation
Standard UPC-A modulo 10 check digit:
1. Sum digits in odd positions (1, 3, 5, 7, 9, 11), multiply by 3
2. Sum digits in even positions (2, 4, 6, 8, 10)
3. Add the two sums
4. Check digit = (10 - (total mod 10)) mod 10

### Weight Encoding Rules
- Weight is always in pounds
- Multiply by 100, round to nearest integer
- Pad to 5 digits with leading zeros
- Maximum encodable weight: 999.99 lbs (5 digits)
- Minimum: 0.01 lbs
- Example: 1.52 lbs = `00152`, 12.5 lbs = `01250`, 0.75 lbs = `00075`

---

## 3. Label Specification

### Physical Label
- **Size:** 4 x 4 inches (102mm x 102mm)
- **Type:** Direct thermal (no ribbon)
- **Stock:** Perforated rolls, 1" core
- **Testing stock:** BETCKEY 4x4 blank labels (350/roll)
- **Production stock:** Preprinted Pomponio rolls (ordered after layout approval)

### Preprinted Elements (on production rolls)
These elements are printed on the label stock by the label vendor:
- Pomponio Ranch branding/logo
- Safe handling instructions
- USDA inspection legend ("bug")
- "Packaged by Sinton & Sons" line
- "Best By" frame/field

### Variable Print Zones (software controlled)
These elements are printed by the Zebra ZP230D at time of packaging:
1. **Product name** (e.g., "Bone-In Ribeye Steak 1.5in Thick")
2. **Net weight** (e.g., "Net Wt: 1.52 lb")
3. **UPC-A barcode** (12-digit barcode with human-readable digits below)
4. **Source line** (e.g., "Sourced from California")

### ZPL Template Strategy
- Design label layout in ZebraDesigner for Developers (free) to get pixel-perfect positioning
- Export ZPL template with variable field placeholders
- Software injects variable data (product name, weight, barcode) into template at print time
- Template stored as `.zpl` file in repo; updatable via GitHub releases

### Print Zone Positions
**TBD:** Exact coordinates depend on preprinted label layout from Daniel's label vendor. For blank test labels, use full 4x4 area:
- Product name: top third
- Net weight: middle area
- Barcode: bottom third, centered
- Source line: below product name or above barcode

---

## 4. SKU Data

### Source
Pomponio Ranch price sheet (PDF, uploaded 2026-02-11). Parsed to CSV at `data/pomponio_skus.csv`.

### Counts
- Beef: 69 SKUs (active for v1)
- Pork: 40 SKUs (inactive, ready for v2)
- Jerky: 6 SKUs (future)
- Boxes/Treats/Merch: various (future)

### Known Data Issues (Require Resolution)

Three duplicate SKU codes exist in the Pomponio price sheet:

| SKU | Product A | Unit A | Product B | Unit B |
|-----|-----------|--------|-----------|--------|
| 00160 | Carne Asada Seasoned | pack | Carne Asada Unseasoned | lb |
| 00190 | Beef Burger Patties Quarter Pound | pack | Kidney Fat | lb |
| 00192 | Burger Patties Chuck & Brisket | pack | Fajita Unseasoned | pack |

**Action required:** Daniel or Pomponio must assign unique SKU codes to the duplicate entries before production use. Software will reject duplicate SKU imports.

### V1 Scope
- Beef SKUs only (69 items)
- Pork and other categories disabled in UI but present in database for future activation

---

## 5. Hardware (Ordered)

See `docs/HARDWARE.md` for full specifications and integration details.

| Component | Model | Key Specs |
|-----------|-------|-----------|
| Label Printer | Zebra ZP230D | ZPL II, USB/Serial/Parallel, 203 DPI, 5 in/sec |
| Platform Scale | Brecknell 6710U (15 lb) | USB virtual COM, 0.005 lb resolution, 10"x10" platform |
| Barcode Scanner | Zebra DS2208 | USB HID keyboard wedge, 1D/2D, corded |
| Mini PC | Beelink Mini S12 | Intel N95, 8GB RAM, 256GB SSD, Win 11 |
| Touchscreen | Angel POS 17" | Capacitive, VGA, true flat seamless |
| Test Labels | BETCKEY 4x4 | Direct thermal, 350/roll, blank |

All hardware connects directly; no adapters required.

---

## 6. Workflow

### 6.1 Package Labeling (primary workflow)

```
IDLE → PRODUCT_SELECTED → WEIGHT_CAPTURED → LABEL_PRINTED → AWAITING_SCAN → VERIFIED
```

1. **IDLE:** Operator sees product grid on touchscreen. Categories: Steaks, Roasts, Ground, Offal/Specialty, Bones, Sausage/Processed.
2. **PRODUCT_SELECTED:** Operator taps product button (e.g., "Bone-In Ribeye"). Product name and SKU displayed on screen.
3. **WEIGHT_CAPTURED:** Operator places vacuum-sealed cut on scale. Software polls scale, waits for stable reading, locks weight. Weight displayed on screen. Operator confirms or re-weighs.
4. **LABEL_PRINTED:** Software computes barcode (0 + SKU + weight*100 + check digit), builds ZPL with product name, weight, and barcode, sends to printer. Label prints. Operator applies label to package.
5. **AWAITING_SCAN:** Operator scans the barcode on the label they just applied. Software captures scan via keyboard wedge input.
6. **VERIFIED:** Software compares scanned barcode to expected barcode. If match, package is logged to current box and current animal. If mismatch, alert operator. Return to IDLE for next package.

### 6.2 Box Management

- Packages drop into boxes after labeling
- Mixed boxes are acceptable (multiple SKUs per box)
- When operator closes a box:
  - Software prints box label(s): one sticker per SKU type in box
  - Box label format: "[Qty] [Product Name] - [Total Weight]"
  - Example: "10 Ground Beef 70/30 - 10.2 lbs" and "5 NY Strip Boneless - 8.7 lbs"
- Box labels print on same Zebra printer using separate ZPL template

### 6.3 Animal Tracking and Manifest

- Software tracks all packages as they are labeled
- Operator assigns packages to an "animal" (e.g., "Beef #1 - 2/15/2026")
- When animal is complete, operator closes animal
- Software generates manifest spreadsheet:
  - Columns: SKU, Product Name, Quantity, Individual Weights, Total Weight
  - One row per unique product
  - Summary totals at bottom
- Manifest delivery: email to back office and/or save to local file
- Typical volume: 3-4 animals per shift currently, target 7, Pomponio adds 10-15/month

---

## 7. User Interface Requirements

### General
- Framework: Python + CustomTkinter
- Theme: Dark theme (reduce glare in processing environment)
- Touch targets: Minimum 80px height for all interactive elements
- Font sizes: Minimum 16pt for labels, 24pt for primary information
- Glove-compatible: All interactions via tap; no drag, swipe, or pinch required

### Product Grid Screen
- Category tabs along top (Steaks, Roasts, Ground, etc.)
- Product buttons in grid layout, 3-4 columns depending on screen width
- Each button shows: product name (2 lines max), SKU code small
- Category color coding (e.g., steaks = red accent, roasts = brown, ground = gray)
- Search/filter option for finding products quickly

### Labeling Screen (primary workflow)
- Top: Current product name and SKU (large text)
- Middle: Weight display (very large, 48pt+), scale status indicator
- Bottom: Action buttons (Print Label, Re-weigh, Cancel)
- Status bar: Current box, packages in box, current animal
- Workflow state indicator: clear visual showing current step

### Box Management Screen
- List of open boxes with package counts
- Close box button with confirmation
- Box label preview before printing

### Manifest/Reporting Screen
- List of active animals
- Close animal button generates manifest
- View/email/save manifest options
- Historical manifest lookup

### Settings/Setup
- Hardware configuration (COM port for scale, printer selection)
- WiFi/network settings
- Auto-updater controls
- SKU data import

---

## 8. Software Architecture

### Technology Stack
- Language: Python 3.11+
- UI: CustomTkinter
- Database: SQLite (local, single file)
- Printer: Raw ZPL via USB (pyusb or direct device write)
- Scale: pyserial over virtual COM port
- Scanner: Keyboard wedge (standard input capture)
- Packaging: PyInstaller (single directory, Windows exe)
- Updates: GitHub Releases API (auto-check on launch)

### Module Structure
```
src/
  database.py       # SQLite CRUD: products, packages, boxes, animals, scan_log
  barcode.py        # UPC-A generation: SKU + weight encoding + check digit
  scale.py          # Brecknell 6710U serial communication, weight polling, stability
  printer.py        # ZPL template loading, variable injection, print dispatch
  scanner.py        # Keyboard wedge input capture, barcode parsing
  config.py         # Configuration management (config.ini)
  manifest.py       # Spreadsheet generation (openpyxl), email delivery
  updater.py        # GitHub release checking, download, self-update
  safety.py         # Workflow state machine, validators, operation locks
  ui/
    app.py          # Main application, tab navigation
    labeling.py     # Primary labeling workflow screen
    products.py     # Product grid with category tabs
    boxes.py        # Box management screen
    animals.py      # Animal tracking and manifest screen
    settings.py     # Hardware configuration and setup
    theme.py        # Dark theme, colors, fonts
    widgets.py      # Reusable touch-optimized components
data/
  pomponio_skus.csv # Product SKU database (source of truth)
  templates/
    package_label.zpl   # ZPL template for package labels
    box_label.zpl       # ZPL template for box labels
docs/
  PRD.md            # This document
  HARDWARE.md       # Hardware specifications
tests/
  test_barcode.py   # Barcode generation and check digit tests
  test_scale.py     # Scale communication protocol tests
  test_printer.py   # ZPL template and print tests
  test_database.py  # Database CRUD tests
  test_workflow.py  # Workflow state machine tests
```

### Database Schema
```sql
CREATE TABLE products (
  id INTEGER PRIMARY KEY,
  sku TEXT UNIQUE NOT NULL,      -- 5-digit Pomponio SKU
  name TEXT NOT NULL,
  category TEXT NOT NULL,         -- Beef, Pork, etc.
  unit TEXT NOT NULL,             -- lb or pack
  active BOOLEAN DEFAULT 1
);

CREATE TABLE animals (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,             -- e.g., "Beef #1 - 2/15/2026"
  species TEXT DEFAULT 'Beef',
  started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  closed_at TIMESTAMP,
  manifest_path TEXT              -- path to generated spreadsheet
);

CREATE TABLE boxes (
  id INTEGER PRIMARY KEY,
  animal_id INTEGER REFERENCES animals(id),
  box_number INTEGER NOT NULL,
  opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  closed_at TIMESTAMP
);

CREATE TABLE packages (
  id INTEGER PRIMARY KEY,
  product_id INTEGER REFERENCES products(id),
  animal_id INTEGER REFERENCES animals(id),
  box_id INTEGER REFERENCES boxes(id),
  weight_lb REAL NOT NULL,
  barcode TEXT NOT NULL,           -- full 12-digit UPC-A
  label_printed_at TIMESTAMP,
  scan_verified_at TIMESTAMP,
  scan_matched BOOLEAN
);

CREATE TABLE scan_log (
  id INTEGER PRIMARY KEY,
  scanned_barcode TEXT NOT NULL,
  expected_barcode TEXT,
  matched BOOLEAN,
  scanned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 9. Scale Communication Detail

### Brecknell 6710U Protocol

**Connection:** USB virtual COM port via pyserial
**Settings:** 9600 baud, 8 data bits, no parity, 1 stop bit (8N1)

**Request weight:**
```
Send: W\r  (0x57 0x0D)
```

**Response format:**
```
<LF>[8-char weight field][unit]<CR><LF>[H status byte]<CR><ETX>
```

**Weight field:** Right-justified, space-padded, includes decimal point
**Unit field:** `lb`, `kg`, `oz`, etc.
**H byte:** Bit field encoding stability, zero, tare, motion, etc.

**Stability detection:** Check H byte bit for "stable/no motion" before accepting weight. Do not accept weight while motion bit is set.

**Polling strategy:**
1. Poll every 200ms
2. Display current weight in real-time on screen
3. When weight is stable for 3 consecutive readings (600ms), auto-lock
4. Operator can manually confirm or re-weigh
5. Zero/tare before each new item (or use touchless tare)

---

## 10. Printer Communication Detail

### Zebra ZP230D ZPL Integration

**Connection:** USB; printer appears as Windows device
**Language:** ZPL II

**Approach:** Raw ZPL template with variable substitution

**Example ZPL for 4x4 label (blank stock, test layout):**
```zpl
^XA
^FO50,30^A0N,40,40^FD{product_name}^FS
^FO50,90^A0N,30,30^FDNet Wt: {weight_lb} lb^FS
^FO50,140^A0N,24,24^FDSourced from California^FS
^FO100,200^BY3,2,100
^BCN,100,Y,N,N
^FD{barcode_12}^FS
^XZ
```

Variables injected at print time:
- `{product_name}` - from product grid selection
- `{weight_lb}` - from scale reading (formatted to 2 decimal places)
- `{barcode_12}` - computed 12-digit UPC-A

**Template management:**
- Store ZPL templates in `data/templates/`
- Load template, replace placeholders, send to printer
- Separate templates for package labels and box labels
- Update templates via GitHub releases (auto-updater)

---

## 11. Deployment

### Pre-Deployment (at Peter's location)
1. Unbox and connect all hardware
2. Install Windows drivers (Zebra ZDesigner, Brecknell COM port)
3. Install Python, dependencies, build exe
4. Configure hardware connections in setup wizard
5. Load Pomponio SKU data
6. Test end-to-end: select product, weigh, print, scan, verify
7. Print sample labels on blank stock
8. Scan test labels in Shopify (Jensen's test environment)

### Production Deployment (at Sinton plant)
1. Deliver pre-configured station (PC, monitor, printer, scale, scanner)
2. Set up on dedicated table away from LPA machines
3. Connect power and load label stock
4. Run calibration (printer label calibration, scale zero)
5. Train operators: 30-minute walkthrough of labeling workflow
6. First animal: supervised run with Peter present
7. Verify manifests generate correctly

### Maintenance
- Auto-updater checks GitHub on launch
- TeamViewer/AnyDesk for emergency remote support
- Config.ini and database survive updates
- Backup database daily (automated to local folder)

---

## 12. Timeline

| Date | Milestone | Owner |
|------|-----------|-------|
| Feb 11 | Hardware ordered. PRD and hardware spec finalized. | Peter |
| Feb 11 | Send duplicate SKU conflicts to Daniel for resolution. | Peter |
| Feb 12-13 | Get label photos, label layout spec from Daniel. | Peter/Daniel |
| Feb 13-14 | Hardware arrives. Configure and test at home. | Peter |
| Feb 15-16 | Build final exe. Print samples. Scan-test with Shopify. | Peter |
| Feb 17 | Ship sample labels to Pomponio for approval. | Daniel |
| Feb 18-19 | Pomponio confirms labels scan correctly. | Pomponio |
| Feb 20 | Deploy to plant. Train floor staff. | Peter |

---

## 13. Open Questions

| # | Question | Owner | Status |
|---|----------|-------|--------|
| 1 | Photos of Leppies labels showing exact barcode layout | Daniel | Pending |
| 2 | Preprinted label layout: variable print zone positions (measurements from edges) | Daniel/vendor | Pending |
| 3 | Resolution for 3 duplicate SKUs (00160, 00190, 00192) | Daniel/Pomponio | Pending |
| 4 | Shopify test environment for barcode scan verification | Jensen/Daniel | Pending |
| 5 | How many boxes per beef animal typically? | Daniel | Pending |
| 6 | Error handling: how to handle mislabeled packages? Reprint? Void? | Daniel | Pending |
| 7 | Manifest delivery preference: email, print, both? | Daniel | Pending |

---

## 14. Out of Scope (V1)

- Pork, jerky, box, or merch SKUs (beef only)
- Integration with existing LPA system
- Network printing (USB direct only)
- Shopify API integration (barcodes work via standard UPC-A scan)
- Multi-station support (single station only)
- Primal/subprimal weighing (scale capacity is 15 lb)
- Preprinted label ordering (handled separately after layout approval)
