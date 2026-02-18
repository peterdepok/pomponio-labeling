# Pomponio Ranch Labeling System
## Operational Guide for Sinton and Sons

**Version 1.0 | February 2026**
**Prepared by Westco**

---

## Table of Contents

1. System Overview
2. Powering On
3. Daily Workflow
4. Labeling a Package
5. Managing Boxes
6. Scanning and Voiding
7. Closing an Animal
8. Settings Reference
9. Troubleshooting
10. Quick Reference Card

---

## 1. System Overview

### Hardware

| Component | Model | Connection |
|-----------|-------|------------|
| Computer | Beelink Mini S12 | Power adapter |
| Display | 1280x1024 touchscreen | HDMI + USB (touch) |
| Printer | Zebra ZP 230D | USB |
| Scale | Brecknell 6710U | USB |
| Scanner | USB barcode scanner | USB |

The system runs in full-screen kiosk mode. All interaction is through the touchscreen. No mouse or keyboard is required for normal operation.

### Label Stock

Pre-printed 4x4 inch labels with Pomponio Ranch branding. The system prints three dynamic fields onto each label:

- **Product name** (centered, upper area)
- **Barcode** (lower left)
- **Net weight** in pounds and ounces (lower right)

### Barcode Format

Each barcode is 14 digits:

| Positions | Content | Example |
|-----------|---------|---------|
| 1 through 4 | Piece count | 0001 (individual) |
| 5 through 9 | SKU | 00100 |
| 10 through 14 | Weight in hundredths of lb | 03250 (32.50 lb) |

Box labels use the actual piece count (e.g., 0012 for 12 items of that SKU).

---

## 2. Powering On

1. Press the power button on the Beelink Mini S12.
2. Windows will boot and the labeling system will launch automatically.
3. The system kills any stale processes, opens a clean browser session, and connects to the printer and scale.
4. A boot delay of approximately 10 seconds is normal.

### Operator Gate

On every startup, the system requires an operator name before any work can begin.

- **Returning operator:** Tap your name from the recent names list (up to 5 names remembered).
- **New operator:** Tap "Enter New Name," type your name on the on-screen keyboard, and confirm.

Your name is attached to every action in the audit log for traceability.

### If the System Crashes

The watchdog process automatically restarts the application. No action is required. If the system does not recover after 30 seconds, power cycle the Beelink by holding the power button for 5 seconds, then pressing it again.

---

## 3. Daily Workflow

A typical shift follows this sequence:

1. **Power on** the system (or confirm it is already running).
2. **Identify yourself** at the operator gate.
3. **Create or select an animal** on the Animals tab.
4. **Select products and label packages** using the Products and Label tabs.
5. **Close boxes** on the Boxes tab when full.
6. **Close the animal** when all packages are labeled (exports the manifest).
7. **End the shift** by tapping Exit (red button, top right).

### Changing Operators Mid-Shift

Tap your name in the info bar at the bottom left of the screen. Confirm the operator change. The gate modal will reappear for the next operator.

---

## 4. Labeling a Package

### Step by Step

1. Tap the **Animals** tab. Select your animal (or create a new one).
2. Tap the **Products** tab. Select a category (Steaks, Roasts, Ground, etc.) and tap the product.
3. The screen switches to the **Label** tab automatically.
4. Place the item on the scale.
5. The weight reading appears in real time. When the scale is stable (3 identical readings), the weight locks automatically.
6. A barcode is generated, a label is sent to the printer, and a confirmation screen appears.
7. After 2.5 seconds, the screen returns to Products for the next item.

### If the Scale Is Unstable

After 10 seconds of instability, two buttons appear:

- **Lock at X.XX lb**: Accepts the current reading as-is.
- **Manual Entry**: Opens a numeric keyboard to type the weight by hand.

### If the Printer Fails

A large overlay appears with three options:

- **Retry Print**: Sends the same label again. Try this first.
- **Save Without Print**: Records the package data but does not print. Write the label by hand.
- **Cancel**: Aborts the package entirely. Nothing is recorded.

---

## 5. Managing Boxes

Boxes group packages for shipping. Every animal starts with one open box.

### Closing a Box

1. Tap the **Boxes** tab.
2. Tap **Close Box** on the open box.
3. The system generates one summary label per unique SKU in the box.
4. A preview appears. Tap **Print Labels and Close Box**.
5. Labels print. A new empty box is created automatically.

### Reopening a Box

If you need to add more items to a closed box, tap **Reopen Box**. The box returns to open status.

### Reprinting Box Labels

Tap **Reprint Labels** on any closed box. The same labels are regenerated and printed.

---

## 6. Scanning and Voiding

The **Scanner** tab has two functions depending on which barcode you scan.

### Voiding a Package

1. Tap the **Scanner** tab.
2. Scan an individual package barcode (the label on a single item).
3. Package details appear on screen.
4. Tap **Void This Package**.
5. Enter a reason on the keyboard (e.g., "Damaged label," "Wrong weight").
6. Confirm. The package is marked void and excluded from manifests.

### Auditing a Box

1. Scan a box summary barcode (the label printed when a box was closed).
2. The system displays all packages in that box, including voided items.
3. Optionally tap **Email Manifest** to resend the box contents by email.

### Global Scanning

On any tab except Scanner, scanning a barcode opens a popup with package details and a quick-void option. This is useful for spot-checking labels without switching tabs.

---

## 7. Closing an Animal

When all packages for an animal are labeled and boxed:

1. Tap the **Animals** tab.
2. Tap **Close Animal**.
3. The system generates a manifest CSV with all SKUs, quantities, and weights.
4. The CSV is exported to the USB drive (or local storage as a fallback).
5. If email is configured, the manifest is sent automatically.
6. The animal and all its data are purged from memory to free storage.

### Daily Production Report

At the end of a shift, tap **Send Daily Report** on the Animals tab. This generates a comprehensive CSV covering all animals, boxes, and packages processed during the session.

---

## 8. Settings Reference

Tap the **Settings** tab (gear icon) to access configuration. Settings persist across restarts.

### Email and Reports

| Setting | Description |
|---------|-------------|
| Email Recipients | Comma-separated addresses for manifests and reports |
| Auto-email on animal close | Sends manifest automatically when an animal is closed |
| Auto-email daily report | Sends production report when the app exits |
| Send Test Email | Validates the email configuration |

### Printer

| Setting | Description |
|---------|-------------|
| Printer Name | Must match the Windows printer queue name exactly |
| Print Darkness | 1 to 30 (default 15). Higher values produce darker print. |
| Send Test Print | Prints a test label to verify connection |

### Scale

| Setting | Description |
|---------|-------------|
| Scale Mode | Serial (hardware) or Simulated (slider for testing) |
| COM Port | Auto-detect recommended. Manual entry if needed. |
| Baud Rate | 9600 (default for Brecknell 6710U) |
| Stability Delay | 500ms to 5000ms. Increase if the environment has vibration. |
| Max Weight | 1 to 500 lb (default 30 lb). Prevents barcode encoding overflow. |

### System

| Setting | Description |
|---------|-------------|
| Storage Usage | Bar showing how much of the 5 MB limit is used |
| Check for Updates | Pulls latest code from the server (requires internet) |
| Reset Settings | Restores defaults without affecting session data |
| Clear All Session Data | Removes all animals, boxes, and packages. Irreversible. |

### Audit Log

| Setting | Description |
|---------|-------------|
| View Log | Scrollable list of the 100 most recent events |
| Email Log | Sends the full audit log as a CSV attachment |
| Clear Log | Requires passcode **3450**. Clears all entries. |

---

## 9. Troubleshooting

### Printer

| Symptom | Cause | Fix |
|---------|-------|-----|
| Nothing prints, light solid green | ZPL sent but wrong printer name | Settings: verify printer name matches Windows |
| Nothing prints, light flashing green | Printer paused at firmware level | Power cycle the Zebra: unplug, wait 5 seconds, replug |
| Labels printing faintly | Darkness too low or ribbon depleted | Increase darkness in Settings, or replace ribbon |
| Labels printing off-center | Label stock not aligned in guide | Open printer, reseat label roll, close firmly |
| "Print Failed" overlay | USB disconnected or driver issue | Check USB cable. Retry. If persistent, restart system. |

### Scale

| Symptom | Cause | Fix |
|---------|-------|-----|
| "SCALE ERROR" on Label screen | USB disconnected or wrong COM port | Settings: tap Auto-Detect to rescan |
| Weight fluctuates and never locks | Environmental vibration | Increase stability delay in Settings (try 2000ms) |
| Weight reads zero | Nothing on scale or scale not zeroed | Place item, or remove item and wait for zero, then replace |
| Scale not detected during Auto-Detect | Wrong baud rate | Try 9600 (Brecknell default) |

### System

| Symptom | Cause | Fix |
|---------|-------|-----|
| App shows white screen | Build not found or browser cache | Power cycle the Beelink |
| "Storage nearly full" warning | Too many open animals in session | Close completed animals (exports data first) |
| Email says "queued, will retry" | No internet connection | Data is safe locally. Email sends when connection restores. |
| Operator names missing after restart | Normal behavior if profile was cleared | Names are restored from server backup within 2 seconds |

### Emergency Operator Bypass

If the operator gate keyboard is not responding:

1. Tap the title "Operator Identification" five times quickly.
2. The system enters as "Emergency" operator.
3. All functions work normally. Change operator name via the info bar when able.

---

## 10. Quick Reference Card

**Print and cut this section for posting near the workstation.**

---

### LABEL A PACKAGE
Animals > Select animal > Products > Tap product > Place on scale > Label prints automatically

### CLOSE A BOX
Boxes > Close Box > Preview > Print Labels and Close Box

### VOID A PACKAGE
Scanner > Scan label > Void This Package > Enter reason > Confirm

### CLOSE AN ANIMAL
Animals > Close Animal > Manifest exported and emailed

### END SHIFT
Tap red Exit button (top right) > Confirm End Shift

### PRINTER NOT PRINTING
1. Check USB cable
2. Power cycle the Zebra (unplug 5 sec, replug)
3. Verify printer name in Settings

### SCALE NOT READING
1. Settings > Scale > Auto-Detect
2. If still failing: use Manual Entry on the Label screen

### PASSCODES
- Clear Audit Log: **3450**

---

**Support Contact**

For technical issues beyond this guide, contact Westco.

---

*Pomponio Ranch Labeling System v1.0*
*Built by Westco for Sinton and Sons*
*February 2026*
