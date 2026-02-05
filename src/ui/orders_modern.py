"""
Modern order management screen using CustomTkinter.
"""

import customtkinter as ctk
import webbrowser
import os
from pathlib import Path
from typing import Optional
from datetime import datetime

from ..database import (
    Order, Box,
    create_order, get_pending_orders, get_order_by_id,
    get_boxes_for_order, assign_box_to_order, update_order_status,
    get_box_by_number, log_scan
)
from ..barcode import parse_box_qr_data
from ..printer import LabelGenerator, ZebraPrinter, MockPrinter
from ..scanner import ScanEvent, play_success_beep, play_error_beep
from ..manifest import (
    generate_manifest, manifest_to_html, generate_zpl_manifest,
    save_manifest_pdf, auto_send_manifest, load_manifest_config
)
from .theme import COLORS, FONTS, SIZES
from .widgets_modern import BigButton, StatusBar, show_verification


class OrdersScreenModern(ctk.CTkFrame):
    """
    Modern order management screen.
    """

    def __init__(
        self,
        parent,
        printer: Optional[ZebraPrinter] = None,
        **kwargs
    ):
        super().__init__(parent, fg_color=COLORS['bg_dark'], **kwargs)

        self.printer = printer or MockPrinter()
        self.label_gen = LabelGenerator()

        self.orders: list[Order] = []
        self.current_order: Optional[Order] = None
        self.pickup_mode: bool = False
        self.scanned_boxes: set[int] = set()

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """Build UI."""
        main = ctk.CTkFrame(self, fg_color='transparent')
        main.pack(fill='both', expand=True, padx=20, pady=20)

        # Order selection
        select_card = ctk.CTkFrame(main, fg_color=COLORS['bg_card'], corner_radius=SIZES['border_radius'])
        select_card.pack(fill='x', pady=(0, 15))

        select_inner = ctk.CTkFrame(select_card, fg_color='transparent')
        select_inner.pack(fill='x', padx=20, pady=15)

        ctk.CTkLabel(
            select_inner,
            text="SELECT ORDER",
            font=FONTS['body_sm'],
            text_color=COLORS['text_muted']
        ).pack(side='left')

        self.order_menu = ctk.CTkOptionMenu(
            select_inner,
            values=["No orders"],
            font=FONTS['body_lg'],
            dropdown_font=FONTS['body_md'],
            width=400,
            height=50,
            command=self._on_order_selected
        )
        self.order_menu.pack(side='left', padx=20)

        self.new_order_btn = BigButton(
            select_inner,
            text="+ NEW ORDER",
            command=self._on_new_order,
            style='primary'
        )
        self.new_order_btn.pack(side='right')

        # Order details
        details_card = ctk.CTkFrame(main, fg_color=COLORS['bg_card'], corner_radius=SIZES['border_radius'])
        details_card.pack(fill='x', pady=(0, 15))

        details_inner = ctk.CTkFrame(details_card, fg_color='transparent')
        details_inner.pack(fill='x', padx=25, pady=20)

        # Customer
        cust_frame = ctk.CTkFrame(details_inner, fg_color='transparent')
        cust_frame.pack(side='left', expand=True)

        ctk.CTkLabel(cust_frame, text="Customer", font=FONTS['body_sm'], text_color=COLORS['text_muted']).pack()
        self.customer_label = ctk.CTkLabel(cust_frame, text="--", font=FONTS['heading_md'], text_color=COLORS['text_primary'])
        self.customer_label.pack()

        # Date
        date_frame = ctk.CTkFrame(details_inner, fg_color='transparent')
        date_frame.pack(side='left', expand=True)

        ctk.CTkLabel(date_frame, text="Date", font=FONTS['body_sm'], text_color=COLORS['text_muted']).pack()
        self.date_label = ctk.CTkLabel(date_frame, text="--", font=FONTS['mono_md'], text_color=COLORS['text_primary'])
        self.date_label.pack()

        # Status
        status_frame = ctk.CTkFrame(details_inner, fg_color='transparent')
        status_frame.pack(side='left', expand=True)

        ctk.CTkLabel(status_frame, text="Status", font=FONTS['body_sm'], text_color=COLORS['text_muted']).pack()
        self.order_status_label = ctk.CTkLabel(status_frame, text="--", font=FONTS['heading_sm'], text_color=COLORS['text_primary'])
        self.order_status_label.pack()

        # Boxes
        boxes_frame = ctk.CTkFrame(details_inner, fg_color='transparent')
        boxes_frame.pack(side='left', expand=True)

        ctk.CTkLabel(boxes_frame, text="Boxes", font=FONTS['body_sm'], text_color=COLORS['text_muted']).pack()
        self.boxes_count_label = ctk.CTkLabel(boxes_frame, text="0", font=FONTS['heading_lg'], text_color=COLORS['text_primary'])
        self.boxes_count_label.pack()

        # Weight
        weight_frame = ctk.CTkFrame(details_inner, fg_color='transparent')
        weight_frame.pack(side='left', expand=True)

        ctk.CTkLabel(weight_frame, text="Weight", font=FONTS['body_sm'], text_color=COLORS['text_muted']).pack()
        self.total_weight_label = ctk.CTkLabel(weight_frame, text="0.00 lb", font=FONTS['heading_lg'], text_color=COLORS['text_primary'])
        self.total_weight_label.pack()

        # Boxes list
        list_card = ctk.CTkFrame(main, fg_color=COLORS['bg_card'], corner_radius=SIZES['border_radius'])
        list_card.pack(fill='both', expand=True, pady=(0, 15))

        list_header = ctk.CTkFrame(list_card, fg_color=COLORS['bg_medium'])
        list_header.pack(fill='x')

        ctk.CTkLabel(list_header, text="BOXES IN ORDER", font=FONTS['body_md'], text_color=COLORS['text_secondary']).pack(pady=12)

        # Column headers
        col_header = ctk.CTkFrame(list_card, fg_color='transparent')
        col_header.pack(fill='x', padx=15, pady=10)

        ctk.CTkLabel(col_header, text="Box Number", font=FONTS['body_sm'], text_color=COLORS['text_muted'], width=200, anchor='w').pack(side='left')
        ctk.CTkLabel(col_header, text="Packages", font=FONTS['body_sm'], text_color=COLORS['text_muted'], width=100).pack(side='left')
        ctk.CTkLabel(col_header, text="Weight", font=FONTS['body_sm'], text_color=COLORS['text_muted'], width=120).pack(side='left')
        ctk.CTkLabel(col_header, text="Scanned", font=FONTS['body_sm'], text_color=COLORS['text_muted'], width=100).pack(side='right')

        self.boxes_scroll = ctk.CTkScrollableFrame(list_card, fg_color='transparent')
        self.boxes_scroll.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Action buttons
        btn_frame = ctk.CTkFrame(main, fg_color='transparent')
        btn_frame.pack(fill='x')

        self.manifest_btn = BigButton(
            btn_frame,
            text="PRINT MANIFEST",
            command=self._on_print_manifest,
            style='secondary',
            state='disabled'
        )
        self.manifest_btn.pack(side='left', expand=True, fill='x', padx=(0, 8))

        self.email_btn = BigButton(
            btn_frame,
            text="EMAIL TO OFFICE",
            command=self._on_email_manifest,
            style='primary',
            state='disabled'
        )
        self.email_btn.pack(side='left', expand=True, fill='x', padx=(0, 8))

        self.pickup_btn = BigButton(
            btn_frame,
            text="START PICKUP",
            command=self._on_pickup,
            style='success',
            size='large',
            state='disabled'
        )
        self.pickup_btn.pack(side='left', expand=True, fill='x')

        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side='bottom', fill='x')

    def refresh(self):
        """Refresh orders."""
        self.orders = get_pending_orders()

        if self.orders:
            options = [f"{o.customer_name} ({o.order_date})" for o in self.orders]
            self.order_menu.configure(values=options)

            # Keep selection or select first
            if self.current_order:
                for i, o in enumerate(self.orders):
                    if o.id == self.current_order.id:
                        self.order_menu.set(options[i])
                        self._load_order(o.id)
                        return

            self.order_menu.set(options[0])
            self._load_order(self.orders[0].id)
        else:
            self.order_menu.configure(values=["No orders"])
            self.order_menu.set("No orders")
            self._clear_display()

    def _on_order_selected(self, selection: str):
        """Handle order selection."""
        for i, o in enumerate(self.orders):
            label = f"{o.customer_name} ({o.order_date})"
            if label == selection:
                self._load_order(o.id)
                return

    def _load_order(self, order_id: int):
        """Load order details."""
        self.current_order = get_order_by_id(order_id)
        if not self.current_order:
            self._clear_display()
            return

        boxes = get_boxes_for_order(order_id)
        total_weight = sum(b.total_weight for b in boxes)

        self.customer_label.configure(text=self.current_order.customer_name)
        self.date_label.configure(text=str(self.current_order.order_date))
        self.order_status_label.configure(text=self.current_order.status.upper())
        self.boxes_count_label.configure(text=str(len(boxes)))
        self.total_weight_label.configure(text=f"{total_weight:.2f} lb")

        # Status color
        colors = {'pending': COLORS['warning'], 'ready': COLORS['primary'], 'picked_up': COLORS['success']}
        self.order_status_label.configure(text_color=colors.get(self.current_order.status, COLORS['text_primary']))

        # Update boxes list
        for widget in self.boxes_scroll.winfo_children():
            widget.destroy()

        if boxes:
            for box in boxes:
                row = ctk.CTkFrame(self.boxes_scroll, fg_color='transparent', height=50)
                row.pack(fill='x', pady=3)
                row.pack_propagate(False)

                ctk.CTkLabel(row, text=box.box_number, font=FONTS['mono_md'], text_color=COLORS['text_primary'], width=200, anchor='w').pack(side='left', padx=5)
                ctk.CTkLabel(row, text=str(box.package_count), font=FONTS['body_lg'], text_color=COLORS['text_secondary'], width=100).pack(side='left')
                ctk.CTkLabel(row, text=f"{box.total_weight:.2f} lb", font=FONTS['mono_md'], text_color=COLORS['text_primary'], width=120).pack(side='left')

                scanned = box.id in self.scanned_boxes
                scan_text = "✓" if scanned else ("SCAN" if self.pickup_mode else "--")
                scan_color = COLORS['success'] if scanned else COLORS['text_muted']
                ctk.CTkLabel(row, text=scan_text, font=FONTS['body_lg'], text_color=scan_color, width=100).pack(side='right')

            self.manifest_btn.configure(state='normal')
            self.email_btn.configure(state='normal')
            self.pickup_btn.configure(state='normal' if self.current_order.status != 'picked_up' else 'disabled')
        else:
            ctk.CTkLabel(
                self.boxes_scroll,
                text="No boxes assigned",
                font=FONTS['body_lg'],
                text_color=COLORS['text_muted']
            ).pack(pady=40)

            self.manifest_btn.configure(state='disabled')
            self.email_btn.configure(state='disabled')
            self.pickup_btn.configure(state='disabled')

    def _clear_display(self):
        """Clear display."""
        self.current_order = None
        self.customer_label.configure(text="--")
        self.date_label.configure(text="--")
        self.order_status_label.configure(text="--")
        self.boxes_count_label.configure(text="0")
        self.total_weight_label.configure(text="0.00 lb")

        for widget in self.boxes_scroll.winfo_children():
            widget.destroy()

        self.manifest_btn.configure(state='disabled')
        self.pickup_btn.configure(state='disabled')

    def _on_new_order(self):
        """Create new order."""
        dialog = ctk.CTkInputDialog(
            text="Customer name:",
            title="New Order"
        )
        customer = dialog.get_input()
        if customer:
            order_id = create_order(customer.strip())
            self.status_bar.flash_success(f"Order created: {customer}")
            self.refresh()
            for i, o in enumerate(self.orders):
                if o.id == order_id:
                    self._load_order(order_id)
                    break

    def _on_print_manifest(self):
        """Print manifest label and save detailed manifest."""
        if not self.current_order:
            return

        # Generate detailed manifest
        manifest = generate_manifest(self.current_order.id)
        if not manifest:
            self.status_bar.flash_error("Could not generate manifest")
            return

        # Save HTML manifest locally
        data_dir = Path(__file__).parent.parent.parent / "data" / "manifests"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = data_dir / f"manifest_{self.current_order.id}_{timestamp}.html"
        save_manifest_pdf(manifest, html_path)

        # Generate and print summary label
        zpl = generate_zpl_manifest(manifest)

        try:
            self.printer.send_zpl(zpl)
            self.status_bar.flash_success("Manifest printed and saved")
            update_order_status(self.current_order.id, 'ready')

            # Open HTML for back office printing
            if html_path.exists():
                webbrowser.open(f'file://{html_path}')

            self.refresh()
        except Exception as e:
            self.status_bar.flash_error(f"Print error: {e}")

    def _on_email_manifest(self):
        """Email manifest to back office."""
        if not self.current_order:
            return

        config = load_manifest_config()
        if not config.enabled:
            self.status_bar.flash_error("Email not configured. Check config.ini")
            return

        self.status_bar.set_status("Sending email...", 'warning')

        try:
            if auto_send_manifest(self.current_order.id):
                self.status_bar.flash_success(f"Manifest sent to {config.back_office_email}")
                update_order_status(self.current_order.id, 'ready')
                self.refresh()
            else:
                self.status_bar.flash_error("Email send failed")
        except Exception as e:
            self.status_bar.flash_error(f"Email error: {e}")

    def _on_pickup(self):
        """Toggle pickup mode."""
        if not self.pickup_mode:
            # Start pickup
            boxes = get_boxes_for_order(self.current_order.id) if self.current_order else []
            if not boxes:
                return

            self.pickup_mode = True
            self.scanned_boxes.clear()
            self.pickup_btn.configure(text="COMPLETE PICKUP")
            self.status_bar.set_status(f"Scan {len(boxes)} boxes", 'warning')
            self._load_order(self.current_order.id)
        else:
            # Complete pickup
            boxes = get_boxes_for_order(self.current_order.id) if self.current_order else []
            unscanned = [b for b in boxes if b.id not in self.scanned_boxes]

            if unscanned:
                self.status_bar.flash_error(f"{len(unscanned)} boxes not scanned")
                return

            update_order_status(self.current_order.id, 'picked_up')
            show_verification(self, True, f"Order Complete\n{len(boxes)} boxes")
            play_success_beep()

            self.pickup_mode = False
            self.scanned_boxes.clear()
            self.pickup_btn.configure(text="START PICKUP")
            self.status_bar.flash_success("Order picked up")
            self.refresh()

    def handle_scan(self, event: ScanEvent):
        """Handle QR scan."""
        qr_data = event.barcode.strip()

        parsed = parse_box_qr_data(qr_data)
        if not parsed:
            self.status_bar.flash_error("Invalid QR format")
            play_error_beep()
            return

        box = get_box_by_number(parsed.box_number)
        if not box:
            self.status_bar.flash_error(f"Box not found: {parsed.box_number}")
            play_error_beep()
            return

        if self.pickup_mode and self.current_order:
            if box.order_id != self.current_order.id:
                self.status_bar.flash_error(f"Box not in this order")
                play_error_beep()
                log_scan('pickup', box.id, qr_data, False)
                return

            self.scanned_boxes.add(box.id)
            log_scan('pickup', box.id, qr_data, True)
            play_success_beep()

            boxes = get_boxes_for_order(self.current_order.id)
            remaining = len(boxes) - len(self.scanned_boxes)

            if remaining > 0:
                self.status_bar.set_status(f"Scanned. {remaining} more", 'success')
            else:
                self.status_bar.set_status("All scanned. Press Complete.", 'success')

            self._load_order(self.current_order.id)
        else:
            if box.order_id:
                order = get_order_by_id(box.order_id)
                self.status_bar.set_status(f"Box {box.box_number}: {order.customer_name if order else 'Unknown'}")
            else:
                self.status_bar.set_status(f"Box {box.box_number}: Not assigned")
