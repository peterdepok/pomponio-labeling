"""
Modern, bullet-proof labeling screen with enforced workflow.
Clean design optimized for touchscreen line workers.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Optional

from ..database import (
    Product,
    get_products_by_category,
    create_package, verify_package, get_package_by_barcode,
    get_current_box, create_box, assign_package_to_box, update_box_totals,
    get_packages_in_box, log_scan
)
from ..barcode import generate_package_barcode, validate_package_barcode
from ..printer import LabelGenerator, ZebraPrinter, MockPrinter
from ..scale import Scale, MockScale, WeightReading
from ..scanner import ScanEvent, play_success_beep, play_error_beep
from ..safety import WorkflowGuard, WorkflowState, WeightValidator, BarcodeValidator
from .theme import COLORS, FONTS, SIZES, CATEGORY_COLORS
from .widgets_modern import (
    BigButton, ProductCard, WeightDisplay, StatusBar,
    BoxSummaryCard, PackageListItem, CategoryTab, show_verification
)
from .dialogs import alert, confirm, CountdownOverlay


class SafeLabelingScreen(ctk.CTkFrame):
    """
    Modern labeling screen with enforced workflow.

    Features:
    - Clean, minimal design
    - Large touch targets (80px+ buttons)
    - Clear visual feedback
    - Enforced step sequence
    - Weight validation
    - Scan timeout protection
    """

    SCAN_TIMEOUT = 30

    def __init__(
        self,
        parent,
        scale: Optional[Scale] = None,
        printer: Optional[ZebraPrinter] = None,
        **kwargs
    ):
        super().__init__(parent, fg_color=COLORS['bg_dark'], **kwargs)

        # Hardware
        self.scale = scale or MockScale()
        self.printer = printer or MockPrinter()
        self.label_gen = LabelGenerator()

        # Safety
        self.workflow = WorkflowGuard()
        self.weight_validator = WeightValidator()
        self.barcode_validator = BarcodeValidator()

        # State
        self.selected_product: Optional[Product] = None
        self.captured_weight: Optional[float] = None
        self.pending_package_id: Optional[int] = None
        self.pending_barcode: Optional[str] = None
        self.products_by_category: dict = {}
        self.product_cards: dict[int, ProductCard] = {}
        self.category_tabs: dict[str, CategoryTab] = {}
        self.current_category: Optional[str] = None
        self._scan_time_remaining: int = 0

        self._build_ui()
        self._load_products()
        self._load_current_box()
        self._setup_scale()
        self._update_ui_state()

    def _build_ui(self):
        """Build modern UI layout."""

        # Main horizontal split
        main = ctk.CTkFrame(self, fg_color='transparent')
        main.pack(fill='both', expand=True)

        # ===== LEFT SIDE: Product Selection =====
        left = ctk.CTkFrame(main, fg_color='transparent')
        left.pack(side='left', fill='both', expand=True, padx=(20, 10), pady=20)

        # Category tabs
        self.tabs_frame = ctk.CTkFrame(left, fg_color='transparent', height=70)
        self.tabs_frame.pack(fill='x')
        self.tabs_frame.pack_propagate(False)

        self.tabs_scroll = ctk.CTkScrollableFrame(
            self.tabs_frame,
            fg_color='transparent',
            orientation='horizontal',
            height=60
        )
        self.tabs_scroll.pack(fill='both', expand=True)

        # Product grid
        self.grid_scroll = ctk.CTkScrollableFrame(
            left,
            fg_color=COLORS['bg_medium'],
            corner_radius=SIZES['border_radius_lg']
        )
        self.grid_scroll.pack(fill='both', expand=True, pady=(12, 0))

        # ===== RIGHT SIDE: Controls =====
        right = ctk.CTkFrame(main, fg_color='transparent', width=420)
        right.pack(side='right', fill='y', padx=(10, 20), pady=20)
        right.pack_propagate(False)

        # Selected product display
        self.selected_frame = ctk.CTkFrame(
            right,
            fg_color=COLORS['bg_card'],
            corner_radius=SIZES['border_radius']
        )
        self.selected_frame.pack(fill='x')

        selected_inner = ctk.CTkFrame(self.selected_frame, fg_color='transparent')
        selected_inner.pack(fill='x', padx=24, pady=20)

        ctk.CTkLabel(
            selected_inner,
            text="SELECTED",
            font=FONTS['label'],
            text_color=COLORS['text_muted']
        ).pack(anchor='w')

        self.selected_name = ctk.CTkLabel(
            selected_inner,
            text="Tap a product to begin",
            font=FONTS['heading_md'],
            text_color=COLORS['text_muted'],
            wraplength=360,
            anchor='w',
            justify='left'
        )
        self.selected_name.pack(anchor='w', pady=(8, 4))

        self.selected_price = ctk.CTkLabel(
            selected_inner,
            text="",
            font=FONTS['body_lg'],
            text_color=COLORS['text_secondary']
        )
        self.selected_price.pack(anchor='w')

        # Spacer
        ctk.CTkFrame(right, fg_color='transparent', height=16).pack()

        # Weight display
        self.weight_display = WeightDisplay(right)
        self.weight_display.pack(fill='x')

        # Spacer
        ctk.CTkFrame(right, fg_color='transparent', height=16).pack()

        # Action buttons container
        self.actions_frame = ctk.CTkFrame(right, fg_color='transparent')
        self.actions_frame.pack(fill='x')

        # Lock weight button
        self.lock_weight_btn = BigButton(
            self.actions_frame,
            text="Lock Weight",
            command=self._on_lock_weight,
            style='primary',
            size='large'
        )
        self.lock_weight_btn.pack(fill='x')
        self.lock_weight_btn.configure(state='disabled')

        # Locked weight indicator (hidden initially)
        self.locked_indicator = ctk.CTkFrame(
            self.actions_frame,
            fg_color=COLORS['success_bg'],
            corner_radius=SIZES['border_radius']
        )

        locked_inner = ctk.CTkFrame(self.locked_indicator, fg_color='transparent')
        locked_inner.pack(fill='x', padx=20, pady=16)

        self.locked_weight_label = ctk.CTkLabel(
            locked_inner,
            text="0.00 lb",
            font=FONTS['heading_lg'],
            text_color=COLORS['success']
        )
        self.locked_weight_label.pack(side='left')

        ctk.CTkLabel(
            locked_inner,
            text="LOCKED",
            font=FONTS['button_sm'],
            text_color=COLORS['success']
        ).pack(side='right')

        # Spacer
        ctk.CTkFrame(right, fg_color='transparent', height=16).pack()

        # Print button
        self.print_btn = BigButton(
            right,
            text="Print Label",
            command=self._on_print,
            style='success',
            size='large'
        )
        self.print_btn.pack(fill='x')
        self.print_btn.configure(state='disabled')

        # Scan prompt (hidden initially)
        self.scan_frame = ctk.CTkFrame(
            right,
            fg_color=COLORS['warning_bg'],
            corner_radius=SIZES['border_radius']
        )

        scan_inner = ctk.CTkFrame(self.scan_frame, fg_color='transparent')
        scan_inner.pack(fill='both', expand=True, padx=24, pady=24)

        ctk.CTkLabel(
            scan_inner,
            text="SCAN LABEL NOW",
            font=FONTS['heading_md'],
            text_color=COLORS['warning']
        ).pack()

        self.scan_timer_label = ctk.CTkLabel(
            scan_inner,
            text="30",
            font=FONTS['heading_xl'],
            text_color=COLORS['warning']
        )
        self.scan_timer_label.pack(pady=(8, 16))

        ctk.CTkButton(
            scan_inner,
            text="REPRINT",
            font=FONTS['button_sm'],
            fg_color=COLORS['bg_elevated'],
            hover_color=COLORS['bg_light'],
            height=48,
            corner_radius=SIZES['border_radius_sm'],
            command=self._on_reprint
        ).pack(fill='x')

        # Spacer
        ctk.CTkFrame(right, fg_color='transparent', height=16).pack()

        # Box summary
        self.box_summary = BoxSummaryCard(right)
        self.box_summary.pack(fill='x')

        # Package list
        self.package_list_frame = ctk.CTkFrame(
            right,
            fg_color=COLORS['bg_card'],
            corner_radius=SIZES['border_radius']
        )
        self.package_list_frame.pack(fill='both', expand=True, pady=(16, 0))

        list_inner = ctk.CTkFrame(self.package_list_frame, fg_color='transparent')
        list_inner.pack(fill='both', expand=True, padx=16, pady=16)

        ctk.CTkLabel(
            list_inner,
            text="PACKAGES IN BOX",
            font=FONTS['label'],
            text_color=COLORS['text_muted']
        ).pack(anchor='w')

        self.package_scroll = ctk.CTkScrollableFrame(
            list_inner,
            fg_color='transparent'
        )
        self.package_scroll.pack(fill='both', expand=True, pady=(8, 0))

        # Status bar at bottom
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side='bottom', fill='x')

    def _update_ui_state(self):
        """Update UI based on workflow state."""
        state = self.workflow.state

        # Hide all conditional elements first
        self.locked_indicator.pack_forget()
        self.scan_frame.pack_forget()

        # Show appropriate UI for state
        if state == WorkflowState.IDLE:
            self.lock_weight_btn.pack(fill='x', in_=self.actions_frame)
            self.lock_weight_btn.configure(state='disabled')
            self.print_btn.configure(state='disabled')

        elif state == WorkflowState.PRODUCT_SELECTED:
            self.lock_weight_btn.pack(fill='x', in_=self.actions_frame)
            stable = self.weight_validator.get_stable_weight()
            self.lock_weight_btn.configure(state='normal' if stable else 'disabled')
            self.print_btn.configure(state='disabled')

        elif state == WorkflowState.WEIGHT_CAPTURED:
            self.lock_weight_btn.pack_forget()
            self.locked_indicator.pack(fill='x', in_=self.actions_frame)
            self.print_btn.configure(state='normal')

        elif state in [WorkflowState.LABEL_PRINTED, WorkflowState.AWAITING_SCAN]:
            self.lock_weight_btn.pack_forget()
            self.locked_indicator.pack(fill='x', in_=self.actions_frame)
            self.print_btn.pack_forget()
            self.scan_frame.pack(fill='x', after=self.locked_indicator, pady=(16, 0))

        elif state == WorkflowState.VERIFIED:
            pass  # Will reset

    def _load_products(self):
        """Load products into grid."""
        self.products_by_category = get_products_by_category()

        for widget in self.tabs_scroll.winfo_children():
            widget.destroy()
        self.category_tabs.clear()

        for category in self.products_by_category.keys():
            tab = CategoryTab(
                self.tabs_scroll,
                text=category,
                command=lambda c=category: self._select_category(c)
            )
            tab.pack(side='left', padx=4)
            self.category_tabs[category] = tab

        if self.products_by_category:
            first = list(self.products_by_category.keys())[0]
            self._select_category(first)

    def _select_category(self, category: str):
        """Select and display category."""
        self.current_category = category

        for cat, tab in self.category_tabs.items():
            tab.set_active(cat == category)

        for widget in self.grid_scroll.winfo_children():
            widget.destroy()
        self.product_cards.clear()

        products = self.products_by_category.get(category, [])
        for i, product in enumerate(products):
            row, col = divmod(i, 3)
            card = ProductCard(
                self.grid_scroll,
                product_name=product.name,
                price_per_lb=product.price_per_lb,
                category=product.category,
                on_select=lambda p=product: self._select_product(p)
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky='nsew')
            self.product_cards[product.id] = card

        for col in range(3):
            self.grid_scroll.columnconfigure(col, weight=1)

    def _select_product(self, product: Product):
        """Select a product."""
        if not self.workflow.can_select_product:
            alert(self, "In Progress", "Complete current label first", 'warning')
            return

        # Deselect previous
        if self.selected_product and self.selected_product.id in self.product_cards:
            self.product_cards[self.selected_product.id].set_selected(False)

        # Select new
        self.selected_product = product
        self.selected_name.configure(
            text=product.name,
            text_color=COLORS['text_primary']
        )
        self.selected_price.configure(text=f"${product.price_per_lb:.2f}/lb")

        if product.id in self.product_cards:
            self.product_cards[product.id].set_selected(True)

        # Reset weight
        self.captured_weight = None
        self.weight_validator.reset()

        self.workflow.transition(WorkflowState.PRODUCT_SELECTED)
        self._update_ui_state()

        self.status_bar.set_status(f"Selected: {product.name}")

    def _setup_scale(self):
        """Setup scale connection."""
        if self.scale:
            self.scale.on_weight(self._on_weight)
            try:
                self.scale.connect()
                self.scale.start_continuous()
            except Exception as e:
                alert(self, "Scale Error", f"Could not connect: {e}", 'error')

    def _on_weight(self, reading: WeightReading):
        """Handle weight reading."""
        self.weight_validator.add_reading(reading.weight_lbs)
        self.weight_display.set_weight(reading.weight_lbs, reading.stable)

        if self.workflow.state == WorkflowState.PRODUCT_SELECTED:
            stable = self.weight_validator.get_stable_weight()
            self.lock_weight_btn.configure(state='normal' if stable else 'disabled')

    def _on_lock_weight(self):
        """Lock the current weight."""
        stable = self.weight_validator.get_stable_weight()
        if not stable:
            alert(self, "Not Stable", "Wait for stable reading", 'warning')
            return

        if stable < 0.1:
            alert(self, "Too Light", "Place item on scale", 'warning')
            return

        if not confirm(self, "Lock Weight", f"Lock at {stable:.2f} lb?"):
            return

        self.captured_weight = stable
        self.locked_weight_label.configure(text=f"{stable:.2f} lb")

        self.workflow.transition(WorkflowState.WEIGHT_CAPTURED)
        self._update_ui_state()

        self.status_bar.set_status(f"Weight locked: {stable:.2f} lb")

    def _on_print(self):
        """Print label."""
        if not self.selected_product or not self.captured_weight:
            return

        product = self.selected_product
        weight = self.captured_weight

        barcode = generate_package_barcode(product.sku, weight)
        package_id = create_package(product.id, weight, barcode)
        self.pending_package_id = package_id
        self.pending_barcode = barcode

        date_str = datetime.now().strftime("%m/%d/%y")
        zpl = self.label_gen.package_label(
            product_name=product.name,
            sku=product.sku,
            weight_lbs=weight,
            price_per_lb=product.price_per_lb,
            barcode=barcode,
            date_packed=date_str
        )

        try:
            self.printer.send_zpl(zpl)
        except Exception as e:
            alert(self, "Print Error", str(e), 'error')
            return

        self.barcode_validator.expect_barcode(barcode, self.SCAN_TIMEOUT)

        self.workflow.transition(WorkflowState.LABEL_PRINTED)
        self.workflow.transition(WorkflowState.AWAITING_SCAN)
        self._update_ui_state()

        self._start_scan_countdown()
        self.status_bar.set_status("SCAN THE LABEL", 'warning')

    def _start_scan_countdown(self):
        """Start countdown timer."""
        self._scan_time_remaining = self.SCAN_TIMEOUT
        self._update_scan_timer()

    def _update_scan_timer(self):
        """Update countdown display."""
        if self.workflow.state != WorkflowState.AWAITING_SCAN:
            return

        self._scan_time_remaining -= 1
        self.scan_timer_label.configure(text=str(self._scan_time_remaining))

        if self._scan_time_remaining <= 5:
            self.scan_timer_label.configure(text_color=COLORS['error'])
        elif self._scan_time_remaining <= 10:
            self.scan_timer_label.configure(text_color=COLORS['warning'])

        if self._scan_time_remaining <= 0:
            self._on_scan_timeout()
        else:
            self.after(1000, self._update_scan_timer)

    def _on_scan_timeout(self):
        """Handle timeout."""
        alert(self, "Timeout", "Label not scanned. Reprint required.", 'error')
        play_error_beep()
        self.workflow.transition(WorkflowState.WEIGHT_CAPTURED)
        self._update_ui_state()

    def _on_reprint(self):
        """Reprint label."""
        if not self.pending_barcode:
            return
        self.workflow.transition(WorkflowState.WEIGHT_CAPTURED)
        self._update_ui_state()
        self._on_print()

    def handle_scan(self, event: ScanEvent):
        """Handle barcode scan."""
        barcode = event.barcode.strip()
        result = self.barcode_validator.validate_scan(barcode)

        if not result.valid:
            show_verification(self, False, result.message)
            play_error_beep()
            log_scan('package', self.pending_package_id or 0, barcode, False)
            if not result.can_retry:
                self.workflow.reset()
                self._reset_state()
            return

        # Success
        if self.pending_package_id:
            verify_package(self.pending_package_id)

            current_box = get_current_box()
            if not current_box:
                create_box()
                current_box = get_current_box()

            assign_package_to_box(self.pending_package_id, current_box.id)
            update_box_totals(current_box.id)

            log_scan('package', self.pending_package_id, barcode, True)

        show_verification(self, True, "VERIFIED")
        play_success_beep()

        self.workflow.transition(WorkflowState.VERIFIED)
        self.barcode_validator.clear_expectation()

        self._reset_state()
        self._load_current_box()

        self.status_bar.flash_success("Package added to box")

    def _reset_state(self):
        """Reset for next package."""
        self.selected_product = None
        self.captured_weight = None
        self.pending_package_id = None
        self.pending_barcode = None
        self.weight_validator.reset()

        self.selected_name.configure(
            text="Tap a product to begin",
            text_color=COLORS['text_muted']
        )
        self.selected_price.configure(text="")

        for card in self.product_cards.values():
            card.set_selected(False)

        self.workflow.reset()
        self._update_ui_state()

    def _load_current_box(self):
        """Load current box info."""
        current_box = get_current_box()

        for widget in self.package_scroll.winfo_children():
            widget.destroy()

        if current_box:
            packages = get_packages_in_box(current_box.id)
            total_weight = sum(p.weight_lbs for p in packages)

            self.box_summary.set_box(
                current_box.box_number,
                len(packages),
                total_weight
            )

            for pkg in packages:
                item = PackageListItem(
                    self.package_scroll,
                    product_name=pkg.product_name or "Unknown",
                    weight=pkg.weight_lbs,
                    verified=pkg.verified
                )
                item.pack(fill='x', pady=2)
        else:
            self.box_summary.set_box(None)

    def refresh(self):
        """Refresh display."""
        self._load_current_box()
        self._update_ui_state()

    def cleanup(self):
        """Cleanup."""
        if self.scale:
            self.scale.stop_continuous()
            self.scale.disconnect()
