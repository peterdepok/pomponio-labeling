"""
Modern box management screen using CustomTkinter.
"""

import customtkinter as ctk
from typing import Optional

from ..database import (
    Box, Package,
    get_current_box, get_box_by_id, get_box_by_number,
    get_packages_in_box, close_box, verify_box, create_box,
    update_box_totals, log_scan
)
from ..barcode import generate_box_qr_data, parse_box_qr_data, validate_box_qr
from ..printer import LabelGenerator, ZebraPrinter, MockPrinter
from ..scanner import ScanEvent, play_success_beep, play_error_beep
from .theme import COLORS, FONTS, SIZES
from .widgets_modern import BigButton, StatusBar, show_verification


class BoxesScreenModern(ctk.CTkFrame):
    """
    Modern box management screen.
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

        self.current_box: Optional[Box] = None
        self.pending_box_id: Optional[int] = None
        self.pending_qr_data: Optional[str] = None

        self._build_ui()
        self.refresh()

    def _build_ui(self):
        """Build UI."""
        # Main content
        main = ctk.CTkFrame(self, fg_color='transparent')
        main.pack(fill='both', expand=True, padx=20, pady=20)

        # Current box card
        box_card = ctk.CTkFrame(
            main,
            fg_color=COLORS['bg_card'],
            corner_radius=SIZES['border_radius_lg']
        )
        box_card.pack(fill='x', pady=(0, 15))

        # Box header
        header = ctk.CTkFrame(box_card, fg_color='transparent')
        header.pack(fill='x', padx=25, pady=20)

        ctk.CTkLabel(
            header,
            text="CURRENT BOX",
            font=FONTS['body_sm'],
            text_color=COLORS['text_muted']
        ).pack(anchor='w')

        self.box_number_label = ctk.CTkLabel(
            header,
            text="No Active Box",
            font=FONTS['heading_xl'],
            text_color=COLORS['text_primary']
        )
        self.box_number_label.pack(anchor='w')

        # Stats row
        stats = ctk.CTkFrame(box_card, fg_color='transparent')
        stats.pack(fill='x', padx=25, pady=(0, 25))

        # Package count
        count_frame = ctk.CTkFrame(stats, fg_color=COLORS['bg_light'], corner_radius=12)
        count_frame.pack(side='left', expand=True, fill='x', padx=(0, 10))

        ctk.CTkLabel(
            count_frame,
            text="Packages",
            font=FONTS['body_md'],
            text_color=COLORS['text_muted']
        ).pack(pady=(15, 5))

        self.count_label = ctk.CTkLabel(
            count_frame,
            text="0",
            font=FONTS['heading_xl'],
            text_color=COLORS['text_primary']
        )
        self.count_label.pack(pady=(0, 15))

        # Total weight
        weight_frame = ctk.CTkFrame(stats, fg_color=COLORS['bg_light'], corner_radius=12)
        weight_frame.pack(side='left', expand=True, fill='x', padx=(0, 10))

        ctk.CTkLabel(
            weight_frame,
            text="Total Weight",
            font=FONTS['body_md'],
            text_color=COLORS['text_muted']
        ).pack(pady=(15, 5))

        self.weight_label = ctk.CTkLabel(
            weight_frame,
            text="0.00 lb",
            font=FONTS['heading_xl'],
            text_color=COLORS['text_primary']
        )
        self.weight_label.pack(pady=(0, 15))

        # Status
        status_frame = ctk.CTkFrame(stats, fg_color=COLORS['bg_light'], corner_radius=12)
        status_frame.pack(side='left', expand=True, fill='x')

        ctk.CTkLabel(
            status_frame,
            text="Status",
            font=FONTS['body_md'],
            text_color=COLORS['text_muted']
        ).pack(pady=(15, 5))

        self.status_label = ctk.CTkLabel(
            status_frame,
            text="--",
            font=FONTS['heading_md'],
            text_color=COLORS['text_primary']
        )
        self.status_label.pack(pady=(0, 15))

        # Package list
        list_card = ctk.CTkFrame(
            main,
            fg_color=COLORS['bg_card'],
            corner_radius=SIZES['border_radius']
        )
        list_card.pack(fill='both', expand=True, pady=(0, 15))

        list_header = ctk.CTkFrame(list_card, fg_color=COLORS['bg_medium'])
        list_header.pack(fill='x')

        ctk.CTkLabel(
            list_header,
            text="PACKAGES IN BOX",
            font=FONTS['body_md'],
            text_color=COLORS['text_secondary']
        ).pack(pady=12)

        # Column headers
        col_header = ctk.CTkFrame(list_card, fg_color='transparent')
        col_header.pack(fill='x', padx=15, pady=10)

        ctk.CTkLabel(col_header, text="Product", font=FONTS['body_sm'], text_color=COLORS['text_muted'], width=250, anchor='w').pack(side='left')
        ctk.CTkLabel(col_header, text="SKU", font=FONTS['body_sm'], text_color=COLORS['text_muted'], width=80).pack(side='left')
        ctk.CTkLabel(col_header, text="Weight", font=FONTS['body_sm'], text_color=COLORS['text_muted'], width=100).pack(side='left')
        ctk.CTkLabel(col_header, text="OK", font=FONTS['body_sm'], text_color=COLORS['text_muted'], width=60).pack(side='right')

        # Scrollable list
        self.package_scroll = ctk.CTkScrollableFrame(list_card, fg_color='transparent')
        self.package_scroll.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Action buttons
        btn_frame = ctk.CTkFrame(main, fg_color='transparent')
        btn_frame.pack(fill='x')

        self.new_btn = BigButton(
            btn_frame,
            text="NEW BOX",
            command=self._on_new_box,
            style='secondary'
        )
        self.new_btn.pack(side='left', expand=True, fill='x', padx=(0, 8))

        self.close_btn = BigButton(
            btn_frame,
            text="CLOSE & PRINT QR",
            command=self._on_close_box,
            style='success',
            size='large'
        )
        self.close_btn.pack(side='left', expand=True, fill='x')

        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side='bottom', fill='x')

    def refresh(self):
        """Refresh box display."""
        self.current_box = get_current_box()

        # Clear list
        for widget in self.package_scroll.winfo_children():
            widget.destroy()

        if self.current_box:
            packages = get_packages_in_box(self.current_box.id)
            total_weight = sum(p.weight_lbs for p in packages)

            self.box_number_label.configure(text=self.current_box.box_number)
            self.count_label.configure(text=str(len(packages)))
            self.weight_label.configure(text=f"{total_weight:.2f} lb")

            if self.current_box.closed_at:
                self.status_label.configure(text="CLOSED", text_color=COLORS['success'])
                self.close_btn.configure(state='disabled')
            else:
                self.status_label.configure(text="OPEN", text_color=COLORS['warning'])
                self.close_btn.configure(state='normal' if packages else 'disabled')

            # Add package rows
            for pkg in packages:
                row = ctk.CTkFrame(self.package_scroll, fg_color='transparent', height=45)
                row.pack(fill='x', pady=3)
                row.pack_propagate(False)

                ctk.CTkLabel(row, text=(pkg.product_name or "Unknown")[:30], font=FONTS['body_md'], text_color=COLORS['text_primary'], width=250, anchor='w').pack(side='left', padx=5)
                ctk.CTkLabel(row, text=pkg.product_sku or "", font=FONTS['mono_sm'], text_color=COLORS['text_secondary'], width=80).pack(side='left')
                ctk.CTkLabel(row, text=f"{pkg.weight_lbs:.2f} lb", font=FONTS['mono_md'], text_color=COLORS['text_primary'], width=100).pack(side='left')

                ok_text = "✓" if pkg.verified else ""
                ok_color = COLORS['success'] if pkg.verified else COLORS['text_muted']
                ctk.CTkLabel(row, text=ok_text, font=FONTS['heading_sm'], text_color=ok_color, width=60).pack(side='right')

            if not packages:
                ctk.CTkLabel(
                    self.package_scroll,
                    text="No packages yet",
                    font=FONTS['body_lg'],
                    text_color=COLORS['text_muted']
                ).pack(pady=40)
        else:
            self.box_number_label.configure(text="No Active Box")
            self.count_label.configure(text="0")
            self.weight_label.configure(text="0.00 lb")
            self.status_label.configure(text="--", text_color=COLORS['text_muted'])
            self.close_btn.configure(state='disabled')

    def _on_new_box(self):
        """Create new box."""
        create_box()
        self.status_bar.flash_success("New box created")
        self.refresh()

    def _on_close_box(self):
        """Close box and print QR."""
        if not self.current_box:
            return

        packages = get_packages_in_box(self.current_box.id)
        if not packages:
            self.status_bar.flash_error("Cannot close empty box")
            return

        update_box_totals(self.current_box.id)
        self.current_box = get_box_by_id(self.current_box.id)

        # Generate QR
        items = [(p.product_sku, p.weight_lbs) for p in packages]
        total_weight = sum(p.weight_lbs for p in packages)
        qr_data = generate_box_qr_data(
            self.current_box.box_number,
            total_weight,
            items
        )

        close_box(self.current_box.id, qr_data)

        self.pending_box_id = self.current_box.id
        self.pending_qr_data = qr_data

        # Print
        zpl = self.label_gen.box_label(
            box_number=self.current_box.box_number,
            total_weight=total_weight,
            package_count=len(packages),
            qr_data=qr_data
        )

        try:
            self.printer.send_zpl(zpl)
            self.status_bar.set_status("Box closed. SCAN QR TO VERIFY", 'warning')
        except Exception as e:
            self.status_bar.flash_error(f"Print error: {e}")

        self.refresh()

    def handle_scan(self, event: ScanEvent):
        """Handle QR scan."""
        qr_data = event.barcode.strip()

        parsed = parse_box_qr_data(qr_data)
        if not parsed:
            self.status_bar.flash_error("Invalid QR format")
            play_error_beep()
            return

        if self.pending_box_id and self.pending_qr_data:
            valid, msg = validate_box_qr(qr_data)
            if valid:
                verify_box(self.pending_box_id)
                log_scan('box', self.pending_box_id, qr_data, True)
                show_verification(self, True, f"Box {parsed.box_number}\nVerified")
                play_success_beep()
                self.status_bar.flash_success("Box sealed")

                self.pending_box_id = None
                self.pending_qr_data = None

                create_box()
                self.refresh()
            else:
                log_scan('box', self.pending_box_id, qr_data, False)
                show_verification(self, False, msg)
                play_error_beep()
        else:
            box = get_box_by_number(parsed.box_number)
            if box:
                status = "Verified" if box.verified else "Not verified"
                self.status_bar.set_status(f"Box {box.box_number}: {status}, {box.package_count} pkgs")
            else:
                self.status_bar.flash_error(f"Box not found: {parsed.box_number}")
