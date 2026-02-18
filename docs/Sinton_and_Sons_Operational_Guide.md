# Pomponio Ranch Labeling System
## Complete Operational Guide for Sinton and Sons

**Version 3.0 | February 2026**
**Prepared by Peter dePOK, Westco**
**Contact: peter@westllc.co**

**Source code repository:** https://github.com/peterdepok/pomponio-labeling.git

All questions, issues, and requests related to this system should be directed to Peter dePOK at **peter@westllc.co**. Peter is the sole person responsible for the design, development, deployment, and ongoing maintenance of this system.

---

## How to Use This Guide

This guide is written so that anyone can follow it, even if you have never used a computer before. Every step is spelled out. Nothing is assumed. If a section tells you to "tap" something, that means touch it with your finger on the screen.

**Read the whole guide once before your first shift.** After that, use the Table of Contents to jump to whatever section you need. The Quick Reference Card at the very end is designed to be printed and posted near the workstation for daily use.

If something goes wrong and you cannot find the answer in this guide, contact **Peter dePOK at peter@westllc.co**.

---

## Table of Contents

1. [System Overview: What This System Is and What It Does](#1-system-overview-what-this-system-is-and-what-it-does)
2. [Hardware: Every Piece of Equipment Explained](#2-hardware-every-piece-of-equipment-explained)
3. [Credentials and Access: Every Password and Login](#3-credentials-and-access-every-password-and-login)
4. [Remote Support via RustDesk](#4-remote-support-via-rustdesk)
5. [Powering On: Step by Step from a Cold Start](#5-powering-on-step-by-step-from-a-cold-start)
6. [What the Watchdog Does and Why It Matters](#6-what-the-watchdog-does-and-why-it-matters)
7. [Operator Identification: Logging In](#7-operator-identification-logging-in)
8. [Navigation: The Six Tabs and the Info Bar](#8-navigation-the-six-tabs-and-the-info-bar)
9. [Animals: Creating, Selecting, Closing, and Deleting](#9-animals-creating-selecting-closing-and-deleting)
10. [Products: Finding and Selecting What to Label](#10-products-finding-and-selecting-what-to-label)
11. [Labeling: The Core Workflow, Step by Step](#11-labeling-the-core-workflow-step-by-step)
12. [Boxes: Grouping Packages for Shipping](#12-boxes-grouping-packages-for-shipping)
13. [Scanner: Voiding Packages and Auditing Boxes](#13-scanner-voiding-packages-and-auditing-boxes)
14. [Settings: Every Option Explained](#14-settings-every-option-explained)
15. [Data, Exports, and Email: Where Everything Goes](#15-data-exports-and-email-where-everything-goes)
16. [Audit Log and Compliance](#16-audit-log-and-compliance)
17. [Software Updates: How to Check and Apply](#17-software-updates-how-to-check-and-apply)
18. [Quick Fixes: Common Bugs and How to Solve Them](#18-quick-fixes-common-bugs-and-how-to-solve-them)
19. [Troubleshooting: Printer Problems](#19-troubleshooting-printer-problems)
20. [Troubleshooting: Scale Problems](#20-troubleshooting-scale-problems)
21. [Troubleshooting: System and Software Problems](#21-troubleshooting-system-and-software-problems)
22. [Troubleshooting: Network and Email Problems](#22-troubleshooting-network-and-email-problems)
23. [Hardware Specifications and Replacement Parts](#23-hardware-specifications-and-replacement-parts)
24. [OEM Instruction Manuals for All Hardware](#24-oem-instruction-manuals-for-all-hardware)
25. [Label Stock and Barcode Specification](#25-label-stock-and-barcode-specification)
26. [Maintenance Schedule](#26-maintenance-schedule)
27. [Quick Reference Card](#27-quick-reference-card)

---

## 1. System Overview: What This System Is and What It Does

The Pomponio Ranch Labeling System is a self-contained workstation for weighing, labeling, and tracking meat packages. It is designed to run without a mouse or keyboard. Everything is done by touching the screen with your finger.

Here is what the system does, in plain terms:

1. You select a product (for example, "Ribeye Steak").
2. You place the meat package on the scale.
3. The system reads the weight automatically.
4. The system prints a label with the product name, weight, and a barcode.
5. You stick the label on the package.
6. The system records everything so you can export a report at the end.

That is the entire job. The rest of this guide explains every detail of how to do it, what to do when something goes wrong, and how to maintain the equipment.

### What Is Running Behind the Scenes

The system is made of two parts that work together:

- **The backend server** is a program called Flask (written in Python) that runs on port 8000. It talks to the printer and the scale. You never see this program directly. It runs in the background.
- **The frontend application** is what you see on the screen. It is a web application (written in React) that runs inside the Chrome web browser in full-screen mode. There is no address bar, no tabs, and no browser buttons. It looks like a standalone app.

When you tap a button on the screen, the frontend sends a request to the backend. The backend does the work (reads the scale, sends data to the printer) and sends the result back to the frontend, which updates the screen.

You do not need to understand any of this to use the system. It is included here so that if something breaks, a technician can understand the architecture.

---

## 2. Hardware: Every Piece of Equipment Explained

There are five physical devices connected together. Each one has a specific job. If any one of them is disconnected or broken, that part of the system will not work.

### The Computer: Beelink Mini S12

This is a small black box about the size of a sandwich. It is the brain of the whole system. It runs Windows 11 and all the labeling software.

- **Where it is:** Usually mounted behind the touchscreen or sitting on the desk nearby.
- **Power button:** Small round button on the top or front of the unit.
- **Connections:** It has USB ports on the front and back. HDMI ports on the back connect to the screen. An Ethernet port on the back connects to the network (optional but recommended).
- **What to know:** If you need to restart the system, this is the box you power cycle. Hold the power button for 5 seconds to force it off, then press it again to turn it back on.

### The Touchscreen: Angel POS 17-Inch Capacitive Monitor

This is the screen you touch to operate the system. It uses two cables:

1. **HDMI cable** (carries the picture from the Beelink to the screen).
2. **USB cable** (carries your finger touches from the screen back to the Beelink).

If the screen shows a picture but does not respond to touch, the USB cable is probably loose. If the screen is completely black, either the HDMI cable is loose, the screen is not powered on, or the Beelink is off.

- **Note about gloves:** This is a capacitive touchscreen. Standard latex or nitrile gloves will NOT work with it. You need special capacitive-compatible gloves, or you need to use bare fingers. Some thick rubber gloves may partially work but will be unreliable.

### The Label Printer: Zebra ZP 230D

This is a grey box that prints labels. It uses direct thermal printing, which means it uses heat to create the image on special label paper. There is no ink, no toner, and no ribbon.

- **Where it is:** Usually on the desk near the workstation.
- **Power:** The power cable plugs into the back. There is no on/off switch. It is on whenever it is plugged in.
- **Status light:** One LED on the front.
  - **Solid green** = ready and working normally.
  - **Flashing green** = paused or has an error. See Troubleshooting section.
  - **Off** = no power or USB not connected.
- **Label loading:** Open the top lid by pressing the release tabs on both sides simultaneously. The label roll sits inside with labels feeding out through the front slot.
- **USB cable:** Connects the printer to one of the USB ports on the Beelink.
- **Feed button:** A small button on the front. Press it once to advance one label. This is useful after loading a new roll to align the labels.

### The Platform Scale: Brecknell 6710U (15 lb capacity)

This is the stainless steel platform you place meat packages on. It has two parts:

1. **The platform** (a flat stainless steel surface, about 10 inches square).
2. **The indicator** (a small display box connected to the platform by a cable). The indicator has buttons for zeroing and displays the weight on its own small screen.

The scale connects to the Beelink via a USB cable (with a serial adapter built in).

- **Capacity:** 15 pounds maximum. Do not put anything heavier than 15 pounds on this scale. It could damage the load cell (the sensor inside).
- **Zeroing:** If the scale does not read 0.00 when empty, press the zero button on the indicator.
- **Important:** The scale must be on a stable, flat surface. If it is on a surface that vibrates (near a compressor, near heavy foot traffic), the weight readings will jump around and the system will have trouble locking the weight.

### The Barcode Scanner: Zebra DS2208

This is a handheld barcode scanner connected to the Beelink by a shielded USB cable. It looks like a small gun. You point it at a barcode and pull the trigger (or it may auto-scan when it sees a barcode, depending on configuration).

- **What it does:** When you scan a barcode, the scanner sends the digits to the Beelink as if someone typed them very fast on a keyboard, then presses Enter.
- **When you use it:** On the Scanner tab, to void packages or audit boxes. You can also scan a barcode from any tab and a popup will appear.
- **The scanner reads 1D and 2D barcodes.** The barcodes on your labels are 1D (Code 128).

### The Label Stock: BETCKEY 4x4 Inch Direct Thermal Labels

These are the labels you load into the Zebra printer. Each label is 4 inches by 4 inches (102mm by 102mm). They come pre-printed with the Pomponio Ranch logo, company information, safe handling instructions, and the USDA stamp.

The system prints three things onto each label:
1. The product name (centered in the middle area)
2. A barcode (lower left area)
3. The net weight (lower right area)

Everything else on the label is pre-printed on the label stock itself.

- **Roll size:** 350 labels per roll.
- **Brand:** BETCKEY. Other brands of 4x4 direct thermal labels may work, but only BETCKEY has been tested and confirmed compatible.
- **Which side is the print side:** The print side feels slightly smoother. If you are unsure, scratch the label with your fingernail. The side that shows a dark mark from the scratch is the print side.

---

## 3. Credentials and Access: Every Password and Login

**IMPORTANT: Store this section securely. Do not post this page near the workstation where visitors can see it. The Quick Reference Card at the end of this guide has a trimmed version suitable for posting.**

### Windows Login

When the Beelink boots up, Windows may ask for a password before the labeling app starts.

| What to Enter | Value |
|---------------|-------|
| User account name | Labeling Station |
| Password | 3450 |

You type this on the Windows login screen using a physical keyboard (if connected) or the Windows on-screen keyboard.

### Email Account

The system has its own email account for sending manifests, reports, and audit logs. You should not need to log into this account directly unless you are troubleshooting email issues.

| What | Value |
|------|-------|
| Email address | Pomponiolabels2026@outlook.com |
| Password | BSGdL-Pc\hy(o]7~2@-b |
| Where to manage it | Go to account.live.com in a web browser |
| Microsoft account recovery code | HMDYK-QZG4E-TD6CR-Z6NY2-CT4Y4 |
| App password (used for SMTP if needed) | njclscjycgjedhil |

### Email Delivery Service (Resend API)

The system does not send email directly through Outlook. Instead, it uses a service called Resend. The API token for Resend is stored inside the server configuration. You do not need to enter it or see it.

**If emails stop working:** Contact Peter dePOK at peter@westllc.co. Only Peter can regenerate the Resend API token.

### Application Passcode

Some actions inside the labeling app require a passcode to prevent accidental data loss:

| Action | Passcode |
|--------|----------|
| Clear the audit log | 3450 |

---

## 4. Remote Support via RustDesk

RustDesk is a program that lets a support person see and control the Beelink screen from another computer over the internet. It is already installed and runs automatically in the background.

### Connection Details

| What | Value |
|------|-------|
| Software | RustDesk |
| Device ID | 369 522 049 |
| Password | 3450Riverside! |
| PIN | 3450 |

### How Remote Support Works

1. You do not need to do anything on your end. RustDesk is always running.
2. The support person (Peter or someone he designates) types the Device ID and password into their copy of RustDesk.
3. A notification may appear on your screen saying someone wants to connect. You can accept it, or it will connect automatically.
4. The support person can now see everything on your screen and move the cursor as if they were standing in front of the machine.
5. The labeling app keeps running normally during remote access. You can continue working.

### When to Use Remote Support

- When something goes wrong and the troubleshooting sections of this guide do not fix it.
- When a setting needs to be changed by a technician.
- When a software update fails.

**To request remote support:** Email peter@westllc.co or contact Peter directly. Tell him the nature of the problem and confirm the Beelink is powered on and connected to the internet.

---

## 5. Powering On: Step by Step from a Cold Start

This section covers what happens when you turn on the system from scratch, such as at the beginning of a shift or after a power outage.

### Step 1: Turn On the Beelink

Find the Beelink Mini S12 (the small black box). Press the power button once. You will see a small blue light come on.

### Step 2: Wait for Windows to Load

The Windows desktop will appear. This takes about 15 to 30 seconds. If Windows asks for a password, type **3450** and press Enter.

### Step 3: The Labeling App Starts Automatically

A script called `start_kiosk.bat` runs automatically when Windows starts. You do not need to click anything. Here is what happens behind the scenes:

1. The script waits 10 seconds to give all USB devices time to connect.
2. It kills any leftover programs from a previous session (old Chrome windows, old Python processes).
3. It kills anything that might be using port 8000 (which the backend server needs).
4. It waits 3 seconds for Windows to fully release all resources.
5. It deletes the Chrome browser profile folder (this ensures a completely clean start every time; do not worry, your settings are saved on the server, not in Chrome).
6. It checks the log file size and rotates it if it is over 10 MB.
7. It starts the backend server (Python/Flask).
8. It opens Chrome in full-screen kiosk mode pointing to the labeling app.

### Step 4: The Operator Gate Appears

After Chrome opens, you will see a full-screen popup asking for your name. This is called the "operator gate." See Section 7 for how to use it.

### Total Time from Power Button to Ready

About 20 to 40 seconds, depending on how fast Windows boots.

### What Happens After a Power Outage

If the Beelink loses power suddenly (power goes out, cord gets pulled), it recovers automatically on the next boot:

1. Windows starts normally.
2. The labeling app launches automatically.
3. **Settings are preserved.** Operator names, email recipients, printer name, scale settings, and print darkness are all saved on the server and survive any restart.
4. **Session data (animals, boxes, packages) from before the power loss will be LOST** if you did not close the animals before the power went out. This data lives only in the browser, and the browser is wiped clean on every startup.

**This is why closing each animal promptly is critical.** When you close an animal, its manifest is exported to disk and emailed. Once exported, the data is safe even if the system loses power.

---

## 6. What the Watchdog Does and Why It Matters

The startup script (`start_kiosk.bat`) is more than just a launcher. It is a **watchdog**. Here is what that means:

If the labeling app crashes, freezes, or exits unexpectedly for any reason, the watchdog automatically restarts it. It does this by:

1. Detecting that the app has exited.
2. Running the full cleanup process (kill old processes, clear the browser profile, release the port).
3. Starting the app fresh.

This restart cycle can happen up to **10 times** before the watchdog gives up. The 10-restart limit prevents an infinite loop if there is a persistent error that keeps crashing the app.

### How to Stop the Watchdog on Purpose

The only correct way to shut down the system is to use the **Exit** button inside the app (the red button in the top right corner of the screen). When you tap Exit and confirm, the app sends a special exit code (42) to the watchdog. The watchdog sees this code and knows it should stop, not restart.

**If you force the Beelink off by holding the power button, the watchdog is killed along with everything else. On the next boot, it starts fresh.**

---

## 7. Operator Identification: Logging In

Every time the app starts, a full-screen popup blocks everything until you identify yourself. This is called the operator gate.

### Picking Your Name from the List

The app remembers the last 5 operator names. They appear as large buttons on the screen.

1. Look at the buttons. If your name is there, tap it.
2. You are now logged in. The popup closes and you can use the system.

### Entering a New Name

If your name is not on the list:

1. Tap the button that says **Enter New Name**.
2. A keyboard appears on the screen. This is an on-screen keyboard, not a physical one.
3. Type your name using the on-screen keys. For example: "Juan" or "Maria S."
4. Tap **Confirm**.
5. Your name is added to the list. If there were already 5 names, the oldest one is removed to make room.

### Changing Operators in the Middle of a Shift

If someone else needs to take over:

1. Look at the very bottom of the screen. There is a thin bar showing information about the current session.
2. Find your name in that bar. It is on the right side.
3. Tap your name.
4. A popup asks: "Log out [your name]?"
5. Tap **Confirm**.
6. The operator gate appears again.
7. The new person taps their name or enters a new one.
8. Both the logout and the new login are recorded in the audit log.

### Emergency Bypass (If the Keyboard Is Not Working)

If the on-screen keyboard is broken or the touchscreen is partially unresponsive:

1. Tap the words "Operator Identification" at the top of the popup. Tap it **five times quickly** (all five taps must happen within 2 seconds).
2. The system logs you in as "Emergency" operator.
3. Everything works normally.
4. Change the operator name through the info bar (bottom of screen) as soon as the issue is fixed.

---

## 8. Navigation: The Six Tabs and the Info Bar

### The Tab Bar (Top of Screen)

There are six colored tabs across the top of the screen. Each tab is a different section of the app. On the far right is a red Exit button.

| Tab | Color | What It Does |
|-----|-------|-------------|
| Animals | Purple | Create and manage animals (carcasses being processed) |
| Products | Red | Browse and pick the product you want to label |
| Label | Blue | Weigh the package and print the label (this is the main work screen) |
| Boxes | Green | Group packages into boxes and print box summary labels |
| Scanner | Orange | Scan barcodes to void packages or check box contents |
| Settings | Gray | Change printer settings, scale settings, email settings, view the audit log |
| Exit | Red | End your shift and shut down the system |

**To switch between tabs:** Tap the tab you want. The active tab is highlighted so you know which one you are on.

### The Info Bar (Bottom of Screen)

A thin bar at the very bottom of the screen is always visible no matter which tab you are on. It shows:

- The name of the current animal
- The current box number
- The total number of packages you have labeled
- Your operator name (tappable; tap it to change operators)

---

## 9. Animals: Creating, Selecting, Closing, and Deleting

An "animal" in this system represents one carcass being processed. Every package you label belongs to an animal. Every box belongs to an animal.

### Creating a New Animal

1. Tap the **Animals** tab.
2. Tap the **New Animal** button.
3. You have two options:
   - **Scan:** Use the barcode scanner to scan an animal ID tag. The scanned value becomes the animal name.
   - **Type:** Tap "Enter Name." An on-screen keyboard appears. Type the name (for example, "Beef 47" or "Wagyu 12"). Tap **Confirm**.
4. The system creates the animal with one empty box.
5. The screen automatically switches to the **Products** tab so you can start labeling.

A default name is suggested in the format "Beef #1 - 02/18/2026" but you can change it to whatever you want.

### Selecting an Existing Animal

If you have more than one animal in the system and you want to switch between them:

1. Tap the **Animals** tab.
2. You will see a card for each animal.
3. Tap the card for the animal you want to work on. It will be highlighted with a cyan (light blue) border.
4. All labeling and boxing from now on will go to this animal.

### Closing an Animal (This Is the Most Important Step)

**Closing an animal is how data leaves the system.** When you close an animal:

1. Tap the **Animals** tab.
2. Find the animal card and tap **Close Animal**.
3. A confirmation popup appears. Tap **Confirm**.
4. The system generates a manifest CSV file. This file contains every package for that animal: SKU, product name, quantity, individual weights, and total weight.
5. The CSV is saved to the USB drive (if one is plugged in) or to the local `exports` folder on the computer.
6. If email is configured and auto-email is turned on, the manifest is emailed to the configured recipients.
7. All data for that animal (boxes, packages, barcodes) is removed from the app's memory to free up space.

**CRITICAL: Once an animal is closed, its data cannot be retrieved from the app.** The only records that survive are the CSV file on disk and the email. Always confirm that the export and email succeeded before moving on.

**Best practice: Close each animal as soon as labeling for it is complete.** Do not leave animals open overnight. If the system restarts (power outage, Windows update, etc.), open animals and their packages are lost.

### Deleting an Animal (for Mistakes Only)

The **Delete** button removes an animal without exporting anything. Use this only if you created an animal by accident. The data is permanently gone.

### Daily Production Report

At the end of a shift, you can generate a report covering all animals processed during the session:

1. Tap the **Animals** tab.
2. Tap **Send Daily Report**.
3. A CSV is generated and emailed to the configured recipients.

This is a summary across all animals, separate from the individual animal manifests.

---

## 10. Products: Finding and Selecting What to Label

### Product Categories

Products are organized into six categories. Each category has its own sub-tab within the Products screen.

| Category | What Is in It |
|----------|--------------|
| Steaks | Ribeye Bone-In, NY Strip Boneless, Filet Mignon, Tri-Tip, etc. |
| Roasts | Chuck Roast, Eye of Round, Sirloin Tip, Cross Rib, etc. |
| Ground | Burger Patties, Ground Beef 70/30, Stew Meat, etc. |
| Offal/Specialty | Liver, Tongue, Heart, Cheeks, Sweetbreads, etc. |
| Bones | Marrow Bones, Stock Bones, Shank, Tendon, etc. |
| Sausage/Processed | Chorizo, Hot Dogs, Bacon, Summer Sausage, etc. |

There are 71 active products in total.

### How to Select a Product

1. Tap the **Products** tab.
2. Tap one of the category sub-tabs (Steaks, Roasts, etc.).
3. Find the product you want. Each product is shown as a large button with the product name and its SKU number.
4. Tap the product button.
5. The screen automatically switches to the **Label** tab with that product ready to go.

### Searching for a Product by Name

If you know the product name but not which category it is in:

1. Tap the **Products** tab.
2. Tap the **Search** sub-tab.
3. An on-screen keyboard appears.
4. Start typing part of the product name. For example, type "rib" and you will see "Ribeye Steak Bone-In," "Ribeye Steak Boneless," "Short Ribs," etc.
5. Results filter in real time as you type.
6. Tap the matching product to select it.

---

## 11. Labeling: The Core Workflow, Step by Step

This is the primary function of the system. You will spend most of your time on this screen.

### Step-by-Step Process

**Step 1: Confirm the Product**
After selecting a product on the Products tab, the Label tab opens. At the top, you will see the product name and SKU. Make sure this is correct. If it is wrong, go back to the Products tab and select the right one.

**Step 2: Place the Package on the Scale**
Put the meat package on the center of the scale platform. Make sure nothing else is touching the scale. Make sure the package is not hanging over the edge.

**Step 3: Wait for the Weight to Lock**
The weight reading appears on screen and updates several times per second. The system needs the reading to be stable (not changing) before it will accept it.

What "stable" means: the scale must give the exact same reading for a certain number of consecutive checks. By default, this is 1 second (1000 milliseconds). You will see a progress indicator showing how close the reading is to locking.

**Step 4: Weight Locks Automatically**
When the weight is stable, the display shows the locked weight in large text. The background may change color to indicate the weight is confirmed.

**Step 5: Barcode Is Generated**
The system creates a 14-digit barcode string. You do not need to do anything for this step. It happens automatically.

The barcode contains:
- Digits 1 through 4: "0001" (meaning this is a single package)
- Digits 5 through 9: the 5-digit SKU number
- Digits 10 through 14: the weight in hundredths of a pound (1.52 lb = 00152)

**Step 6: Label Is Sent to the Printer**
The system sends a print command to the Zebra printer. You will see a brief animation that says "Sending to printer..."

**Step 7: Label Prints**
The Zebra prints the label. Pick it up and stick it on the package.

**Step 8: Success Confirmation**
A green panel appears with a checkmark, a preview of what was printed, and the barcode digits. This confirms the label printed and the package was recorded.

**Step 9: Auto-Return to Products**
After 2.5 seconds, the screen automatically goes back to the Products tab so you can select the next product. You do not need to tap anything.

**Step 10: Package Is Recorded**
The system saves the package data (product, weight, barcode, timestamp, operator name, box number) to memory. This data will appear in the animal's manifest when you close the animal.

### What If the Weight Will Not Lock (Stability Override)

If the weight reading keeps jumping around and does not stabilize within 10 seconds (and the reading is greater than zero), two buttons appear:

- **Lock at X.XX lb**: This accepts the current reading, whatever it is. Tap this if the reading is close enough.
- **Manual Entry**: This opens a numeric keyboard. You type the weight yourself (for example, "1.52"). Use this if you weighed the package on a different scale.

Both options are recorded in the audit log so they can be reviewed later.

### What If the Label Does Not Print (Print Failure)

If the printer returns an error, a large overlay covers the entire screen with three buttons:

| Button | What It Does | When to Use It |
|--------|-------------|----------------|
| **Retry Print** | Sends the exact same print command to the printer again. | Try this first. Most failures are temporary (a brief USB hiccup, for example). |
| **Save Without Print** | Records the package data but does not print a label. | Use this if the printer is down and you need to keep working. Write the label information by hand on a blank label. |
| **Cancel** | Throws away the package entirely. Nothing is recorded. | Use this if you made a mistake and do not want to record the package. |

The error message is shown on screen. Common reasons:
- "USB cable disconnected" -- check the cable.
- "Printer not found" -- the printer name in settings does not match Windows.
- "Printer paused" -- power cycle the Zebra (unplug power, wait 5 seconds, replug).
- "Print request timed out (10s)" -- the printer did not respond within 10 seconds. Check power and USB.

### Speed Tracking

If you label 4 or more packages within 60 seconds, a brief celebration message appears. This is just for fun and does not affect anything. It goes away when you switch tabs.

---

## 12. Boxes: Grouping Packages for Shipping

Every animal starts with one open box. As you label packages, they are automatically added to the current open box.

### Understanding Box Status

- **Open (green stripe on the left side of the box card):** This box is currently receiving packages. Only one box can be open at a time for each animal.
- **Closed (gray stripe on the left side of the box card):** This box is sealed. Summary labels have been printed. You can reopen it or reprint labels.

### What You See on Each Box Card

Each box card on the Boxes tab shows:
- Box number (for example, "Box #1")
- How many packages are in it and the total weight
- A breakdown by product (for example, "3x Ribeye Bone-In (4.2 lb)")

### How to Close a Box

1. Tap the **Boxes** tab.
2. Find the open box (green stripe). Tap **Close Box**.
3. A confirmation popup appears. Tap **Print Labels and Close**.
4. If the box has no packages, it closes immediately with no labels.
5. If the box has packages:
   - The system generates one summary label for each unique product (SKU) in the box.
   - For example, if the box has 5 Ribeyes and 3 Filet Mignons, it generates 2 labels: one for Ribeyes, one for Filet Mignons.
   - Each label shows: "[count]x [product name]", the total weight for that product, and a barcode that encodes the count, SKU, and total weight.
   - A preview screen appears showing all the labels before they print.
6. Tap **Print [X] Labels and Close Box**.
7. The labels print.
8. A new empty box is automatically created for the animal so you can continue labeling.

### How to Reopen a Box

1. Find the closed box on the Boxes tab.
2. Tap **Reopen Box**.
3. The box returns to open status and can receive more packages.
4. **Important:** The summary labels you already printed are now outdated. After adding more items, close the box again to print updated labels.

### How to Reprint Box Labels

1. Find the closed box on the Boxes tab.
2. Tap **Reprint Labels**.
3. The system regenerates the labels from the current data and prints them.
4. Use this if a label was damaged, lost, or if you need a duplicate.

### How to Create an Extra Box Manually

Tap **New Box** at the top of the Boxes screen. This creates a new empty box. You generally do not need to do this because closing a box automatically creates a new one.

---

## 13. Scanner: Voiding Packages and Auditing Boxes

The **Scanner** tab is where you use the Zebra DS2208 barcode scanner to look up or void packages.

### How Barcode Scanning Works in This System

The barcode scanner is a USB device that acts like a very fast keyboard. When you scan a barcode, the scanner types the numbers into the computer followed by an Enter key press. The system watches for rapid digit entry (less than 80 milliseconds between each digit) to distinguish scanner input from someone slowly typing on the on-screen keyboard.

The system expects barcodes to be exactly **14 digits long**.

### Voiding a Package (Removing It from the Record)

Use this when:
- A label was printed wrong (wrong product, wrong weight)
- A package is damaged and cannot be shipped
- A label needs to be re-done

Step by step:

1. Tap the **Scanner** tab.
2. Pick up the barcode scanner.
3. Point the scanner at the barcode on the package label.
4. Pull the trigger (or let it auto-scan, depending on your scanner settings).
5. The system finds the package and shows its details: product name, SKU, weight, which animal it belongs to, which box it is in.
6. Tap **Void This Package**.
7. An on-screen keyboard appears. Type a reason for the void (for example, "wrong weight" or "damaged package").
8. Tap **Confirm**.
9. The package is marked as void. It will NOT appear in future manifests. The void event, the reason, and your operator name are recorded in the audit log.

**Voiding is permanent in the sense that you cannot "un-void" a package.** If you void something by mistake, you need to re-label the package (weigh it again on the Label tab).

The voided package still exists in the system's records for audit purposes. It just does not count toward weight totals or manifests.

### Auditing a Box (Checking Its Contents)

Use this to verify what is in a closed box without opening it physically.

1. Tap the **Scanner** tab.
2. Scan the barcode on a box summary label.
3. The system decodes the SKU and weight from the barcode and finds the matching box.
4. A detail panel shows:
   - Animal name
   - Box number
   - All packages (including voided ones, which are marked as void)
   - Total weight
5. You can optionally tap **Email Manifest** to send the box contents by email.

### Global Scan (Works from Any Tab)

You can scan a barcode while you are on any tab, not just the Scanner tab. If you do, a popup appears with the package details and a quick-void button. This is handy for spot-checking a label without leaving the Products or Label screen. Tap outside the popup to close it.

---

## 14. Settings: Every Option Explained

Tap the **Settings** tab to see all configuration options. Every setting is saved to the server and survives restarts, power cycles, and browser profile resets.

### Email and Reports Section (Cyan/Light Blue Card)

| Setting | What It Does | Default | How to Change It |
|---------|-------------|---------|-----------------|
| Email Recipients | The email addresses where manifests, reports, and audit logs are sent. Separate multiple addresses with commas. | Empty (no email sent) | Tap the field, type the email addresses using the on-screen keyboard, tap confirm. |
| Auto-email manifest on animal close | When turned ON, the manifest CSV is automatically emailed every time you close an animal. | OFF | Tap the toggle switch to turn it on or off. |
| Auto-email daily production report | When turned ON, a daily summary is emailed when you tap Exit. | OFF | Tap the toggle switch. |
| Send Test Email | Sends a test message to the configured recipients to make sure email is working. | N/A | Tap the button. If it says "Sent!" then email is working. If it shows an error, see Troubleshooting. |

### Printer Section (Orange Card)

| Setting | What It Does | Default | How to Change It |
|---------|-------------|---------|-----------------|
| Printer Name | The exact name of the Zebra printer as it appears in Windows. **Must match exactly, including capitalization.** | zebra | Tap the field, type the name, confirm. |
| Print Darkness | How dark the thermal print is. Higher = darker. Range: 1 (lightest) to 30 (darkest). | 15 | Tap the + or - buttons to adjust. |
| Send Test Print | Sends a test label to the printer to verify it is working. | N/A | Tap the button. A test label should print within a few seconds. |

**How to check the printer name in Windows:** If you have a keyboard connected, press Ctrl+Esc to open the Start menu, then type "Printers" and open "Printers and Scanners." The name shown there is what you must enter in the app. If you do not have a keyboard, use RustDesk for remote support.

### Scale Section (Green Card)

| Setting | What It Does | Default | How to Change It |
|---------|-------------|---------|-----------------|
| Scale Mode | "Serial" for the real Brecknell scale. "Simulated" for a test slider (development only). | Serial | Tap to toggle. **Always leave on "Serial" in production.** |
| COM Port | Which USB port the scale is connected to. | COM3 | Use Auto-Detect (see below). |
| Auto-Detect | Scans all USB ports, finds the Brecknell scale, and sets the COM port automatically. | N/A | Tap the button. Wait a few seconds. It will say "Scale found on COMX" or "No scale detected." |
| Baud Rate | Communication speed between the computer and the scale. Must match the scale's setting. | 9600 | **Do not change this** unless a technician tells you to. Options: 9600, 19200, 38400, 115200. |
| Stability Delay | How long the weight must stay the same before the system locks it. Range: 500ms to 5000ms. | 1000 ms | Tap + or - to adjust. See guidance below. |
| Max Weight | Maximum weight the system will accept. Prevents barcode encoding errors. | 30 lb | Tap to change. Should match or exceed your scale's capacity. |

**Stability delay guidance:**
| Environment | Recommended Delay |
|-------------|------------------|
| Very stable surface, no vibration | 500 ms (half a second) |
| Normal conditions | 1000 ms (1 second, the default) |
| Some vibration (foot traffic, nearby equipment) | 2000 ms (2 seconds) |
| Heavy vibration or very precise weight requirements | 3000 ms or higher |

### System Section (Red Card)

| Setting | What It Does |
|---------|-------------|
| App Version | Shows the current version of the software. You cannot change this; it is read-only. |
| Storage Usage | A colored bar showing how much of the browser's 5 MB storage limit is being used. Green (0 to 49%), orange (50 to 79%), red (80%+). If it is red, you need to close animals to free space. |
| Check for Updates | Contacts GitHub to see if newer code is available. Requires internet. |
| Apply Update | Downloads and installs the update, rebuilds the frontend, and restarts the app. Takes 1 to 2 minutes. |
| Reset Settings | Returns all settings to factory defaults. Does NOT delete session data (animals, boxes, packages). |
| Clear All Session Data | Permanently deletes all animals, boxes, and packages from the current session. Settings are NOT affected. **This cannot be undone.** |

### Audit Log Section (Purple Card)

| Setting | What It Does |
|---------|-------------|
| Log Viewer | A scrollable list of the 100 most recent events, newest first. Each entry shows the time, the event type, and details. |
| Email Log | Sends the complete audit log as a CSV email attachment to a recipient you choose. |
| Clear Log | Deletes all audit log entries. **Requires passcode 3450.** The fact that the log was cleared is itself recorded before the entries are deleted. |

---

## 15. Data, Exports, and Email: Where Everything Goes

### Where Each Type of Data Is Stored

| Data Type | Where It Is Stored | Does It Survive a Restart? |
|-----------|--------------------|---------------------------|
| Settings (printer, scale, email, operator names) | Server file: `exports/settings.json` | **Yes** |
| Operator names (most recent 5) | Server file: `exports/settings.json` | **Yes** |
| Animals, boxes, packages (current session) | Browser memory (localStorage, 5 MB limit) | **No.** Cleared on every restart. This is why closing animals is critical. |
| Audit log | Browser memory + server backup | **Partially.** Server backup is retained. |
| Exported manifests (CSV files) | USB drive (if connected) or local `exports/` folder | **Yes** |
| Email queue (emails waiting to be sent) | Server file: `data/email_queue.json` | **Yes** |

### What Happens When You Close an Animal

1. The system creates a CSV file in memory containing every package for that animal.
2. The CSV is sent to the Flask backend server.
3. The server writes the CSV to the `exports/` folder. If a USB drive is plugged in, the server detects the drive automatically and writes the file there instead.
4. If email is turned on, the CSV is added to the email queue.
5. If the internet is available, the email sends immediately.
6. If the internet is NOT available, the email stays in the queue and is retried automatically every 5 minutes. The queue holds up to 100 emails and keeps them for up to 7 days.
7. The animal data is then purged from the app's memory.

### CSV File Naming

- **Animal manifest:** `manifest_[animal name]_[timestamp].csv`
- **Daily production report:** `daily_production_[date].csv`
- **Audit log:** `audit_log_[date].csv`

### What Happens If Email Fails

Nothing is lost. The CSV is always saved to disk first, before any email attempt. Even if the email service is completely broken, your data is safe on the local drive or USB.

---

## 16. Audit Log and Compliance

Every significant action is recorded with a timestamp, the operator name, and relevant details. This creates an auditable trail of all labeling activity.

### Complete List of Tracked Events

| Event | What Triggered It |
|-------|-------------------|
| operator_shift_started | Operator logged in at the gate |
| operator_changed | Mid-shift operator change |
| product_selected | Operator tapped a product |
| weight_captured | Scale reading locked |
| weight_override_forced | Operator used the "Lock at" button (weight was not stable) |
| weight_manual_entry | Operator typed a weight by hand |
| label_printed | Label successfully sent to printer |
| print_failed | Printer returned an error |
| print_retry | Operator tapped Retry after a print failure |
| print_skipped_save | Operator chose "Save Without Print" after a print failure |
| package_recorded | Package data stored in the system |
| package_voided | Package marked as void (with the reason) |
| box_created | New box opened |
| box_closed | Box closed and summary labels printed |
| box_reopened | A closed box was reopened |
| box_labels_printed | Box summary labels printed during close |
| box_labels_reprinted | Box labels reprinted from a closed box |
| animal_created | New animal started |
| animal_selected | Operator switched which animal is active |
| animal_closed | Animal closed and manifest exported |
| animal_purged | Animal data removed from memory |
| manifest_exported | CSV file written to disk |
| manifest_emailed | CSV sent via email |
| daily_report_exported | Daily report CSV generated |
| audit_log_emailed | Audit log sent as email attachment |
| audit_log_cleared | Audit entries deleted (passcode verified) |
| data_cleared | All session data wiped from Settings |
| app_exit_initiated | Operator tapped Exit |
| workflow_cancelled | Operator cancelled a labeling operation mid-way |

### Viewing the Audit Log

1. Tap the **Settings** tab.
2. Scroll down to the **Audit Log** section (purple card).
3. The log viewer shows the 100 most recent entries, newest first.
4. Each entry shows the timestamp, event type, and payload (a JSON object with details like SKU, barcode, weight, and operator name).

### Emailing the Audit Log

1. Settings > Audit Log > **Email Log**.
2. Select a recipient from the list, or tap "Enter Email" to type a new one.
3. The entire log is formatted as a CSV and sent as an email attachment.

### Clearing the Audit Log

1. Settings > Audit Log > **Clear Log**.
2. A passcode prompt appears. Enter **3450**.
3. All entries are deleted. (The fact that the log was cleared is recorded as the final entry before deletion.)

---

## 17. Software Updates: How to Check and Apply

The system can update itself from the GitHub repository if the Beelink has internet access.

### How to Check for Updates

1. Tap the **Settings** tab.
2. Scroll to the **System** section (red card).
3. Tap **Check for Updates**.
4. The system contacts GitHub. After a few seconds, it reports how many new commits (code changes) are available.
5. If updates are available, a button appears: "Update Available (X commits)."

### How to Apply an Update

1. Tap the update button.
2. A confirmation popup appears. Tap **Confirm**.
3. The system does the following (this takes 1 to 2 minutes):
   - Downloads the latest code from GitHub.
   - Rebuilds the frontend.
   - Restarts the backend server.
4. The screen may go white briefly. **This is normal.** Do not turn off the computer.
5. The app reloads automatically within about 60 seconds.

### What If an Update Fails

- A message appears: "Update May Have Failed." Two buttons: **Reload Now** and **Wait Longer**.
- Try **Reload Now** first.
- If the app does not come back, wait 60 more seconds.
- If it still does not work, restart the Beelink by pressing and holding the power button for 5 seconds, then pressing it again. The watchdog will restart the app.
- If the problem persists after a restart, use RustDesk for remote support (contact Peter at peter@westllc.co).

---

## 18. Quick Fixes: Common Bugs and How to Solve Them

This section documents specific bugs and quirks that have been discovered during development and testing. Each one has a plain-language explanation of what goes wrong and how to fix it.

### Bug: Chrome Shows an Old Error Page After Restart

**What happens:** Instead of the labeling app, Chrome shows a page that says "This site can't be reached" or something similar from a previous crash.

**Why:** Chrome cached an error page from the last time it crashed, and it reloads that cached page instead of the live app.

**Fix:** This should not happen during normal operation because the startup script deletes the Chrome profile on every restart. If it does happen:
1. Wait 30 seconds. The watchdog should restart the app with a clean profile.
2. If it does not resolve, restart the Beelink (hold power 5 seconds, then press again).

### Bug: Port 8000 Is Already in Use (Server Cannot Start)

**What happens:** The labeling app shows a blank screen because the backend server could not start.

**Why:** A previous instance of the Python server did not shut down cleanly, and its network port (8000) is still being held open by Windows. Windows can hold a port in a "TIME_WAIT" state for up to 30 seconds after a program exits.

**Fix:** This should be handled automatically by the startup script, which kills anything on port 8000 before starting the server. Additionally, the server uses a setting called SO_REUSEADDR that allows it to take over the port immediately. If you still see a blank screen:
1. Wait 30 to 60 seconds. The watchdog will retry.
2. If still blank, restart the Beelink.

### Bug: Operator Names Are Missing Right After Startup

**What happens:** The operator gate appears, but the list of recent names is empty. After a few seconds, the names appear.

**Why:** The operator names are stored on the server. When the app first loads, it takes 1 to 3 seconds to fetch them. During that time, the list is empty.

**Fix:** This is normal behavior, not a real bug. Just wait 2 to 3 seconds and the names will appear. If names NEVER appear, the `exports/settings.json` file may be corrupted. Go to Settings > Reset Settings and re-enter operator names.

### Bug: Chrome Orphan Processes Accumulate

**What happens:** The Beelink becomes slow over time, especially after several restarts.

**Why:** Chrome creates many sub-processes (for rendering, GPU acceleration, crash reporting). When the app restarts, not all of these processes are killed. They accumulate.

**Fix:** The startup script aggressively kills all Chrome processes before each restart. If slowness occurs:
1. Tap **Exit** to shut down cleanly (this triggers a thorough process cleanup).
2. Restart the Beelink.

### Bug: Scale Shows "SCALE ERROR" After Unplugging and Replugging the USB Cable

**What happens:** You unplug the scale's USB cable and plug it back in, but the app shows "SCALE ERROR."

**Why:** When you unplug and replug the scale, Windows may assign it a different COM port number. The app is still looking for the old port.

**Fix:**
1. Go to Settings > Scale.
2. Tap **Auto-Detect**.
3. The system scans all ports and finds the scale on its new port.
4. If Auto-Detect does not find it, try unplugging the USB cable, waiting 5 seconds, and plugging it back in. Then tap Auto-Detect again.
5. If it still does not work, restart the Beelink.

### Bug: Scale Error Flickers Briefly, Then Disappears

**What happens:** The "SCALE ERROR" message appears for a fraction of a second, then goes away, and the scale works fine.

**Why:** The scale has transient communication errors (a single dropped serial frame, for example). The app waits for 15 consecutive failures (about 3 seconds) before showing the error permanently. A single failure or brief interruption resolves itself.

**Fix:** No action needed. This is handled automatically. If the error persists for more than 5 seconds, then there is a real problem. See Troubleshooting: Scale Problems.

### Bug: Weight Reading Jumps Between Two Values

**What happens:** The weight display on the Label screen alternates between two numbers (for example, 1.52 and 1.53) and never locks.

**Why:** The scale reading is fluctuating due to vibration, air currents, or the item not being fully on the platform.

**Fix:**
1. Make sure the item is centered on the scale and not touching anything.
2. Wait. If it does not stabilize within 10 seconds, the manual override buttons appear. Use "Lock at X.XX lb" to accept the current reading.
3. If this happens frequently, increase the stability delay in Settings (try 2000ms).
4. If the work area has heavy vibration, put a vibration-dampening pad under the scale.

### Bug: "Storage Nearly Full" Warning Appears

**What happens:** A warning banner appears at the top of the screen saying storage is nearly full.

**Why:** The browser's localStorage limit is 5 MB. If you process many animals without closing them, the data builds up.

**Fix:**
1. Go to the **Animals** tab.
2. Close all completed animals. Closing exports the data and frees memory.
3. If the warning persists, clear the audit log (Settings > Audit Log > Clear Log, passcode 3450).
4. As a last resort, use Settings > System > Clear All Session Data. Only do this if all important data has been exported.

### Bug: Email Queue Keeps Growing and Emails Never Send

**What happens:** You see messages like "Queued, will retry" but emails never actually send.

**Why:** The Beelink does not have internet access, or the Resend API token has expired.

**Fix:**
1. Check the network indicator in Settings. If it says "Offline," fix the network connection (check Ethernet cable or WiFi).
2. If the indicator says "Online" but emails still fail, the Resend API token may have expired. Contact Peter at peter@westllc.co.
3. The queue holds up to 100 emails for up to 7 days. If older emails expire from the queue, they are automatically removed. The CSV data is always saved to disk regardless of email status.

### Bug: Voided Packages Still Appear in a Closed Box's Label Count

**What happens:** This does NOT happen. When a box is closed, voided packages are automatically removed from the data. But if you reopen a box, void a package, and then reprint labels, the reprinted labels will reflect the updated (corrected) data.

**Clarification:** Voided packages are excluded from box labels, manifests, and weight totals. If you void a package inside a closed box and need updated labels, reprint the box labels.

### Bug: Print Timeout (10 Seconds) with No Error Message from the Printer

**What happens:** The app shows "Print request timed out (10s)" but the printer light is solid green and nothing else seems wrong.

**Why:** The print command was sent but the printer did not acknowledge it within 10 seconds. This can happen if the USB connection is slow or the printer is busy processing a previous label.

**Fix:**
1. Tap **Retry Print**. This almost always works on the second attempt.
2. If retry also times out, power cycle the Zebra (unplug power, wait 5 seconds, replug).
3. Check the USB cable.

### Bug: Email Queue File Gets Corrupted After Power Loss

**What happens:** Emails in the queue are lost after a power outage.

**Why:** This should NOT happen. The email queue uses atomic file writes (writes to a temporary file first, then renames it). This means that even if power is lost in the middle of a write, the previous version of the queue file is intact.

**If it does happen:** The queue is simply empty on restart. No data is lost because the CSV files are saved to disk before being queued for email. The CSVs can be found in the `exports/` folder and emailed manually if needed.

### Bug: Settings Are Lost After a Restart

**What happens:** This should NOT happen. Settings are stored on the server at `exports/settings.json`, not in the browser. They survive restarts.

**If settings are lost:**
1. The `exports/settings.json` file may be missing or corrupted.
2. Re-enter settings manually in the Settings tab. They will be saved immediately.
3. Contact Peter at peter@westllc.co if this happens repeatedly.

---

## 19. Troubleshooting: Printer Problems

### Zebra ZP 230D Indicator Light

| Light Behavior | Meaning |
|----------------|---------|
| Solid green | Ready. Normal operation. |
| Flashing green | Paused or error at firmware level. |
| Off | No power or USB not connected. |

### Problem: Nothing Prints, Light Is Solid Green

**What is going on:** The printer is ready, but it is not receiving the print job. Usually this means the printer name in the app does not match the printer name in Windows.

**How to fix it:**
1. Go to Settings > Printer.
2. Look at the Printer Name field.
3. You need to check what the printer is called in Windows. If you have a keyboard: press Ctrl+Esc, type "Printers," open "Printers and Scanners." Look at the name of the Zebra printer. It must match exactly, including uppercase and lowercase letters.
4. If the names do not match, change the name in the app to match Windows.
5. Tap **Send Test Print** to verify.

### Problem: Nothing Prints, Light Is Flashing Green

**What is going on:** The printer has paused itself. This commonly happens when the USB cable is disconnected and reconnected while the printer is powered on.

**How to fix it:**
1. Find the power cable going into the back of the Zebra printer.
2. Unplug it from the printer (not from the wall).
3. Count to 5.
4. Plug it back in.
5. Wait for the light to turn solid green (about 5 to 10 seconds).
6. Tap **Send Test Print** in Settings to verify.

### Problem: Labels Print but They Are Very Faint

**What is going on:** The print darkness setting is too low, or the printhead is dirty.

**How to fix it:**
1. Go to Settings > Printer > Print Darkness.
2. Increase the value. Try 20 first. If still faint, try 25.
3. Tap **Send Test Print** after each change to compare.
4. If still faint at 30, the printhead needs cleaning:
   - Turn off the printer (unplug power).
   - Open the lid.
   - Dampen a lint-free cloth with isopropyl alcohol (rubbing alcohol).
   - Gently wipe the printhead (the dark strip that runs across the inside of the lid).
   - Let it dry completely (at least 30 seconds).
   - Close the lid, plug the power back in.

### Problem: Labels Print Off-Center or Crooked

**What is going on:** The label roll is not seated correctly.

**How to fix it:**
1. Open the printer lid (press the release tabs on both sides).
2. Take the label roll out.
3. Put it back in, making sure the labels feed through the center guides. The guides should be snug against both sides of the roll.
4. Close the lid firmly until you hear it click.
5. Press the feed button once to advance one label and check alignment.

### Problem: "Print Failed" Overlay Appears on Screen

**What is going on:** The system tried to print but got an error back.

**How to fix it:**
1. Tap **Retry Print**. This works most of the time.
2. If retry fails, check the USB cable at both ends (printer end and Beelink end). Push them in firmly.
3. Power cycle the Zebra (unplug power, wait 5 seconds, replug).
4. If still failing, tap **Save Without Print** to record the package. Write the label by hand.
5. If the problem happens repeatedly, restart the Beelink.

### Problem: Printer Prints a Blank Label

**What is going on:** The label stock is loaded upside down. The thermal coating is facing the wrong way.

**How to fix it:**
1. Take a label from the roll.
2. Scratch it with your fingernail.
3. The side that shows a dark mark from the scratch is the PRINT side.
4. Load the roll so the print side faces UP (toward the printhead, which is in the lid).

---

## 20. Troubleshooting: Scale Problems

### Problem: "SCALE ERROR" on the Label Screen

**What is going on:** The computer cannot communicate with the scale.

**How to fix it (in this order):**
1. Go to Settings > Scale.
2. Tap **Auto-Detect**. Wait a few seconds.
3. If the message says "Scale found on COMX": the problem is fixed. Go back to the Label tab.
4. If "No scale detected":
   - Check the USB cable between the scale and the Beelink. Make sure both ends are firmly plugged in.
   - Make sure the baud rate in Settings is set to **9600**.
   - Try a different USB port on the Beelink.
   - Unplug the USB cable, wait 5 seconds, plug it back in. Then tap Auto-Detect again.
   - If none of this works, restart the Beelink.

### Problem: Weight Keeps Jumping and Never Locks

**What is going on:** The scale reading is not stable. Environmental factors are causing the reading to change.

**How to fix it:**
1. Make sure the package is centered on the scale platform and is not touching anything else.
2. Remove anything that might be resting on or near the scale (tools, other packages, your hand).
3. Make sure the surface the scale is on is stable and level.
4. Wait. If it does not lock within 10 seconds, manual override buttons appear:
   - Tap **Lock at X.XX lb** to accept the current reading.
   - Tap **Manual Entry** to type the weight yourself.
5. If this is a recurring problem, go to Settings > Scale > Stability Delay and increase it to 2000 ms or 3000 ms.

### Problem: Scale Reads Zero with an Item on It

**What is going on:** The scale needs to be zeroed (tared), or the item is too light.

**How to fix it:**
1. Remove the item.
2. Wait for the scale to read 0.00 on its own display.
3. If it does not read 0.00, press the **zero** button on the scale indicator (the small display box attached to the platform).
4. Put the item back on.

### Problem: Scale Shows "Over Capacity"

**What is going on:** The item is heavier than 15 pounds (the scale's maximum).

**How to fix it:**
1. Remove the item immediately. Leaving heavy items on the scale can damage the load cell.
2. Weigh the item on a different, higher-capacity scale.
3. On the Label screen, use **Manual Entry** to type the weight.

### Problem: Scale Not Found During Auto-Detect

**What is going on:** Windows does not recognize the scale's USB connection.

**How to fix it:**
1. Unplug the scale's USB cable from the Beelink.
2. Wait 5 seconds.
3. Plug it into a different USB port on the Beelink.
4. Wait 10 seconds for Windows to install the driver.
5. Go to Settings > Scale > Auto-Detect.
6. If still not found, restart the Beelink. The USB driver loads during boot.
7. If still not found after restart, the USB cable or serial adapter may be broken. Try a different cable.

---

## 21. Troubleshooting: System and Software Problems

### Problem: App Shows a White Screen

**What is going on:** The frontend did not load. Either the backend server is not running or the frontend build files are missing.

**How to fix it:**
1. Wait 15 to 30 seconds. The watchdog may restart the app automatically.
2. If it does not recover, restart the Beelink (hold power 5 seconds, press again).
3. If it still shows white after reboot, connect via RustDesk for remote support (contact Peter at peter@westllc.co).

### Problem: App Freezes and Does Not Respond to Touch

**What is going on:** The app has hit a memory limit or a JavaScript error.

**How to fix it:**
1. Wait 30 seconds. The watchdog monitors the backend server and will restart if it detects a failure.
2. If the app does not recover, restart the Beelink.
3. On restart, the Chrome profile is deleted, which clears any corrupted browser state.
4. Settings are preserved. Session data (open animals, boxes, packages) may be lost. This is why closing animals promptly matters.

### Problem: Touchscreen Does Not Respond at All

**What is going on:** The touch USB cable is disconnected or the touch driver is not loaded.

**How to fix it:**
1. Check the USB cable from the touchscreen to the Beelink. Push both ends in firmly.
2. Restart the Beelink.
3. If touch still does not work, temporarily connect a USB mouse to navigate.
4. Use RustDesk for remote support if no input method works.

### Problem: System Is Running Slowly

**What is going on:** Too many processes, too much data in memory, or orphaned processes from previous restarts.

**How to fix it:**
1. Close all completed animals (Animals tab > Close Animal). This frees memory.
2. Tap **Exit** to shut down cleanly, then restart the Beelink. The clean shutdown kills all orphaned processes.
3. If the problem persists after a fresh restart, contact Peter at peter@westllc.co.

---

## 22. Troubleshooting: Network and Email Problems

### Problem: Emails Say "Queued, Will Retry"

**What is going on:** The Beelink does not have internet access.

**How to fix it:**
1. Check the network indicator in Settings. It should say "Online" in green.
2. If it says "Offline":
   - If using Ethernet (wired): check the Ethernet cable at both ends (Beelink and router/switch).
   - If using WiFi: the Beelink supports WiFi 5. Make sure the WiFi network is working. You may need to reconnect through Windows network settings (this requires a keyboard or RustDesk).
3. Once connectivity is restored, queued emails will send automatically within 5 minutes. You do not need to do anything manually.
4. Data is always saved to disk first. Even if email never works, your CSV files are safe in the `exports/` folder.

### Problem: Emails Not Arriving Despite "Online" Status

**What is going on:** The Resend API token may have expired, or the recipient address is wrong.

**How to fix it:**
1. Go to Settings > Email > **Send Test Email**.
2. If the test email fails and the error mentions "API key" or "unauthorized": contact Peter at peter@westllc.co. The Resend API token needs to be regenerated.
3. If the error mentions "invalid recipient": check the email address in Settings for typos.
4. If the test email "succeeds" but the recipient does not receive it: check the recipient's spam/junk folder. Emails sent through Resend can be flagged by some email providers.

### Problem: Cannot Check for Updates

**What is going on:** No internet connection, or GitHub is temporarily unreachable.

**How to fix it:**
1. Verify internet connectivity (Settings should show "Online").
2. Try again in a few minutes.
3. Updates are not required for daily operation. The system works fully offline.

---

## 23. Hardware Specifications and Replacement Parts

If any piece of hardware breaks and needs to be replaced, use the specifications below to order an identical or compatible replacement.

### Beelink Mini S12

| Specification | Value |
|---------------|-------|
| Processor | Intel 12th Gen N95 (4-core, up to 3.4 GHz) |
| RAM | 8 GB DDR4 |
| Storage | 256 GB SSD |
| Operating System | Windows 11 Home |
| Display output | Dual HDMI (4K) |
| Network | Gigabit Ethernet, Dual WiFi 5, Bluetooth 4.2 |
| Replacement note | Any Beelink Mini S12 with equivalent or better specs will work. The software runs on standard Windows 11. |

### Angel POS 17-Inch Capacitive Touchscreen

| Specification | Value |
|---------------|-------|
| Screen size | 17 inches |
| Resolution | 1280 x 1024 |
| Touch technology | Capacitive (multi-touch) |
| Design | True flat, seamless edge |
| Video input | VGA |
| Touch input | USB |
| Glove compatibility | Requires capacitive-compatible gloves |
| Replacement note | Any VGA or HDMI touchscreen monitor with USB touch output will work. The software does not depend on a specific brand. Resolution should be at least 1280 x 1024. |

### Zebra ZP 230D Label Printer

| Specification | Value |
|---------------|-------|
| Print method | Direct thermal (no ink or ribbon) |
| Resolution | 203 DPI |
| Max label width | 4.09 inches |
| Connectivity | USB, Serial, Parallel |
| Driver | ZDesigner or generic ZPL driver |
| Replacement for | Zebra ZP 450 |
| Replacement note | Any Zebra printer that supports ZPL (Zebra Programming Language) at 203 DPI will work. The Zebra ZD220, ZD230, or ZD421 are current-production alternatives. The ZPL commands used by this system are standard and compatible across the Zebra desktop printer line. |

### Brecknell 6710U Platform Scale

| Specification | Value |
|---------------|-------|
| Capacity | 15 lb |
| Resolution | 0.005 lb |
| Platform | Stainless steel |
| Communication | Serial via USB adapter |
| Default baud rate | 9600 |
| Protocol | Sends weight data in response to `W\r` command |
| Replacement note | The Brecknell 6710U is the tested and confirmed model. Other Brecknell 67xx series scales use the same protocol and should work. Non-Brecknell scales may require software modification. |

### Zebra DS2208 Barcode Scanner

| Specification | Value |
|---------------|-------|
| Type | Handheld, standard range, corded |
| Part number | DS2208-SR7U2100AZW |
| Cable | Shielded USB |
| Scan types | 1D and 2D barcodes |
| Interface | USB HID (keyboard emulation) |
| Replacement note | Any USB barcode scanner that uses keyboard emulation (HID mode) will work. The system does not require a specific brand. The scanner must be able to read Code 128 barcodes. |

### BETCKEY 4x4 Label Stock

| Specification | Value |
|---------------|-------|
| Brand | BETCKEY |
| Size | 4 x 4 inches (102 x 102 mm) |
| Type | Direct thermal |
| Pre-printing | Pomponio Ranch artwork (logo, handling instructions, USDA stamp) |
| Adhesive | Premium adhesive, perforated between labels |
| Labels per roll | 350 |
| Replacement note | The pre-printed artwork is specific to Pomponio Ranch. Blank BETCKEY 4x4 labels can be used as emergency replacements (the label will only show the product name, barcode, and weight, without the pre-printed branding). To order pre-printed labels, contact the label vendor. |

---

## 24. OEM Instruction Manuals for All Hardware

The following links are to the official manufacturer documentation for each piece of hardware. These manuals cover setup, configuration, and troubleshooting at the hardware level, beyond what this operational guide covers.

**Responsible person for all hardware and software:** Peter dePOK, peter@westllc.co

### Brecknell 6710U Platform Scale

- **Full Manual (PDF):** https://www.brecknellscales.com/wp-content/uploads/2022/09/67xx-Serial-Scale_s_en_501145.pdf
- Covers: setup, calibration, serial communication protocol, indicator buttons, error codes.

### Zebra DS2208 Barcode Scanner

- **Product Reference Guide (full, 400+ pages, PDF):** https://www.zebra.com/content/dam/support-dam/en/documentation/unrestricted/guide/product/ds2208-prg-en.pdf
- **Quick Start Guide (PDF):** https://www.zebra.com/content/dam/support-dam/en/documentation/unrestricted/guide/product/ds2208-qsg-en.pdf
- **Support Page:** https://www.zebra.com/us/en/support-downloads/scanners/general-purpose-scanners/ds2200-series.html
- Covers: setup, programming barcodes, symbology settings, cable configuration.

### Angel POS 17-Inch Touchscreen Monitor

- **No official user manual exists.** This is a plug-and-play device (no driver required on Windows 10/11).
- **Spec Sheet:** https://angelpos.3dcartstores.com/assets/images/download/TouchScreen-Monitor-Specs.pdf
- **Driver Downloads (if needed):** https://angelpos.3dcartstores.com/Downloads_ep_43.html
- Setup: connect VGA/HDMI for video, USB for touch. No configuration needed.

### Beelink Mini S12

- **User Manual (via ManualsLib):** https://www.manualslib.com/manual/3590456/Beelink-Mini-S.html
- **Beelink Official Downloads:** https://www.bee-link.com/pages/drivers-hardware-download
- Covers: setup, dual display, storage expansion, BIOS access, troubleshooting.

### Zebra ZP 230D / ZP 450 Label Printer

- **Full User Guide (PDF, third-party mirror):** http://www.norsystems.net/UM-ZP450EN.pdf
  - Note: Zebra no longer hosts the complete guide for this end-of-life model. This mirror contains the full document (Zebra document 980546-003).
- **Maintenance/Cleaning (Zebra-hosted):** https://support.zebra.com/cpws/docs/crawl/zp_450/zp450_prev_maint.pdf
- **Print Quality Guide (Zebra-hosted):** https://support.zebra.com/cpws/docs/crawl/zp_450/zp450_print_qual.pdf
- **Zebra Support Page (drivers):** https://www.zebra.com/us/en/support-downloads/printers/desktop/zp450.html
- Covers: label loading, printhead cleaning, print quality adjustment, calibration, USB setup.

### Label Stock (BETCKEY 4x4)

No manual required. These are consumable labels. Reorder from Amazon or the BETCKEY website. Search for: "BETCKEY 4x4 Shipping Labels Compatible with Zebra."

---

## 25. Label Stock and Barcode Specification

### Pre-Printed Label Layout

The 4x4 inch labels come pre-printed with:

- Pomponio Ranch logo (top left area)
- Company name and contact info (top right area)
- "Keep Refrigerated or Frozen" text
- Safe Handling Instructions box (bottom left area)
- USDA establishment stamp (bottom right area)
- Website and marketing text

### Dynamic Fields (Printed by the System)

The system prints three fields onto each pre-printed label:

| Field | Where on the Label | Size and Style |
|-------|-------------------|----------------|
| Product name | Upper center, between the logo area and the barcode area | Up to 2 lines, centered, 45-dot font. Truncated to 24 characters if too long. |
| Barcode | Lower left area | Code 128, 14 digits, with the digit string printed below the bars. Module width: 2 dots. Bar height: 120 dots (approximately 15mm). |
| Net weight | Lower right area, above the USDA stamp | Three lines: "NetWeight" label (small), decimal pounds (large, e.g., "1.52 lb"), and pounds+ounces (small, e.g., "1 lb 8.3 oz"). |

### Barcode Specification

| Property | Value |
|----------|-------|
| Symbology | Code 128 |
| Length | 14 digits, all numeric |
| Encoding | Printer auto-selects optimal subset |
| Module width | 2 dots (approximately 0.25 mm at 203 DPI) |
| Bar height | 120 dots (approximately 15 mm) |
| Interpretation line | Yes (digits printed below the bars by the printer) |
| Check digit | Handled automatically by the Code 128 symbology; not part of the 14 data digits |

### Barcode Data Format

| Digit Positions | Field | Description |
|----------------|-------|-------------|
| 1 through 4 | Piece count | "0001" for individual packages. Actual count for box labels (e.g., "0012" for 12 items). Range: 0001 to 9999. |
| 5 through 9 | SKU | 5-digit Pomponio SKU, zero-padded (e.g., "00100" for Ribeye Steak Bone-In) |
| 10 through 14 | Weight | Weight in hundredths of a pound, zero-padded (e.g., "00152" means 1.52 lb) |

### Barcode Examples

**Individual package: 1.52 lb Ribeye Steak Bone-In (SKU 00100)**

Piece count: 0001 (individual), SKU: 00100, Weight: 00152 (1.52 * 100)
Full barcode: `00010010000152`

**Box label: 12 Filet Mignons (SKU 00103) totaling 9.60 lb**

Piece count: 0012, SKU: 00103, Weight: 00960 (9.60 * 100)
Full barcode: `00120010300960`

**Box label: 5 Ground Beef 70/30 (SKU 00200) totaling 24.50 lb**

Piece count: 0005, SKU: 00200, Weight: 02450 (24.50 * 100)
Full barcode: `00050020002450`

---

## 26. Maintenance Schedule

### Daily: Start of Shift

Do these things every day when you start work:

- [ ] Turn on the system. Wait for it to fully load (operator gate appears).
- [ ] Send a test print (Settings > Printer > Send Test Print). Make sure the label prints clearly.
- [ ] Check the scale: with nothing on it, the scale should read 0.00. If not, press the zero button on the scale indicator.
- [ ] Check label stock. Open the Zebra's lid and look at the roll. If fewer than about 50 labels remain, replace the roll now.
- [ ] Check that all USB cables are secure (printer, scale, scanner, touchscreen).

### Daily: End of Shift

Do these things every day when you finish work:

- [ ] Close all animals (Animals tab > Close Animal for each one). This exports manifests and frees memory.
- [ ] Send the daily production report (Animals tab > Send Daily Report).
- [ ] Tap the red **Exit** button in the top right corner to end the shift. Confirm when prompted.
- [ ] Optionally, turn off the Beelink if no overnight processing is planned.

### Weekly

- [ ] Check the storage usage bar in Settings > System. It should be green. If it is orange or red, close animals and clear the audit log.
- [ ] Review the audit log for any unexpected events (Settings > Audit Log).
- [ ] Wipe the touchscreen with a damp (not dripping wet) microfiber cloth. Do not use harsh chemicals.
- [ ] Visually inspect all USB cables for damage, wear, or loose connections.

### Monthly

- [ ] Clean the Zebra printhead:
  1. Unplug the Zebra's power cable.
  2. Open the lid.
  3. Dampen a lint-free cloth with isopropyl alcohol.
  4. Gently wipe the dark strip (printhead) inside the lid.
  5. Let dry 30 seconds.
  6. Close lid, replug power.
- [ ] Check for software updates (Settings > System > Check for Updates). Apply if available.
- [ ] Verify email delivery (Settings > Email > Send Test Email).
- [ ] Back up the `exports/` folder to a USB drive. Plug in a USB drive, navigate to `C:\pomponio-labeling\exports` using File Explorer (requires a keyboard or RustDesk), and copy all files to the USB drive.

### As Needed

- [ ] Replace the label roll when it runs out.
- [ ] Replace the Zebra printhead if print quality degrades permanently despite cleaning. Contact Peter at peter@westllc.co for part number and instructions.
- [ ] Contact Peter at peter@westllc.co if:
  - The Resend API token expires (emails stop working despite internet being available).
  - RustDesk access is not working.
  - Any problem persists after following this guide.

---

## 27. Quick Reference Card

**Print this section and post it near the workstation for daily reference.**

---

### HOW TO LABEL A PACKAGE

1. Animals tab > Select or create an animal
2. Products tab > Tap the product
3. Place package on scale
4. Wait for weight to lock
5. Label prints automatically
6. Stick label on package

### HOW TO CLOSE A BOX

1. Boxes tab
2. Tap "Close Box"
3. Preview the labels
4. Tap "Print Labels and Close Box"

### HOW TO VOID A PACKAGE

1. Scanner tab
2. Scan the package barcode
3. Tap "Void This Package"
4. Type a reason
5. Tap "Confirm"

### HOW TO CLOSE AN ANIMAL (EXPORTS DATA)

1. Animals tab
2. Tap "Close Animal"
3. Confirm
4. Manifest is saved to disk and emailed

### HOW TO END A SHIFT

Tap the red Exit button (top right corner) > Confirm

### PRINTER NOT PRINTING

1. Check USB cable at both ends (printer and computer)
2. Power cycle the Zebra: unplug power cable, wait 5 seconds, replug
3. Check printer name in Settings matches Windows exactly
4. Tap "Send Test Print" in Settings

### ZEBRA LIGHT FLASHING GREEN

Power cycle: unplug power cable from back of printer, wait 5 seconds, replug

### SCALE NOT READING

1. Settings > Scale > Auto-Detect
2. Check USB cable
3. Try a different USB port on the Beelink
4. Restart the Beelink if none of the above works
5. Use Manual Entry on the Label screen as a workaround

### SYSTEM FROZEN OR WHITE SCREEN

Wait 30 seconds (watchdog auto-restarts). If still frozen, hold the Beelink power button for 5 seconds. Then press it once to restart.

### LABELS ARE TOO FAINT

Settings > Printer > increase Print Darkness. Try 20, then 25. Send Test Print after each change.

### SCALE ERROR AFTER UNPLUGGING USB

Settings > Scale > Auto-Detect

### EMAILS NOT SENDING

1. Check network indicator in Settings (should say "Online")
2. If online but failing, contact Peter dePOK at peter@westllc.co (API token may need refresh)
3. CSV files are always saved to disk regardless of email

---

### PASSCODES

| Purpose | Code |
|---------|------|
| Windows login | 3450 |
| Clear audit log | 3450 |

### REMOTE SUPPORT (RUSTDESK)

| What | Value |
|------|-------|
| Device ID | 369 522 049 |
| Password | 3450Riverside! |

### IMPORTANT CONTACTS

| Who | Email | Role |
|-----|-------|------|
| Peter dePOK | peter@westllc.co | System owner and maintainer. Contact for all issues. |

### SOURCE CODE

GitHub repository: https://github.com/peterdepok/pomponio-labeling.git

---

*Pomponio Ranch Labeling System v3.0*
*Designed, built, and maintained by Peter dePOK, Westco*
*Contact: peter@westllc.co*
*February 2026*
