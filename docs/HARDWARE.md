# Hardware Specification: Pomponio Ranch Labeling Station

**Last Updated:** 2026-02-11
**Status:** Ordered, awaiting delivery

---

## Station Overview

Standalone labeling station for Sinton & Sons meat processing facility. Completely independent from existing LPA machines. Do not connect to or modify any existing equipment.

**Deployment location:** Sinton & Sons processing plant
**Configured at:** Peter's location (pre-deployment testing)

---

## 1. Label Printer

**Model:** Zebra ZP230D (ZP450 replacement)
**Part Number:** ZP23042-D11G0004
**Type:** Direct thermal (no ribbon required)

### Specifications
- Resolution: 203 x 203 DPI
- Print speed: 5 in/sec max
- Max print width: 4.09 inches
- Connectivity: USB 1.0/1.1, Serial (RS-232C), Parallel (IEEE 1284)
- Languages: ZPL II, EPL2
- Media: Direct thermal labels, 1" or 1.5" core, up to 5" OD roll

### Key Notes
- ZPL II native; send raw ZPL commands over USB
- Has serial port (RS-232); ZKDU/ZBI theoretically possible but not planned for v1
- ZP450 driver ecosystem; use ZDesigner v5 or v10 Windows driver
- Calibrate for 4x4 label stock on first use (two-flash feed button mode)
- The ZP230D is marketed as ZP450 replacement; functionally identical

### Software Integration
- Connect via USB; appears as printer in Windows
- Send raw ZPL via Python `socket` or write directly to printer port
- Alternative: Install ZDesigner driver, print via Windows GDI (not recommended for variable data)
- Preferred: Raw ZPL over USB using `pyusb` or direct file write to printer device

---

## 2. Platform Scale

**Model:** Brecknell 6710U
**Part Number:** BN6710U15
**Capacity:** 15 lb
**Readability:** 0.005 lb (0.1 oz)

### Specifications
- Platform: 10" x 10" stainless steel
- Display: 5.5 digit LCD with blue backlight, remote/magnetic mount
- Connectivity: USB (virtual COM port) and RS-232 (9-pin)
- Power: AC adapter included (7-9VDC, 500mA+), can also power via USB
- Tare: Manual button and "Touchless Tare" (optical sensor, wave-of-hand)
- Functions: Check weighing, counting, peak/hold

### Communication Protocol
- USB presents as virtual RS-232 COM port (install driver if needed)
- Baud rate: Configurable (default 9600, 8N1)
- Request weight: Send `W\r` (0x57 0x0D)
- Response format: `<LF>________U<CR><LF>H<CR><ETX>`
  - 8-char weight field (right-justified, space-padded)
  - U = unit indicator (lb, kg, oz)
  - H = status header byte (encodes stability, zero, tare, etc.)
- Continuous output mode also available (configurable in setup menu)
- Over capacity: `_ _ _ _ _ _ _ _`
- Under capacity: `- - - - - - - -`

### Key Notes
- 15 lb capacity covers all individual retail cuts (most beef cuts under 10 lb)
- Will NOT handle primals or subprimals (those can weigh 20-80 lb)
- Touchless tare is useful for food safety (gloved hands)
- Must configure to lb units in setup menu (CONFG > UNITS)
- Scale must be on flat, stable surface; vibration affects readings

### Software Integration
- Open virtual COM port via `pyserial`
- Poll with `W\r` command, parse response
- Check stability bit in H byte before accepting weight
- Implement weight-lock logic: require stable reading for N consecutive polls

---

## 3. Barcode Scanner

**Model:** Zebra DS2208 Standard Range
**Part Number:** DS2208-SR7U2100AZW
**Type:** Handheld corded 2D imager
**Kit includes:** Scanner + shielded USB cable

### Specifications
- Reads: 1D and 2D barcodes (UPC-A, EAN, Code 128, QR, DataMatrix, etc.)
- Interface: USB HID keyboard wedge (default out of box)
- Scan range: Up to 14.5" (standard range)
- Cable: Shielded USB, included in kit

### Key Notes
- HID keyboard wedge mode: scanned barcode appears as keyboard input followed by Enter
- No driver installation required
- For software integration: listen for keyboard input in focused text field, or use raw USB HID
- Keyboard wedge is simplest and most reliable for this application
- Scanner beeps on successful decode

### Software Integration
- Capture scan input via hidden text field with keyboard focus
- Parse UPC-A: extract SKU (digits 2-6) and weight (digits 7-11) from 12-digit barcode
- Use scan event to trigger verification against printed label data
- Timeout: if no scan within N seconds after label print, prompt operator

---

## 4. Mini PC

**Model:** Beelink Mini S12
**Processor:** Intel 12th Gen N95, 4-core, up to 3.4 GHz
**RAM:** 8 GB DDR4
**Storage:** 256 GB SSD
**OS:** Windows 11 Home

### Specifications
- Display output: Dual HDMI (4K UHD)
- Network: Gigabit Ethernet, Dual WiFi 5, Bluetooth 4.2
- USB: Multiple USB-A ports (3.0 and 2.0)
- Form factor: Mini desktop (HTPC size)

### Key Notes
- More than sufficient for Python/CustomTkinter labeling application
- Direct HDMI connection to Angel POS monitor
- WiFi for remote updates (auto-updater checks GitHub releases)
- Install TeamViewer/AnyDesk for emergency remote support
- Set Windows to auto-login, auto-start labeling application on boot
- Disable Windows Update restart prompts during business hours
- Disable sleep/hibernate

### Required Accessories (not yet ordered)
- None; all connectivity is direct

---

## 5. Touchscreen Monitor

**Model:** Angel POS 17-inch Capacitive Touchscreen
**Type:** LED backlit, multi-touch, true flat seamless design
**Interface:** VGA and HDMI video input

### Specifications
- Size: 17 inches
- Touch type: Capacitive (projected capacitive works through nitrile gloves)
- Touch interface: USB (separate from video)
- Video interface: VGA and HDMI
- Design: True flat, seamless bezel (easy to clean, no food trap edges)

### Key Notes
- Two cables to PC: HDMI for video, USB for touch input
- Direct HDMI connection to Beelink S12; no adapter needed
- Capacitive touch through nitrile gloves: test on arrival; if unreliable, adjust touch sensitivity or consider thin gloves
- 17" is larger than originally spec'd 15.6"; more room for product grid UI
- True flat design is ideal for processing environment (wipeable, no crevices)
- Mount or position where it won't get splashed directly

### Software Integration
- Touch input appears as mouse events to Windows; no special driver needed for CustomTkinter
- UI designed with 80px+ touch targets for gloved operation
- Test multi-touch if implementing pinch/zoom (not currently planned)

---

## 6. Test Labels

**Model:** BETCKEY 4" x 4" Direct Thermal Labels
**Compatibility:** Zebra and Rollo printers
**Specifications:** 1 roll, 350 labels, premium adhesive, perforated

### Key Notes
- Third-party compatible labels for development and testing
- 4x4 inch (102mm x 102mm) format
- Direct thermal (no ribbon needed)
- Perforated between labels for tear-off
- These are BLANK labels for testing; preprinted Pomponio rolls ordered separately once layout is finalized
- 1" core assumed; verify compatibility with ZP230D on arrival

---

## Connectivity Summary

| Device | Connection to PC | Port Type |
|--------|-----------------|-----------|
| Zebra ZP230D Printer | USB cable | USB-A |
| Brecknell 6710U Scale | USB cable (virtual COM) | USB-A |
| Zebra DS2208 Scanner | Shielded USB cable (included) | USB-A |
| Angel POS Touchscreen (video) | HDMI cable | HDMI out |
| Angel POS Touchscreen (touch) | USB cable | USB-A |
| **Total USB-A ports needed** | **4** | |

### Port Allocation
The Beelink S12 has multiple USB ports. Verify on arrival that it has at least 4 USB-A ports. If short, use a powered USB hub (not bus-powered; the scale may need reliable power).

---

## Items Still Needed

| Item | Purpose | Priority |
|------|---------|----------|
| Preprinted 4x4 Pomponio label rolls | Production labels (after layout approval) | After testing |
| USB cable for scale (if not included) | Brecknell 6710U to PC | Verify on arrival |
| AC adapter for scale (if not included) | Brecknell 6710U power | Verify on arrival |
