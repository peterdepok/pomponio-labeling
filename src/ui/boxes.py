"""
Box management screen.
Handles box closing, QR label printing, and verification.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable

from ..database import (
    Box, Package,
    get_current_box, get_box_by_id, get_box_by_number,
    get_packages_in_box, close_box, verify_box, create_box,
    update_box_totals, log_scan
)
from ..barcode import generate_box_qr_data, parse_box_qr_data, validate_box_qr
from ..printer import LabelGenerator, ZebraPrinter, MockPrinter
from ..scanner import ScanEvent, play_success_beep, play_error_beep
from .widgets import (
    COLORS, FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_MONO,
    TouchButton, StatusBar, show_verification
)


class BoxesScreen(tk.Frame):
    """
    Box management screen.

    Layout:
    +----------------------------------+
    | Current Box Info                 |
    +----------------------------------+
    | Package Details (scrollable)     |
    |                                  |
    +----------------------------------+
    | [NEW BOX]  [CLOSE & PRINT]       |
    +----------------------------------+
    | Recent Boxes List                |
    +----------------------------------+
    | Status Bar                       |
    +----------------------------------+
    """

    def __init__(
        self,
        parent,
        printer: Optional[ZebraPrinter] = None,
        **kwargs
    ):
        super().__init__(parent, **kwargs)
        self.config(bg=COLORS['bg'])

        self.printer = printer or MockPrinter()
        self.label_gen = LabelGenerator()

        # State
        self.current_box: Optional[Box] = None
        self.pending_box_id: Optional[int] = None
        self.pending_qr_data: Optional[str] = None

        # Build UI
        self._build_ui()

        # Load data
        self.refresh()

    def _build_ui(self):
        """Build the boxes screen UI."""
        # Main container
        main = tk.Frame(self, bg=COLORS['bg'])
        main.pack(fill='both', expand=True, padx=20, pady=20)

        # Current box section
        box_frame = tk.Frame(main, bg=COLORS['card_bg'], relief='solid', bd=1)
        box_frame.pack(fill='x', pady=(0, 15))

        # Box header
        header = tk.Frame(box_frame, bg=COLORS['card_bg'])
        header.pack(fill='x', padx=20, pady=15)

        tk.Label(
            header,
            text="CURRENT BOX",
            font=FONT_SMALL,
            bg=COLORS['card_bg'],
            fg=COLORS['disabled']
        ).pack(anchor='w')

        self.box_number_var = tk.StringVar(value="No Active Box")
        tk.Label(
            header,
            textvariable=self.box_number_var,
            font=FONT_LARGE,
            bg=COLORS['card_bg'],
            fg=COLORS['fg']
        ).pack(anchor='w')

        # Box stats
        stats_frame = tk.Frame(box_frame, bg=COLORS['card_bg'])
        stats_frame.pack(fill='x', padx=20, pady=(0, 15))

        # Package count
        count_col = tk.Frame(stats_frame, bg=COLORS['card_bg'])
        count_col.pack(side='left', expand=True)
        tk.Label(count_col, text="Packages", font=FONT_SMALL, bg=COLORS['card_bg'], fg=COLORS['disabled']).pack()
        self.package_count_var = tk.StringVar(value="0")
        tk.Label(count_col, textvariable=self.package_count_var, font=FONT_LARGE, bg=COLORS['card_bg'], fg=COLORS['fg']).pack()

        # Total weight
        weight_col = tk.Frame(stats_frame, bg=COLORS['card_bg'])
        weight_col.pack(side='left', expand=True)
        tk.Label(weight_col, text="Total Weight", font=FONT_SMALL, bg=COLORS['card_bg'], fg=COLORS['disabled']).pack()
        self.total_weight_var = tk.StringVar(value="0.00 lb")
        tk.Label(weight_col, textvariable=self.total_weight_var, font=FONT_LARGE, bg=COLORS['card_bg'], fg=COLORS['fg']).pack()

        # Status
        status_col = tk.Frame(stats_frame, bg=COLORS['card_bg'])
        status_col.pack(side='left', expand=True)
        tk.Label(status_col, text="Status", font=FONT_SMALL, bg=COLORS['card_bg'], fg=COLORS['disabled']).pack()
        self.box_status_var = tk.StringVar(value="--")
        self.box_status_label = tk.Label(status_col, textvariable=self.box_status_var, font=FONT_MEDIUM, bg=COLORS['card_bg'], fg=COLORS['fg'])
        self.box_status_label.pack()

        # Package list
        list_frame = tk.Frame(main, bg=COLORS['card_bg'], relief='solid', bd=1)
        list_frame.pack(fill='both', expand=True, pady=(0, 15))

        tk.Label(
            list_frame,
            text="PACKAGES IN BOX",
            font=FONT_SMALL,
            bg=COLORS['bg'],
            fg=COLORS['disabled'],
            pady=10
        ).pack(fill='x')

        # Scrollable list
        list_container = tk.Frame(list_frame, bg=COLORS['card_bg'])
        list_container.pack(fill='both', expand=True)

        self.list_canvas = tk.Canvas(list_container, bg=COLORS['card_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient='vertical', command=self.list_canvas.yview)

        self.packages_frame = tk.Frame(self.list_canvas, bg=COLORS['card_bg'])
        self.packages_frame.bind('<Configure>', lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox('all')))

        self.list_canvas.create_window((0, 0), window=self.packages_frame, anchor='nw')
        self.list_canvas.configure(yscrollcommand=scrollbar.set)

        self.list_canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Action buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg'])
        btn_frame.pack(fill='x', pady=(0, 15))

        self.new_box_btn = TouchButton(
            btn_frame,
            text="NEW BOX",
            command=self._on_new_box,
            style='default'
        )
        self.new_box_btn.pack(side='left', expand=True, fill='x', padx=(0, 10), ipady=5)

        self.close_btn = TouchButton(
            btn_frame,
            text="CLOSE & PRINT QR",
            command=self._on_close_box,
            style='success'
        )
        self.close_btn.pack(side='left', expand=True, fill='x', ipady=5)

        # Recent boxes section
        recent_frame = tk.Frame(main, bg=COLORS['card_bg'], relief='solid', bd=1)
        recent_frame.pack(fill='x')

        tk.Label(
            recent_frame,
            text="RECENT BOXES",
            font=FONT_SMALL,
            bg=COLORS['bg'],
            fg=COLORS['disabled'],
            pady=10
        ).pack(fill='x')

        self.recent_list = tk.Frame(recent_frame, bg=COLORS['card_bg'])
        self.recent_list.pack(fill='x', padx=10, pady=(0, 10))

        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side='bottom', fill='x')

    def refresh(self):
        """Refresh box display."""
        self.current_box = get_current_box()

        if self.current_box:
            packages = get_packages_in_box(self.current_box.id)
            total_weight = sum(p.weight_lbs for p in packages)

            self.box_number_var.set(self.current_box.box_number)
            self.package_count_var.set(str(len(packages)))
            self.total_weight_var.set(f"{total_weight:.2f} lb")

            if self.current_box.closed_at:
                self.box_status_var.set("CLOSED")
                self.box_status_label.config(fg=COLORS['success'])
                self.close_btn.config(state='disabled')
            else:
                self.box_status_var.set("OPEN")
                self.box_status_label.config(fg=COLORS['warning'])
                self.close_btn.config(state='normal' if packages else 'disabled')

            # Update package list
            self._update_package_list(packages)
        else:
            self.box_number_var.set("No Active Box")
            self.package_count_var.set("0")
            self.total_weight_var.set("0.00 lb")
            self.box_status_var.set("--")
            self.close_btn.config(state='disabled')
            self._update_package_list([])

    def _update_package_list(self, packages: list[Package]):
        """Update the package list display."""
        for widget in self.packages_frame.winfo_children():
            widget.destroy()

        if not packages:
            tk.Label(
                self.packages_frame,
                text="No packages in box",
                font=FONT_SMALL,
                bg=COLORS['card_bg'],
                fg=COLORS['disabled'],
                pady=20
            ).pack()
            return

        # Header row
        header = tk.Frame(self.packages_frame, bg=COLORS['bg'])
        header.pack(fill='x', padx=10, pady=5)
        tk.Label(header, text="Product", font=FONT_SMALL, bg=COLORS['bg'], fg=COLORS['disabled'], width=25, anchor='w').pack(side='left')
        tk.Label(header, text="SKU", font=FONT_SMALL, bg=COLORS['bg'], fg=COLORS['disabled'], width=8).pack(side='left')
        tk.Label(header, text="Weight", font=FONT_SMALL, bg=COLORS['bg'], fg=COLORS['disabled'], width=10).pack(side='left')
        tk.Label(header, text="Verified", font=FONT_SMALL, bg=COLORS['bg'], fg=COLORS['disabled'], width=8).pack(side='left')

        # Package rows
        for pkg in packages:
            row = tk.Frame(self.packages_frame, bg=COLORS['card_bg'])
            row.pack(fill='x', padx=10, pady=2)

            tk.Label(row, text=pkg.product_name or "Unknown", font=FONT_SMALL, bg=COLORS['card_bg'], fg=COLORS['fg'], width=25, anchor='w').pack(side='left')
            tk.Label(row, text=pkg.product_sku or "", font=FONT_MONO, bg=COLORS['card_bg'], fg=COLORS['fg'], width=8).pack(side='left')
            tk.Label(row, text=f"{pkg.weight_lbs:.2f} lb", font=FONT_MONO, bg=COLORS['card_bg'], fg=COLORS['fg'], width=10).pack(side='left')

            verified_text = "OK" if pkg.verified else "--"
            verified_color = COLORS['success'] if pkg.verified else COLORS['disabled']
            tk.Label(row, text=verified_text, font=FONT_SMALL, bg=COLORS['card_bg'], fg=verified_color, width=8).pack(side='left')

    def _on_new_box(self):
        """Create a new box."""
        box_id = create_box()
        self.status_bar.flash_success("New box created")
        self.refresh()

    def _on_close_box(self):
        """Close current box and print QR label."""
        if not self.current_box:
            return

        packages = get_packages_in_box(self.current_box.id)
        if not packages:
            self.status_bar.flash_error("Cannot close empty box")
            return

        # Update totals
        update_box_totals(self.current_box.id)
        self.current_box = get_box_by_id(self.current_box.id)

        # Generate QR data
        items = [(p.product_sku, p.weight_lbs) for p in packages]
        total_weight = sum(p.weight_lbs for p in packages)
        qr_data = generate_box_qr_data(
            self.current_box.box_number,
            total_weight,
            items
        )

        # Close box in database
        close_box(self.current_box.id, qr_data)

        # Store pending verification data
        self.pending_box_id = self.current_box.id
        self.pending_qr_data = qr_data

        # Generate and print label
        zpl = self.label_gen.box_label(
            box_number=self.current_box.box_number,
            total_weight=total_weight,
            package_count=len(packages),
            qr_data=qr_data
        )

        try:
            self.printer.send_zpl(zpl)
            self.status_bar.set_status(f"Box closed. Scan QR to verify.", 'warning')
        except Exception as e:
            self.status_bar.flash_error(f"Print error: {e}")
            return

        self.refresh()

    def handle_scan(self, event: ScanEvent):
        """Handle QR code scan for box verification."""
        qr_data = event.barcode.strip()

        # Parse QR data
        parsed = parse_box_qr_data(qr_data)
        if not parsed:
            self.status_bar.flash_error("Invalid QR code format")
            play_error_beep()
            return

        # Check if this is pending verification
        if self.pending_box_id and self.pending_qr_data:
            valid, msg = validate_box_qr(qr_data, self.current_box.box_number if self.current_box else None)
            if valid:
                verify_box(self.pending_box_id)
                log_scan('box', self.pending_box_id, qr_data, True)
                show_verification(self, True, f"Box {parsed.box_number} Verified")
                play_success_beep()
                self.status_bar.flash_success("Box verified and sealed")

                # Clear pending state
                self.pending_box_id = None
                self.pending_qr_data = None

                # Create new box for next packages
                create_box()
                self.refresh()
            else:
                log_scan('box', self.pending_box_id, qr_data, False)
                show_verification(self, False, msg)
                play_error_beep()
        else:
            # Just looking up a box
            box = get_box_by_number(parsed.box_number)
            if box:
                if box.verified:
                    self.status_bar.set_status(f"Box {box.box_number}: Verified, {box.package_count} packages, {box.total_weight:.2f} lb")
                else:
                    self.status_bar.set_status(f"Box {box.box_number}: Not verified", 'warning')
            else:
                self.status_bar.flash_error(f"Box not found: {parsed.box_number}")
