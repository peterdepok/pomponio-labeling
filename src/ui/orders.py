"""
Order completion and pickup screen.
Handles order creation, manifest printing, and pickup verification.
"""

import tkinter as tk
from tkinter import ttk, simpledialog
from typing import Optional
from datetime import datetime

from ..database import (
    Order, Box,
    create_order, get_pending_orders, get_order_by_id,
    get_boxes_for_order, assign_box_to_order, update_order_status,
    get_box_by_number, verify_box, log_scan
)
from ..barcode import parse_box_qr_data
from ..printer import LabelGenerator, ZebraPrinter, MockPrinter
from ..scanner import ScanEvent, play_success_beep, play_error_beep
from .widgets import (
    COLORS, FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_MONO,
    TouchButton, StatusBar, show_verification
)


class OrdersScreen(tk.Frame):
    """
    Order completion and pickup screen.

    Layout:
    +----------------------------------+
    | Order Selection (dropdown)       |
    +----------------------------------+
    | Order Details                    |
    | - Customer, Date, Status         |
    +----------------------------------+
    | Boxes in Order (list)            |
    | - Box number, weight, verified   |
    +----------------------------------+
    | [NEW ORDER] [ASSIGN BOX] [PICKUP]|
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
        self.current_order: Optional[Order] = None
        self.orders: list[Order] = []
        self.pickup_mode: bool = False
        self.scanned_boxes: set[int] = set()

        # Build UI
        self._build_ui()

        # Load data
        self.refresh()

    def _build_ui(self):
        """Build the orders screen UI."""
        # Main container
        main = tk.Frame(self, bg=COLORS['bg'])
        main.pack(fill='both', expand=True, padx=20, pady=20)

        # Order selection section
        select_frame = tk.Frame(main, bg=COLORS['card_bg'], relief='solid', bd=1)
        select_frame.pack(fill='x', pady=(0, 15))

        select_header = tk.Frame(select_frame, bg=COLORS['card_bg'])
        select_header.pack(fill='x', padx=20, pady=15)

        tk.Label(
            select_header,
            text="SELECT ORDER",
            font=FONT_SMALL,
            bg=COLORS['card_bg'],
            fg=COLORS['disabled']
        ).pack(side='left')

        self.order_var = tk.StringVar()
        self.order_dropdown = ttk.Combobox(
            select_header,
            textvariable=self.order_var,
            state='readonly',
            font=FONT_MEDIUM,
            width=40
        )
        self.order_dropdown.pack(side='left', padx=20)
        self.order_dropdown.bind('<<ComboboxSelected>>', self._on_order_selected)

        # Order details section
        details_frame = tk.Frame(main, bg=COLORS['card_bg'], relief='solid', bd=1)
        details_frame.pack(fill='x', pady=(0, 15))

        details_header = tk.Frame(details_frame, bg=COLORS['card_bg'])
        details_header.pack(fill='x', padx=20, pady=15)

        # Customer name
        customer_col = tk.Frame(details_header, bg=COLORS['card_bg'])
        customer_col.pack(side='left', expand=True)
        tk.Label(customer_col, text="Customer", font=FONT_SMALL, bg=COLORS['card_bg'], fg=COLORS['disabled']).pack()
        self.customer_var = tk.StringVar(value="--")
        tk.Label(customer_col, textvariable=self.customer_var, font=FONT_MEDIUM, bg=COLORS['card_bg'], fg=COLORS['fg']).pack()

        # Order date
        date_col = tk.Frame(details_header, bg=COLORS['card_bg'])
        date_col.pack(side='left', expand=True)
        tk.Label(date_col, text="Order Date", font=FONT_SMALL, bg=COLORS['card_bg'], fg=COLORS['disabled']).pack()
        self.date_var = tk.StringVar(value="--")
        tk.Label(date_col, textvariable=self.date_var, font=FONT_MONO, bg=COLORS['card_bg'], fg=COLORS['fg']).pack()

        # Status
        status_col = tk.Frame(details_header, bg=COLORS['card_bg'])
        status_col.pack(side='left', expand=True)
        tk.Label(status_col, text="Status", font=FONT_SMALL, bg=COLORS['card_bg'], fg=COLORS['disabled']).pack()
        self.status_var = tk.StringVar(value="--")
        self.status_label = tk.Label(status_col, textvariable=self.status_var, font=FONT_MEDIUM, bg=COLORS['card_bg'], fg=COLORS['fg'])
        self.status_label.pack()

        # Box count
        boxes_col = tk.Frame(details_header, bg=COLORS['card_bg'])
        boxes_col.pack(side='left', expand=True)
        tk.Label(boxes_col, text="Boxes", font=FONT_SMALL, bg=COLORS['card_bg'], fg=COLORS['disabled']).pack()
        self.box_count_var = tk.StringVar(value="0")
        tk.Label(boxes_col, textvariable=self.box_count_var, font=FONT_LARGE, bg=COLORS['card_bg'], fg=COLORS['fg']).pack()

        # Total weight
        weight_col = tk.Frame(details_header, bg=COLORS['card_bg'])
        weight_col.pack(side='left', expand=True)
        tk.Label(weight_col, text="Total Weight", font=FONT_SMALL, bg=COLORS['card_bg'], fg=COLORS['disabled']).pack()
        self.total_weight_var = tk.StringVar(value="0.00 lb")
        tk.Label(weight_col, textvariable=self.total_weight_var, font=FONT_LARGE, bg=COLORS['card_bg'], fg=COLORS['fg']).pack()

        # Boxes list
        boxes_frame = tk.Frame(main, bg=COLORS['card_bg'], relief='solid', bd=1)
        boxes_frame.pack(fill='both', expand=True, pady=(0, 15))

        tk.Label(
            boxes_frame,
            text="BOXES IN ORDER",
            font=FONT_SMALL,
            bg=COLORS['bg'],
            fg=COLORS['disabled'],
            pady=10
        ).pack(fill='x')

        # Scrollable list
        list_container = tk.Frame(boxes_frame, bg=COLORS['card_bg'])
        list_container.pack(fill='both', expand=True)

        self.list_canvas = tk.Canvas(list_container, bg=COLORS['card_bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient='vertical', command=self.list_canvas.yview)

        self.boxes_frame = tk.Frame(self.list_canvas, bg=COLORS['card_bg'])
        self.boxes_frame.bind('<Configure>', lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox('all')))

        self.list_canvas.create_window((0, 0), window=self.boxes_frame, anchor='nw')
        self.list_canvas.configure(yscrollcommand=scrollbar.set)

        self.list_canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # Action buttons
        btn_frame = tk.Frame(main, bg=COLORS['bg'])
        btn_frame.pack(fill='x', pady=(0, 15))

        self.new_order_btn = TouchButton(
            btn_frame,
            text="NEW ORDER",
            command=self._on_new_order,
            style='default'
        )
        self.new_order_btn.pack(side='left', expand=True, fill='x', padx=(0, 5), ipady=5)

        self.print_manifest_btn = TouchButton(
            btn_frame,
            text="PRINT MANIFEST",
            command=self._on_print_manifest,
            style='default'
        )
        self.print_manifest_btn.pack(side='left', expand=True, fill='x', padx=5, ipady=5)

        self.pickup_btn = TouchButton(
            btn_frame,
            text="START PICKUP",
            command=self._on_start_pickup,
            style='success'
        )
        self.pickup_btn.pack(side='left', expand=True, fill='x', padx=(5, 0), ipady=5)

        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side='bottom', fill='x')

    def refresh(self):
        """Refresh orders list and display."""
        self.orders = get_pending_orders()

        # Update dropdown
        order_options = [f"{o.customer_name} ({o.order_date})" for o in self.orders]
        self.order_dropdown['values'] = order_options

        if self.current_order:
            # Keep current selection if still valid
            for i, o in enumerate(self.orders):
                if o.id == self.current_order.id:
                    self.order_dropdown.current(i)
                    self._load_order(self.current_order.id)
                    return

        # Select first order if available
        if self.orders:
            self.order_dropdown.current(0)
            self._load_order(self.orders[0].id)
        else:
            self._clear_display()

    def _on_order_selected(self, event):
        """Handle order selection from dropdown."""
        selection = self.order_dropdown.current()
        if selection >= 0 and selection < len(self.orders):
            self._load_order(self.orders[selection].id)

    def _load_order(self, order_id: int):
        """Load and display order details."""
        self.current_order = get_order_by_id(order_id)
        if not self.current_order:
            self._clear_display()
            return

        boxes = get_boxes_for_order(order_id)
        total_weight = sum(b.total_weight for b in boxes)

        self.customer_var.set(self.current_order.customer_name)
        self.date_var.set(str(self.current_order.order_date))
        self.status_var.set(self.current_order.status.upper())
        self.box_count_var.set(str(len(boxes)))
        self.total_weight_var.set(f"{total_weight:.2f} lb")

        # Status color
        status_colors = {
            'pending': COLORS['warning'],
            'ready': COLORS['primary'],
            'picked_up': COLORS['success']
        }
        self.status_label.config(fg=status_colors.get(self.current_order.status, COLORS['fg']))

        # Update boxes list
        self._update_boxes_list(boxes)

        # Update button states
        self.print_manifest_btn.config(state='normal' if boxes else 'disabled')
        self.pickup_btn.config(state='normal' if boxes and self.current_order.status != 'picked_up' else 'disabled')

    def _clear_display(self):
        """Clear the display when no order selected."""
        self.current_order = None
        self.customer_var.set("--")
        self.date_var.set("--")
        self.status_var.set("--")
        self.box_count_var.set("0")
        self.total_weight_var.set("0.00 lb")
        self._update_boxes_list([])
        self.print_manifest_btn.config(state='disabled')
        self.pickup_btn.config(state='disabled')

    def _update_boxes_list(self, boxes: list[Box]):
        """Update the boxes list display."""
        for widget in self.boxes_frame.winfo_children():
            widget.destroy()

        if not boxes:
            tk.Label(
                self.boxes_frame,
                text="No boxes assigned to this order",
                font=FONT_SMALL,
                bg=COLORS['card_bg'],
                fg=COLORS['disabled'],
                pady=20
            ).pack()
            return

        # Header row
        header = tk.Frame(self.boxes_frame, bg=COLORS['bg'])
        header.pack(fill='x', padx=10, pady=5)
        tk.Label(header, text="Box Number", font=FONT_SMALL, bg=COLORS['bg'], fg=COLORS['disabled'], width=20, anchor='w').pack(side='left')
        tk.Label(header, text="Packages", font=FONT_SMALL, bg=COLORS['bg'], fg=COLORS['disabled'], width=10).pack(side='left')
        tk.Label(header, text="Weight", font=FONT_SMALL, bg=COLORS['bg'], fg=COLORS['disabled'], width=12).pack(side='left')
        tk.Label(header, text="Scanned", font=FONT_SMALL, bg=COLORS['bg'], fg=COLORS['disabled'], width=10).pack(side='left')

        # Box rows
        for box in boxes:
            row = tk.Frame(self.boxes_frame, bg=COLORS['card_bg'])
            row.pack(fill='x', padx=10, pady=2)

            tk.Label(row, text=box.box_number, font=FONT_MONO, bg=COLORS['card_bg'], fg=COLORS['fg'], width=20, anchor='w').pack(side='left')
            tk.Label(row, text=str(box.package_count), font=FONT_MONO, bg=COLORS['card_bg'], fg=COLORS['fg'], width=10).pack(side='left')
            tk.Label(row, text=f"{box.total_weight:.2f} lb", font=FONT_MONO, bg=COLORS['card_bg'], fg=COLORS['fg'], width=12).pack(side='left')

            # Scanned indicator (for pickup mode)
            scanned = box.id in self.scanned_boxes
            scanned_text = "OK" if scanned else ("--" if not self.pickup_mode else "SCAN")
            scanned_color = COLORS['success'] if scanned else COLORS['disabled']
            tk.Label(row, text=scanned_text, font=FONT_SMALL, bg=COLORS['card_bg'], fg=scanned_color, width=10).pack(side='left')

    def _on_new_order(self):
        """Create a new order."""
        # Simple dialog for customer name
        customer = simpledialog.askstring(
            "New Order",
            "Enter customer name:",
            parent=self
        )
        if customer:
            order_id = create_order(customer.strip())
            self.status_bar.flash_success(f"Order created for {customer}")
            self.refresh()
            # Select the new order
            for i, o in enumerate(self.orders):
                if o.id == order_id:
                    self.order_dropdown.current(i)
                    self._load_order(order_id)
                    break

    def _on_print_manifest(self):
        """Print order manifest."""
        if not self.current_order:
            return

        boxes = get_boxes_for_order(self.current_order.id)
        if not boxes:
            self.status_bar.flash_error("No boxes in order")
            return

        total_weight = sum(b.total_weight for b in boxes)
        box_numbers = [b.box_number for b in boxes]

        zpl = self.label_gen.manifest_label(
            order_id=self.current_order.id,
            customer_name=self.current_order.customer_name,
            box_count=len(boxes),
            total_weight=total_weight,
            box_numbers=box_numbers
        )

        try:
            self.printer.send_zpl(zpl)
            self.status_bar.flash_success("Manifest printed")
            update_order_status(self.current_order.id, 'ready')
            self.refresh()
        except Exception as e:
            self.status_bar.flash_error(f"Print error: {e}")

    def _on_start_pickup(self):
        """Start pickup verification mode."""
        if not self.current_order:
            return

        boxes = get_boxes_for_order(self.current_order.id)
        if not boxes:
            self.status_bar.flash_error("No boxes in order")
            return

        self.pickup_mode = True
        self.scanned_boxes.clear()
        self.pickup_btn.config(text="COMPLETE PICKUP", command=self._on_complete_pickup)
        self.status_bar.set_status(f"Scan {len(boxes)} boxes to verify pickup", 'warning')

        # Refresh to show scan indicators
        self._load_order(self.current_order.id)

    def _on_complete_pickup(self):
        """Complete pickup if all boxes scanned."""
        if not self.current_order:
            return

        boxes = get_boxes_for_order(self.current_order.id)
        unscanned = [b for b in boxes if b.id not in self.scanned_boxes]

        if unscanned:
            self.status_bar.flash_error(f"{len(unscanned)} boxes not scanned")
            return

        # Mark order complete
        update_order_status(self.current_order.id, 'picked_up')

        show_verification(self, True, f"Order Complete\\n{len(boxes)} boxes picked up")
        play_success_beep()

        # Reset pickup mode
        self.pickup_mode = False
        self.scanned_boxes.clear()
        self.pickup_btn.config(text="START PICKUP", command=self._on_start_pickup)

        self.status_bar.flash_success("Order marked as picked up")
        self.refresh()

    def handle_scan(self, event: ScanEvent):
        """Handle QR code scan for pickup verification."""
        qr_data = event.barcode.strip()

        # Parse QR data
        parsed = parse_box_qr_data(qr_data)
        if not parsed:
            self.status_bar.flash_error("Invalid QR code format")
            play_error_beep()
            return

        # Look up box
        box = get_box_by_number(parsed.box_number)
        if not box:
            self.status_bar.flash_error(f"Box not found: {parsed.box_number}")
            play_error_beep()
            return

        if self.pickup_mode and self.current_order:
            # Verify box belongs to this order
            if box.order_id != self.current_order.id:
                self.status_bar.flash_error(f"Box {box.box_number} is not in this order")
                play_error_beep()
                log_scan('pickup', box.id, qr_data, False)
                return

            # Mark as scanned
            self.scanned_boxes.add(box.id)
            log_scan('pickup', box.id, qr_data, True)
            play_success_beep()

            boxes = get_boxes_for_order(self.current_order.id)
            remaining = len(boxes) - len(self.scanned_boxes)

            if remaining > 0:
                self.status_bar.set_status(f"Box scanned. {remaining} more to scan.", 'success')
            else:
                self.status_bar.set_status("All boxes scanned. Press Complete Pickup.", 'success')

            # Refresh display
            self._load_order(self.current_order.id)
        else:
            # Just info lookup
            if box.order_id:
                order = get_order_by_id(box.order_id)
                self.status_bar.set_status(f"Box {box.box_number}: Order for {order.customer_name if order else 'Unknown'}")
            else:
                self.status_bar.set_status(f"Box {box.box_number}: Not assigned to order")

    def assign_box_to_current_order(self, box_id: int):
        """Assign a box to the current order."""
        if not self.current_order:
            self.status_bar.flash_error("No order selected")
            return

        assign_box_to_order(box_id, self.current_order.id)
        self.status_bar.flash_success("Box assigned to order")
        self._load_order(self.current_order.id)
