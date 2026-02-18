# Pomponio Ranch Labeling System
## Complete Operational Guide for Sinton and Sons

**Version 2.0 | February 2026**
**Prepared by Westco**

---

## Table of Contents

1. System Overview and Hardware
2. Credentials and Access
3. Remote Support via RustDesk
4. Powering On and Startup Sequence
5. Operator Identification
6. Navigation and Screen Layout
7. Animals: Creating and Managing
8. Products: Selecting What to Label
9. Labeling: The Core Workflow
10. Boxes: Grouping Packages for Shipping
11. Scanner: Voiding and Auditing
12. Settings: Complete Reference
13. Data, Exports, and Email
14. Audit Log and Compliance
15. Software Updates
16. Troubleshooting: Printer
17. Troubleshooting: Scale
18. Troubleshooting: System and Software
19. Troubleshooting: Network and Email
20. Hardware Specifications and Replacement Parts
21. Label Stock and Barcode Specification
22. Maintenance Schedule
23. Quick Reference Card

---

## 1. System Overview and Hardware

The Pomponio Ranch Labeling System is a self-contained kiosk for weighing, labeling, and tracking meat packages. It runs on a small Windows PC in full-screen mode. All interaction is through the touchscreen. No external mouse or keyboard is required for daily operation.

### What Is Connected

| Component | Model | Port | Purpose |
|-----------|-------|------|---------|
| Computer | Beelink Mini S12 | N/A | Runs the software |
| Touchscreen | Angel POS 17" Capacitive | HDMI + USB | Display and input |
| Label printer | Zebra ZP 230D | USB | Prints package and box labels |
| Platform scale | Brecknell 6710U (15 lb kit) | USB (serial adapter) | Weighs packages |
| Barcode scanner | Zebra DS2208 | USB (shielded cable) | Scans barcodes for voiding and auditing |

### How It Works

The Beelink runs two things simultaneously:

1. **A backend server** (Python/Flask on port 8000) that talks to the printer and scale.
2. **A frontend application** (React, displayed in Chrome kiosk mode) that the operator interacts with.

When the operator selects a product and places it on the scale, the system reads the weight, generates a barcode, sends a ZPL command to the Zebra printer, and records the package. All data is stored locally and can be emailed or exported to CSV.

---

## 2. Credentials and Access

**Store this section securely. Do not post near the workstation.**

### Windows Login

| Field | Value |
|-------|-------|
| User | Labeling Station |
| Password | 3450 |

### Email Account (for sending manifests and reports)

| Field | Value |
|-------|-------|
| Address | Pomponiolabels2026@outlook.com |
| Password | BSGdL-Pc\hy(o]7~2@-b |
| Microsoft account recovery code | HMDYK-QZG4E-TD6CR-Z6NY2-CT4Y4 |
| App password (SMTP) | njclscjycgjedhil |
| Account management | account.live.com |

### Email Delivery Service (Resend API)

The system sends email through the Resend API, not directly through Outlook SMTP. The API token is configured in the server and does not need to be entered by the operator. If the token needs to be regenerated or replaced, contact Peter at Westco.

### Application Passcode

| Purpose | Code |
|---------|------|
| Clear audit log | 3450 |

---

## 3. Remote Support via RustDesk

RustDesk is installed on the Beelink for remote troubleshooting. It allows a support person to see and control the screen from another computer.

### Connection Details

| Field | Value |
|-------|-------|
| Software | RustDesk |
| Device ID | 369 522 049 |
| Password | 3450Riverside! |
| PIN | 3450 |

### How to Allow Remote Access

1. RustDesk runs automatically in the background. No action is needed from the operator.
2. The support person enters the Device ID and password on their end.
3. A notification may appear on the Beelink screen. The operator can accept or it will auto-connect.
4. Remote access works while the labeling app is running. The support person can see and interact with everything the operator sees.

### When to Use Remote Support

- Software errors that are not resolved by the troubleshooting section of this guide.
- Settings that need to be changed by a technician.
- Software updates that fail through the built-in update mechanism.

---

## 4. Powering On and Startup Sequence

### Normal Startup

1. Press the power button on the Beelink Mini S12 (small button on the top or front of the unit).
2. Windows boots. The labeling system launches automatically via a startup shortcut.
3. There is a 10-second delay after Windows loads to allow all USB devices to initialize.
4. The system performs the following cleanup before launching:
   - Kills any leftover Chrome or Python processes from a previous session.
   - Kills any process occupying port 8000.
   - Deletes the Chrome browser profile (ensures a clean session every time).
   - Rotates the log file if it exceeds 10 MB.
5. The Flask server starts and waits for the scale and printer to connect.
6. Chrome opens in kiosk mode (full screen, no address bar, no tabs).
7. The operator gate modal appears, requesting an operator name.

**Total startup time: approximately 20 to 40 seconds from power button to operator gate.**

### What the Watchdog Does

The startup script (`start_kiosk.bat`) is a watchdog. If the application crashes or exits unexpectedly, the watchdog restarts it automatically. This cycle repeats up to 10 times before the watchdog gives up (to prevent infinite loops if there is a persistent error).

The only way to stop the watchdog intentionally is to use the **Exit** button inside the application, which sends a special exit code (42) that tells the watchdog to stop.

### Cold Start After Power Loss

If the Beelink loses power unexpectedly (power outage, cord pulled), the system recovers on next boot:

1. Windows starts normally.
2. The labeling app launches via the startup shortcut.
3. Settings are restored from the server-side backup file (`exports/settings.json`).
4. Operator names, email recipients, printer name, scale settings, and print darkness are all preserved.
5. **Session data (animals, boxes, packages) from the previous session will be lost** if the operator did not close animals before the power loss. The data only persists in the browser, which is cleared on every startup.

**Best practice: Close each animal as soon as labeling is complete.** This exports the manifest to disk and email, ensuring data survives any failure.

---

## 5. Operator Identification

Every time the app starts, it displays a full-screen modal that blocks all interaction until an operator identifies themselves.

### Selecting Your Name

- Up to 5 recent operator names are shown as large buttons.
- Tap your name to proceed.
- Names are stored on the server and persist across restarts and power cycles.

### Entering a New Name

1. Tap **Enter New Name**.
2. An on-screen QWERTY keyboard appears.
3. Type your name and tap **Confirm**.
4. Your name is added to the recent list (pushing out the oldest if there are already 5).

### Changing Operators During a Shift

1. Look at the **info bar** at the very bottom of the screen.
2. Tap the operator name displayed there.
3. A confirmation dialog appears: "Log out [current name]?"
4. Confirm. The operator gate reappears.
5. The new operator selects or enters their name.
6. Both the logout and the new login are recorded in the audit log.

### Emergency Bypass

If the on-screen keyboard is not responding or the touchscreen has an issue:

1. Tap the title text "Operator Identification" five times in rapid succession (within 2 seconds).
2. The system logs in as "Emergency" operator.
3. All functions work normally.
4. Change the operator name through the info bar as soon as the issue is resolved.

---

## 6. Navigation and Screen Layout

### Tab Bar (Top of Screen)

Six colored tabs across the top, plus a red Exit button on the far right:

| Tab | Color | Purpose |
|-----|-------|---------|
| Animals | Purple | Create and manage animals |
| Products | Red | Browse and select products to label |
| Label | Blue | Weigh and print labels (primary workflow) |
| Boxes | Green | Group packages, print box summary labels |
| Scanner | Orange | Void packages, audit boxes by scanning barcodes |
| Settings | Gray | Configure printer, scale, email, view audit log |
| Exit | Red | End shift and shut down |

The active tab is highlighted. Tap any tab to switch.

### Info Bar (Bottom of Screen)

A persistent bar showing:

- Current animal name
- Current box number
- Total package count
- Current operator name (tappable to change)

This bar is always visible regardless of which tab is active.

---

## 7. Animals: Creating and Managing

An "animal" in this system represents one carcass being processed. All packages and boxes are organized under an animal.

### Creating a New Animal

1. Tap the **Animals** tab.
2. Tap **New Animal**.
3. Two options:
   - **Scan**: Use the barcode scanner to scan an animal ID tag. The scanned value becomes the animal name.
   - **Type**: Tap "Enter Name," type on the on-screen keyboard, confirm.
4. The system creates the animal with one empty box and switches to the Products tab.

A default name is suggested in the format "Beef #1 - 02/18/2026" but can be overridden.

### Selecting an Existing Animal

If multiple animals exist in the session, tap the one you want to work on. The selected animal is highlighted with a cyan border. All subsequent labeling and boxing applies to this animal.

### Closing an Animal

Closing an animal is how data leaves the system. This is the most important operational step.

1. Tap **Close Animal** on the animal card.
2. The system generates a manifest CSV containing every package: SKU, product name, quantity, individual weights, and total weight.
3. The CSV is saved to the USB drive (if one is plugged in) or to the local `exports` folder.
4. If email is configured and auto-email is enabled, the manifest is emailed.
5. All data for that animal (boxes, packages, barcodes) is purged from memory to free storage.

**Once an animal is closed, its data cannot be retrieved from the app.** The manifest CSV and email are the permanent records. Always confirm that the export and email succeeded before moving on.

### Deleting an Animal

The **Delete** option removes an animal without exporting. This is for mistakes only (e.g., created an animal by accident). Data is permanently lost.

### Daily Production Report

At the end of a shift, tap **Send Daily Report** on the Animals tab. This generates a CSV covering all animals processed during the session and emails it (if configured). This is a summary across all animals, not a per-animal manifest.

---

## 8. Products: Selecting What to Label

### Product Categories

Products are organized into six categories, each with its own tab:

| Category | Examples |
|----------|---------|
| Steaks | Ribeye Bone-In, NY Strip Boneless, Filet Mignon, Tri-Tip |
| Roasts | Chuck Roast, Eye of Round, Sirloin Tip, Cross Rib |
| Ground | Burger Patties, Ground Beef 70/30, Stew Meat |
| Offal/Specialty | Liver, Tongue, Heart, Cheeks, Sweetbreads |
| Bones | Marrow Bones, Stock Bones, Shank, Tendon |
| Sausage/Processed | Chorizo, Hot Dogs, Bacon, Summer Sausage |

There are 71 active SKUs in total.

### Selecting a Product

1. Tap the **Products** tab.
2. Tap a category tab (or use **Search** to type a product name).
3. Tap the product button. Each button shows the product name and SKU.
4. The screen switches to the **Label** tab automatically with the product pre-loaded.

### Searching for a Product

1. Tap the **Search** tab within the Products screen.
2. An on-screen keyboard appears.
3. Type part of the product name. Results filter in real time.
4. Tap the matching product to select it.

---

## 9. Labeling: The Core Workflow

This is the primary function of the system. The flow is: select product, weigh, print, confirm.

### Detailed Step-by-Step

1. **Product appears at top of Label screen** with name and SKU.
2. **Place the item on the scale.** The weight reading updates every 200 milliseconds.
3. **Wait for stability.** The system requires 3 identical consecutive readings before locking the weight. A progress indicator shows stability status.
4. **Weight locks automatically.** The display shows the locked weight in large text.
5. **Barcode is generated.** Format: 0001 + 5-digit SKU + 5-digit weight (hundredths of lb).
6. **Label is sent to the Zebra printer.** A "Sending to printer..." animation plays.
7. **Success confirmation.** A green panel displays the label preview, barcode digits, and a checkmark.
8. **Auto-return.** After 2.5 seconds, the screen returns to the Products tab for the next item.
9. **Package is recorded.** The data is stored locally and included in the animal's manifest.

### Stability Delay

The default stability delay is 1000 ms (1 second). This means the scale reading must remain constant for 1 second before the weight locks. If the work environment has vibration (nearby machinery, foot traffic), increase this in Settings to 2000 ms or higher.

### Manual Weight Override

If the scale cannot stabilize after 10 seconds (and the weight reading is greater than zero), two buttons appear:

- **Lock at X.XX lb**: Accepts whatever the scale is currently showing.
- **Manual Entry**: Opens a numeric keyboard. Type the weight (e.g., "1.52") and confirm.

Both options are logged in the audit trail so they can be reviewed later.

### Print Failure

If the label fails to print, a large overlay covers the screen with three options:

| Button | What It Does |
|--------|-------------|
| Retry Print | Sends the exact same ZPL command again. Try this first. Most failures are transient. |
| Save Without Print | Records the package data but skips printing. Use this if the printer is down and you need to keep working. Write the label by hand. |
| Cancel | Aborts the package entirely. Nothing is recorded. The product and weight are discarded. |

The failure reason is displayed on screen and logged. Common causes: USB cable disconnected, printer out of labels, printer paused.

### Speed Tracking

The system tracks labeling speed. If you label 4 or more packages within 60 seconds, a brief celebration message appears. This is motivational only and does not affect operation. It auto-dismisses when you switch tabs.

---

## 10. Boxes: Grouping Packages for Shipping

Every animal starts with one open box. Packages are automatically added to the current open box as they are labeled.

### Box Status

- **Open (green stripe)**: Accepting packages. Only one box can be open at a time per animal.
- **Closed (gray stripe)**: Sealed. Summary labels have been printed. Can be reopened or reprinted.

### Viewing Box Contents

Each box card shows:
- Box number
- Package count and total weight
- Breakdown by SKU (e.g., "3x Ribeye Bone-In (4.2 lb)")

### Closing a Box

1. Tap the **Boxes** tab.
2. Tap **Close Box** on the open box.
3. If the box is empty, it closes immediately with no labels.
4. If the box has packages:
   - The system generates one summary label per unique SKU in the box.
   - Each label shows: "[count]x [product name]", the total weight for that SKU, and a barcode encoding the count, SKU, and total weight.
   - A preview screen appears showing all labels.
5. Tap **Print Labels and Close Box**.
6. Labels print.
7. A new empty box is automatically created for the animal.

### Reopening a Box

Tap **Reopen Box** on a closed box. The box returns to open status and can receive additional packages. The previously printed summary labels are now outdated; reprint after adding items and re-closing.

### Reprinting Box Labels

Tap **Reprint Labels** on any closed box. The system regenerates the summary labels from current data and sends them to the printer. This is useful if a label was damaged or if you need duplicates.

### Creating Additional Boxes Manually

Tap **New Box** at the top of the Boxes screen. This creates an empty box without closing the current one. Typically not needed, since closing a box auto-creates a new one.

---

## 11. Scanner: Voiding and Auditing

The **Scanner** tab uses the Zebra DS2208 barcode scanner (or any USB barcode scanner that emulates keyboard input).

### How Barcode Scanning Works

USB barcode scanners send digits rapidly followed by Enter, mimicking keyboard input. The system distinguishes scanner input from human typing by measuring the speed between keystrokes (scanner: under 80ms per character; human: much slower).

**Minimum scan length: 14 digits** (matching the barcode format).

### Voiding a Package

Use this when a package label is wrong, damaged, or the package needs to be removed from the manifest.

1. Tap the **Scanner** tab.
2. Scan the barcode on the individual package label.
3. The system looks up the package and displays its details: product name, SKU, weight, animal, box.
4. Tap **Void This Package**.
5. An on-screen keyboard appears. Enter a reason for voiding.
6. Tap **Confirm**.
7. The package is marked as void. It will not appear in future manifests. The void reason and operator name are recorded in the audit log.

**Voiding is reversible only by re-labeling.** A voided package still exists in the system's records for audit purposes, but it is excluded from weight totals and manifests.

### Auditing a Box

Use this to verify the contents of a closed box without opening it.

1. Scan the barcode on a box summary label.
2. The system decodes the SKU and weight from the barcode, then finds the matching box (using SKU match and weight within a tolerance of 0.5 lb).
3. A detail panel appears showing:
   - Animal name
   - Box number
   - All packages (including voided ones, marked as such)
   - Total weight
4. Optionally tap **Email Manifest** to resend the box contents by email.

### Global Scan (Available on All Tabs)

If you scan a barcode while on any tab other than Scanner, a popup appears with package details and a quick-void option. This is useful for spot-checking a label without navigating away from your current workflow. Dismiss the popup by tapping outside it.

---

## 12. Settings: Complete Reference

Tap the **Settings** tab to access all configuration. Settings are saved to the server and persist across restarts, power cycles, and profile resets.

### Email and Reports Section (Cyan Card)

| Setting | What It Does | Default |
|---------|-------------|---------|
| Email Recipients | Comma-separated email addresses. Manifests and reports are sent here. | Empty (no email) |
| Auto-email manifest on animal close | When ON, the manifest CSV is automatically emailed when you close an animal. | OFF |
| Auto-email daily production report | When ON, a daily summary is emailed when you exit the app. | OFF |
| Send Test Email | Sends a test message to the configured recipients to verify the setup. | N/A |

### Printer Section (Orange Card)

| Setting | What It Does | Default |
|---------|-------------|---------|
| Printer Name | The exact name of the printer as it appears in Windows. Must match exactly. | zebra |
| Print Darkness | Controls how dark the thermal print is. Range: 1 (lightest) to 30 (darkest). | 15 |
| Send Test Print | Sends a test label to the printer. Use after changing cables or settings. | N/A |

**The printer name in the system must match the printer name in Windows exactly.** To check: open Windows Settings > Bluetooth and Devices > Printers and Scanners. The name shown there is what you enter in the app.

### Scale Section (Green Card)

| Setting | What It Does | Default |
|---------|-------------|---------|
| Scale Mode | "Serial" for the real Brecknell scale. "Simulated" for a drag-slider (testing only). | Serial |
| COM Port | The serial port the scale is connected to. Use Auto-Detect. | COM3 |
| Auto-Detect | Scans all COM ports, tests each for a Brecknell response, and sets the port automatically. | N/A |
| Baud Rate | Communication speed. Must match the scale's setting. | 9600 |
| Stability Delay | How long the weight must remain constant before auto-locking. Range: 500ms to 5000ms. | 1000 ms |
| Max Weight | Upper limit for weight entry. Prevents encoding errors in the barcode. | 30 lb |

**Baud rate options:** 9600 (standard for Brecknell 6710U), 19200, 38400, 115200. Only change this if instructed by a technician.

**Stability delay guidance:**
- 500ms: Very fast, for stable environments only.
- 1000ms: Default, suitable for most conditions.
- 2000ms: Moderate vibration (nearby equipment, foot traffic).
- 3000ms+: Heavy vibration or very precise weight requirements.

### System Section (Red Card)

| Setting | What It Does |
|---------|-------------|
| App Version | Read-only. Shows current software version. |
| Storage Usage | Bar chart showing how much of the 5 MB browser storage limit is in use. Green (0-49%), orange (50-79%), red (80%+). |
| Check for Updates | Contacts the GitHub server to see if new code is available. Requires internet. |
| Apply Update | Downloads and installs the update, rebuilds the app, and restarts. Takes 1 to 2 minutes. |
| Reset Settings | Returns all settings to factory defaults. Does NOT delete session data (animals, boxes, packages). |
| Clear All Session Data | Permanently deletes all animals, boxes, and packages from the current session. Settings are not affected. **Irreversible.** |

### Audit Log Section (Purple Card)

| Setting | What It Does |
|---------|-------------|
| Log Viewer | Scrollable list of the 100 most recent audit events, newest first. Shows timestamp, event type, and details. |
| Email Log | Emails the complete audit log as a CSV attachment to a selected recipient. |
| Clear Log | Deletes all audit entries. **Requires passcode 3450.** The clearance itself is logged before the entries are deleted. |

---

## 13. Data, Exports, and Email

### Where Data Lives

| Data Type | Storage Location | Survives Restart? |
|-----------|-----------------|-------------------|
| Settings (printer, scale, email, etc.) | Server file: `exports/settings.json` | Yes |
| Operator names (recent 5) | Server file: `exports/settings.json` | Yes |
| Animals, boxes, packages | Browser localStorage (5 MB limit) | No (cleared on restart) |
| Audit log | Browser localStorage + server backup | Partially (server backup retained) |
| Exported manifests | USB drive or local `exports/` folder | Yes |
| Email queue | Server file: `data/email_queue.json` | Yes |

### Export Flow When Closing an Animal

1. Manifest CSV is generated in memory.
2. CSV is sent to the Flask server via POST request.
3. Server writes the CSV to the `exports/` folder (or USB drive if mounted).
4. If email is enabled, the CSV is queued for email delivery.
5. If internet is available, the email sends immediately.
6. If internet is unavailable, the email is queued and retried automatically every 5 minutes. The queue holds up to 100 emails and retains them for 7 days.

### CSV File Format

**Animal Manifest:**
Filename: `manifest_[animal_name]_[timestamp].csv`
Columns: SKU, Product Name, Quantity, Individual Weights, Total Weight

**Daily Production Report:**
Filename: `daily_production_[date].csv`
Covers all animals, boxes, and packages from the session.

**Audit Log:**
Filename: `audit_log_[date].csv`
Columns: Timestamp, Event Type, Payload (JSON)

### Email Delivery

Email is sent through the Resend API (a cloud email delivery service). The API token is embedded in the server configuration. If emails stop working:

1. Check internet connectivity (Settings shows "Online" or "Offline" indicator).
2. If online but emails are failing, the API token may have expired. Contact Peter at Westco.
3. Queued emails will send automatically when connectivity is restored.

---

## 14. Audit Log and Compliance

Every significant action in the system is recorded with a timestamp, the operator name, and relevant details. This creates an auditable trail of all labeling activity.

### Events Tracked

| Event | When It Fires |
|-------|--------------|
| operator_shift_started | Operator logs in at gate |
| operator_changed | Mid-shift operator change |
| product_selected | Operator taps a product |
| weight_captured | Scale reading locks |
| weight_override_forced | Operator uses "Lock at" button |
| weight_manual_entry | Operator types weight manually |
| label_printed | Label successfully sent to printer |
| print_failed | Printer returned an error |
| print_retry | Operator tapped Retry |
| print_skipped_save | Operator chose Save Without Print |
| package_recorded | Package data stored |
| package_voided | Package marked void with reason |
| box_created | New box opened |
| box_closed | Box closed and labels printed |
| box_reopened | Closed box reopened |
| box_labels_printed | Box summary labels printed |
| box_labels_reprinted | Box labels reprinted |
| animal_created | New animal started |
| animal_selected | Operator switched active animal |
| animal_closed | Animal closed, manifest exported |
| animal_purged | Animal data removed from memory |
| manifest_exported | CSV written to disk |
| manifest_emailed | CSV sent via email |
| daily_report_exported | Daily report CSV generated |
| audit_log_emailed | Audit log sent as email attachment |
| audit_log_cleared | Audit entries deleted (passcode verified) |
| data_cleared | All session data wiped |
| app_exit_initiated | Operator tapped Exit |
| workflow_cancelled | Operator cancelled mid-label |

### Viewing the Audit Log

Settings > Audit Log section. The log viewer shows the 100 most recent entries in reverse chronological order. Each entry displays:

- Timestamp (date and time)
- Event type
- Payload (JSON with details like SKU, barcode, weight, operator)

### Emailing the Audit Log

1. Settings > Audit Log > **Email Log**.
2. Select a recipient from the recent list, or tap "Enter Email" to type one.
3. The complete log is formatted as a CSV and sent as an attachment.

### Clearing the Audit Log

1. Settings > Audit Log > **Clear Log**.
2. A passcode prompt appears. Enter **3450**.
3. All entries are deleted. The clearance event itself is logged before purging.

---

## 15. Software Updates

The system can update itself from the GitHub repository if the Beelink has internet access.

### Checking for Updates

1. Settings > System > **Check for Updates**.
2. The system contacts GitHub and reports how many commits are ahead of the current version.
3. If updates are available, a button appears: "Update Available (X commits)."

### Applying an Update

1. Tap the update button.
2. A confirmation dialog appears with a summary.
3. Confirm. The system:
   - Pulls the latest code from GitHub.
   - Rebuilds the frontend (`npm run build`).
   - Restarts the Flask server.
4. The screen may go white briefly during the restart. This is normal.
5. The app reloads automatically within 60 seconds.

### If an Update Fails

- A "Update May Have Failed" message appears with two buttons: **Reload Now** or **Wait Longer**.
- Try Reload Now first.
- If the app does not recover, power cycle the Beelink. The watchdog will restart the app.
- If the problem persists after a power cycle, use RustDesk for remote support.

---

## 16. Troubleshooting: Printer

### Zebra ZP 230D Indicator Light

| Light Behavior | Meaning |
|----------------|---------|
| Solid green | Ready. Normal operation. |
| Flashing green | Paused or error at firmware level. |
| Off | No power or USB not connected. |

### Problem: Nothing Prints, Light Solid Green

**Cause:** The label was sent but the printer name in the app does not match the Windows printer name.

**Fix:**
1. Go to Settings > Printer.
2. Verify the printer name. It must match Windows exactly (case-sensitive).
3. To check the Windows name: press Ctrl+Esc (if a keyboard is connected), open Settings > Bluetooth and Devices > Printers and Scanners. Note the exact name.
4. Update the name in the app and tap **Send Test Print**.

### Problem: Nothing Prints, Light Flashing Green

**Cause:** The printer is paused at the firmware level. This commonly happens when the USB cable is disconnected and reconnected while the printer is powered on.

**Fix:**
1. Unplug the Zebra's power cable from the back of the printer.
2. Wait 5 seconds.
3. Plug it back in.
4. Wait for the light to turn solid green.
5. Tap **Send Test Print** in Settings to verify.

### Problem: Labels Print Faintly

**Cause:** Print darkness is set too low, or the thermal printhead is dirty.

**Fix:**
1. Go to Settings > Printer > Print Darkness.
2. Increase the value (try 20, then 25).
3. Tap **Send Test Print** to compare.
4. If still faint at darkness 30, clean the printhead with isopropyl alcohol and a lint-free cloth. Let it dry completely before loading labels.

### Problem: Labels Print Off-Center or Misaligned

**Cause:** Label stock is not seated correctly in the label guides.

**Fix:**
1. Open the printer lid.
2. Remove the label roll.
3. Reseat the roll, ensuring the labels feed through the center guides.
4. Close the lid firmly until it clicks.
5. Press the feed button once to advance one label.

### Problem: "Print Failed" Overlay Appears on Screen

**Cause:** USB cable disconnected, driver issue, or printer error.

**Fix:**
1. Tap **Retry Print**. This succeeds most of the time for transient errors.
2. If retry fails, check the USB cable at both ends (printer and Beelink).
3. Power cycle the Zebra (unplug power, wait 5 seconds, replug).
4. If still failing, tap **Save Without Print** to record the package and apply a hand-written label.
5. If the problem persists, restart the Beelink.

### Problem: Printer Prints a Blank Label

**Cause:** Label stock loaded upside down (thermal coating on wrong side), or labels are not thermal-compatible.

**Fix:**
1. The printable side of a thermal label feels slightly smoother and less glossy.
2. Scratch a label with your fingernail. The side that shows a dark mark is the print side.
3. Reload with the print side facing up (toward the printhead when the lid is closed).
4. Use BETCKEY 4x4 labels (102mm x 102mm) for compatibility. Other brands may work but are not tested.

---

## 17. Troubleshooting: Scale

### Brecknell 6710U Reference

- **Capacity:** 15 lb
- **Communication:** Serial over USB (virtual COM port)
- **Default baud rate:** 9600
- **Protocol:** Sends weight data in response to `W\r` command

### Problem: "SCALE ERROR" on Label Screen

**Cause:** The scale is not connected, the COM port is wrong, or the baud rate does not match.

**Fix:**
1. Go to Settings > Scale.
2. Tap **Auto-Detect**. The system scans all COM ports and tests each one.
3. If detected, the COM port is updated automatically. Toast: "Scale found on COMX."
4. If not detected:
   - Verify the USB cable is plugged into both the scale and the Beelink.
   - Ensure the baud rate is set to 9600.
   - Try a different USB port on the Beelink.
   - Restart the Beelink.

### Problem: Weight Fluctuates and Never Locks

**Cause:** Environmental vibration, air currents, or the item is not fully on the platform.

**Fix:**
1. Ensure the item is centered on the scale platform and not touching anything else.
2. Wait for the reading to stabilize. If it does not stabilize within 10 seconds, manual override buttons appear.
3. If fluctuations are persistent, increase the stability delay in Settings (try 2000ms or 3000ms).
4. If the work area has heavy vibration, consider placing the scale on a vibration-dampening pad.

### Problem: Weight Reads Zero with Item on Scale

**Cause:** Scale needs to be zeroed, or the item is too light to register.

**Fix:**
1. Remove the item from the scale.
2. Wait for the scale to read 0.00.
3. Place the item back on.
4. If the scale does not zero on its own, press the zero button on the scale indicator (the small display unit connected to the platform).

### Problem: Scale Shows "Over Capacity"

**Cause:** Item exceeds the 15 lb capacity of the Brecknell 6710U.

**Fix:**
1. Remove the item immediately to avoid damaging the load cell.
2. Weigh the item on a separate scale.
3. Use **Manual Entry** on the Label screen to type the weight.

### Problem: Scale Not Detected During Auto-Detect

**Cause:** USB driver not loaded, cable issue, or port conflict.

**Fix:**
1. Unplug the scale's USB cable, wait 5 seconds, replug.
2. Try a different USB port on the Beelink.
3. Restart the Beelink (the USB driver loads on boot).
4. If still not detected, the USB cable or adapter may need replacement.

---

## 18. Troubleshooting: System and Software

### Problem: App Shows a White Screen

**Cause:** The frontend build is missing or the browser is showing a cached error page.

**Fix:**
1. Wait 15 seconds. The watchdog may restart the app automatically.
2. If it does not recover, power cycle the Beelink.
3. If it still shows a white screen after reboot, connect via RustDesk for remote diagnosis.

### Problem: "Storage Nearly Full" Warning

**Cause:** The browser's 5 MB localStorage limit is approaching capacity. Too many animals, packages, or audit entries are stored.

**Fix:**
1. Go to the **Animals** tab.
2. Close all completed animals. Closing an animal exports the manifest and purges data from memory.
3. If the warning persists, go to Settings > System > **Clear All Session Data** (only if all data has been exported).
4. Consider clearing the audit log if it has grown large (Settings > Audit Log > Clear Log, passcode: 3450).

### Problem: App Freezes or Becomes Unresponsive

**Cause:** Memory limit reached, JavaScript error, or browser hang.

**Fix:**
1. Wait 30 seconds. The watchdog monitors the Flask server and will restart if it detects a failure.
2. If the app does not recover, power cycle the Beelink.
3. On restart, the Chrome profile is deleted, which clears any corrupted state.
4. Settings are preserved (server-side backup), but session data is lost.

### Problem: Operator Names Missing After Restart

**Cause:** This is expected behavior for the first 2 seconds after startup. The operator names are stored on the server and loaded asynchronously.

**Fix:**
1. Wait 2 to 3 seconds after the operator gate appears.
2. The recent names list will populate once the server data is fetched.
3. If names never appear, the `exports/settings.json` file may be corrupted. Reset settings and re-enter operator names manually.

### Problem: Touchscreen Not Responding

**Cause:** USB connection for touch is loose, or the touch driver is not loaded.

**Fix:**
1. Check the USB cable from the touchscreen to the Beelink.
2. Restart the Beelink.
3. If touch still does not work, connect a USB mouse temporarily to navigate.
4. Use RustDesk for remote support if no input devices are functional.

---

## 19. Troubleshooting: Network and Email

### Problem: Email Says "Queued, Will Retry"

**Cause:** The Beelink does not have internet access.

**Fix:**
1. Check the network indicator in Settings. It should show "Online" in green.
2. If offline, check the Ethernet cable or WiFi connection.
3. The Beelink has dual WiFi 5 and Gigabit Ethernet. Wired Ethernet is more reliable in plant environments.
4. Queued emails will send automatically when connectivity is restored. The queue retries every 5 minutes and holds emails for up to 7 days.
5. Data is always saved to disk first (CSV in `exports/` folder), so no data is lost even if email never succeeds.

### Problem: Emails Not Arriving Despite "Online" Status

**Cause:** The Resend API token may be expired, rate-limited, or the recipient address may be invalid.

**Fix:**
1. Go to Settings > Email > **Send Test Email**.
2. If the test email fails, note the error message.
3. If the error mentions "API key" or "unauthorized," contact Peter at Westco. The Resend API token needs to be refreshed.
4. If the error mentions "invalid recipient," verify the email address in Settings.
5. Check the recipient's spam folder. Resend emails may be flagged by some providers.

### Problem: Cannot Check for Updates

**Cause:** No internet connection, or GitHub is unreachable.

**Fix:**
1. Verify internet connectivity (Settings shows "Online").
2. Try again in a few minutes. GitHub may have temporary outages.
3. Updates are not required for daily operation. The system works fully offline.

---

## 20. Hardware Specifications and Replacement Parts

### Beelink Mini S12

| Spec | Value |
|------|-------|
| Processor | Intel 12th Gen N95 (4-core, up to 3.4 GHz) |
| RAM | 8 GB DDR4 |
| Storage | 256 GB SSD |
| OS | Windows 11 Home |
| Display output | Dual HDMI (4K) |
| Network | Gigabit Ethernet, Dual WiFi 5, Bluetooth 4.2 |

### Angel POS Touchscreen

| Spec | Value |
|------|-------|
| Size | 17 inch |
| Resolution | 1280 x 1024 |
| Touch | Capacitive (multi-touch) |
| Design | True flat, seamless |
| Input | VGA video, USB touch |
| Note | Works with gloves if capacitive-compatible gloves are used |

### Zebra ZP 230D Label Printer

| Spec | Value |
|------|-------|
| Print method | Direct thermal |
| Resolution | 203 DPI |
| Max label width | 4.09 inches |
| Connectivity | USB, Serial, Parallel |
| Replacement for | Zebra ZP 450 |
| Driver | ZDesigner or generic ZPL driver |

### Brecknell 6710U Platform Scale

| Spec | Value |
|------|-------|
| Capacity | 15 lb |
| Resolution | 0.005 lb |
| Platform | Stainless steel |
| Communication | Serial via USB adapter |
| Default baud rate | 9600 |
| Protocol | Send `W\r` to receive weight reading |
| Manual | https://www.brecknellscales.com/wp-content/uploads/2022/09/67xx-Serial-Scale_s_en_501145.pdf |

### Zebra DS2208 Barcode Scanner

| Spec | Value |
|------|-------|
| Type | Handheld, standard range, corded |
| Part number | DS2208-SR7U2100AZW |
| Cable | Shielded USB |
| Scan types | 1D and 2D barcodes |
| Interface | USB HID (keyboard emulation) |

### Label Stock

| Spec | Value |
|------|-------|
| Brand | BETCKEY |
| Size | 4 x 4 inches (102 x 102 mm) |
| Type | Direct thermal, pre-printed Pomponio Ranch artwork |
| Printer compatibility | Zebra ZP 230D (and Rollo) |
| Adhesive | Premium adhesive, perforated |
| Roll quantity | 350 labels per roll |

---

## 21. Label Stock and Barcode Specification

### Pre-Printed Label Layout

The 4x4 inch labels come pre-printed with:

- Pomponio Ranch logo (top left)
- Company name and contact info (top right)
- "Keep Refrigerated or Frozen" text
- Safe Handling Instructions box (bottom left)
- USDA establishment stamp (bottom right)
- Website and marketing text

### Dynamic Fields (Printed by the System)

The system prints three fields onto each label:

| Field | Position | Description |
|-------|----------|-------------|
| Product name | Upper center | Up to 2 lines, centered, 45-dot font |
| Barcode | Lower left | Code 128, 14 digits, with interpretation line |
| Net weight | Lower right | "NetWeight" label, decimal pounds, pounds + ounces |

### Barcode Specification

| Property | Value |
|----------|-------|
| Symbology | Code 128 |
| Length | 14 digits |
| Encoding | Auto-selects subset based on data |
| Module width | 2 dots (0.25 mm at 203 DPI) |
| Bar height | 120 dots (15 mm) |
| Interpretation line | Yes (digits printed below bars) |

### Barcode Data Format

| Digit Positions | Field | Description |
|----------------|-------|-------------|
| 1 through 4 | Piece count | 0001 for individual packages. Actual count for box labels (e.g., 0012 for 12 items). |
| 5 through 9 | SKU | 5-digit Pomponio SKU (e.g., 00100 for Ribeye Steak Bone-In) |
| 10 through 14 | Weight | Weight in hundredths of a pound (e.g., 01520 = 15.20 lb) |

**Example barcode for an individual 1.52 lb Ribeye Steak (SKU 00100):**
`00010010000152`

**Example barcode for a box of 12 Filet Mignons (SKU 00103) totaling 9.60 lb:**
`00120010300960`

---

## 22. Maintenance Schedule

### Daily (Start of Shift)

- [ ] Power on the system and verify all devices connect.
- [ ] Send a test print to confirm the Zebra is working.
- [ ] Verify the scale reads zero with nothing on the platform.
- [ ] Check label stock level. Replace the roll if fewer than ~50 labels remain.

### Daily (End of Shift)

- [ ] Close all animals (exports manifests).
- [ ] Send the daily production report (Animals tab > Send Daily Report).
- [ ] Tap **Exit** to end the shift cleanly (stops the watchdog).
- [ ] Optionally power off the Beelink if no overnight processing is planned.

### Weekly

- [ ] Check the storage usage bar in Settings. Should be green.
- [ ] Review the audit log for any unexpected events.
- [ ] Wipe the touchscreen with a damp (not wet) microfiber cloth.
- [ ] Inspect USB cables for wear or loose connections.

### Monthly

- [ ] Clean the Zebra printhead with isopropyl alcohol and a lint-free cloth.
- [ ] Check for software updates (Settings > System > Check for Updates).
- [ ] Verify email delivery is working (Settings > Email > Send Test Email).
- [ ] Back up the `exports/` folder to a USB drive or network share.

### As Needed

- [ ] Replace label stock when the roll runs out.
- [ ] Replace the Zebra thermal printhead if print quality degrades permanently despite cleaning.
- [ ] Contact Westco if the Resend API token expires or if RustDesk access is not working.

---

## 23. Quick Reference Card

**Print and cut this section for posting near the workstation.**

---

### LABEL A PACKAGE

Animals > Select animal > Products > Tap product > Place on scale > Label prints automatically

### CLOSE A BOX

Boxes > Close Box > Preview labels > Print Labels and Close Box

### VOID A PACKAGE

Scanner > Scan package label > Void This Package > Enter reason > Confirm

### CLOSE AN ANIMAL (EXPORTS DATA)

Animals > Close Animal > Manifest saved to disk and emailed

### END SHIFT

Red Exit button (top right) > Confirm End Shift

### PRINTER NOT PRINTING

1. Check USB cable at both ends
2. Power cycle the Zebra (unplug power 5 seconds, replug)
3. Verify printer name in Settings matches Windows
4. Send Test Print from Settings

### SCALE NOT READING

1. Settings > Scale > Auto-Detect
2. Check USB cable
3. Try a different USB port
4. Use Manual Entry on the Label screen as a workaround

### LIGHT FLASHING GREEN ON ZEBRA

Power cycle: unplug power cable, wait 5 seconds, replug

### SYSTEM FROZEN

Wait 30 seconds (watchdog auto-restarts). If not recovered, hold Beelink power button 5 seconds, then press again.

### PASSCODES

- Windows login: **3450**
- Clear audit log: **3450**

### REMOTE SUPPORT

RustDesk ID: **369 522 049** | Password: **3450Riverside!**

---

**Support Contact**

For issues beyond this guide, contact Peter at Westco.
Resend API token replacement and RustDesk access can only be provided by Westco.

---

*Pomponio Ranch Labeling System v2.0*
*Built by Westco for Sinton and Sons*
*February 2026*
