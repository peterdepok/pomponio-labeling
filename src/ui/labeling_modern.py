"""
Modern package labeling screen using CustomTkinter.
Touch-optimized for meat processing environment.
"""

import customtkinter as ctk
from datetime import datetime
from typing import Optional, Callable

from ..database import (
    Product, Package, Box,
    get_products_by_category, get_product_by_id,
    create_package, verify_package, get_package_by_barcode,
    get_current_box, create_box, assign_package_to_box, update_box_totals,
    get_packages_in_box, log_scan
)
from ..barcode import generate_package_barcode, parse_package_barcode, validate_package_barcode
from ..printer import LabelGenerator, ZebraPrinter, MockPrinter
from ..scale import Scale, MockScale, WeightReading
from ..scanner import ScanEvent, play_success_beep, play_error_beep
from .theme import COLORS, FONTS, SIZES, CATEGORY_COLORS
from .widgets_modern import (
    BigButton, ProductCard, WeightDisplay, StatusBar,
    BoxSummaryCard, PackageListItem, CategoryTab, show_verification
)


class LabelingScreenModern(ctk.CTkFrame):
    """
    Modern package labeling screen.

    Layout:
    +------------------------------------------+
    | [Category Tabs]                          |
    +------------------+-----------------------+
    | Product Grid     | Selected Product      |
    | (scrollable)     | Weight Display        |
    |                  | [PRINT LABEL] button  |
    |                  +-----------------------+
    |                  | Box Summary           |
    |                  | Package List          |
    +------------------+-----------------------+
    | Status Bar                               |
    +------------------------------------------+
    """

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

        # State
        self.selected_product: Optional[Product] = None
        self.current_weight: float = 0.0
        self.weight_stable: bool = False
        self.current_box: Optional[Box] = None
        self.pending_package_id: Optional[int] = None
        self.pending_barcode: Optional[str] = None
        self.products_by_category: dict = {}
        self.product_cards: dict[int, ProductCard] = {}
        self.category_tabs: dict[str, CategoryTab] = {}
        self.current_category: Optional[str] = None

        # Build UI
        self._build_ui()

        # Load data
        self._load_products()
        self._load_current_box()

        # Start scale
        self._setup_scale()

    def _build_ui(self):
        """Build the labeling screen UI."""
        # Category tabs at top
        self.tabs_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_medium'], height=60)
        self.tabs_frame.pack(fill='x')
        self.tabs_frame.pack_propagate(False)

        self.tabs_scroll = ctk.CTkScrollableFrame(
            self.tabs_frame,
            fg_color='transparent',
            orientation='horizontal',
            height=50
        )
        self.tabs_scroll.pack(fill='both', expand=True, padx=10, pady=5)

        # Main content area
        main = ctk.CTkFrame(self, fg_color='transparent')
        main.pack(fill='both', expand=True, padx=15, pady=15)

        # Left: Product grid
        left = ctk.CTkFrame(main, fg_color='transparent')
        left.pack(side='left', fill='both', expand=True)

        self.grid_scroll = ctk.CTkScrollableFrame(
            left,
            fg_color=COLORS['bg_medium'],
            corner_radius=SIZES['border_radius']
        )
        self.grid_scroll.pack(fill='both', expand=True)

        # Right: Controls and info
        right = ctk.CTkFrame(main, fg_color='transparent', width=380)
        right.pack(side='right', fill='y', padx=(15, 0))
        right.pack_propagate(False)

        # Selected product display
        self.selected_frame = ctk.CTkFrame(
            right,
            fg_color=COLORS['bg_card'],
            corner_radius=SIZES['border_radius']
        )
        self.selected_frame.pack(fill='x', pady=(0, 12))

        ctk.CTkLabel(
            self.selected_frame,
            text="SELECTED",
            font=FONTS['body_sm'],
            text_color=COLORS['text_muted']
        ).pack(pady=(15, 5))

        self.selected_name = ctk.CTkLabel(
            self.selected_frame,
            text="Tap a product",
            font=FONTS['heading_sm'],
            text_color=COLORS['text_secondary'],
            wraplength=340
        )
        self.selected_name.pack(pady=(0, 5))

        self.selected_price = ctk.CTkLabel(
            self.selected_frame,
            text="",
            font=FONTS['body_md'],
            text_color=COLORS['text_muted']
        )
        self.selected_price.pack(pady=(0, 15))

        # Weight display
        self.weight_display = WeightDisplay(right)
        self.weight_display.pack(fill='x', pady=(0, 12))

        # Print button
        self.print_btn = BigButton(
            right,
            text="PRINT LABEL",
            command=self._on_print,
            style='success',
            size='large',
            state='disabled'
        )
        self.print_btn.pack(fill='x', pady=(0, 12))

        # Box summary
        self.box_summary = BoxSummaryCard(right)
        self.box_summary.pack(fill='x', pady=(0, 12))

        # Package list
        self.package_list_frame = ctk.CTkFrame(
            right,
            fg_color=COLORS['bg_card'],
            corner_radius=SIZES['border_radius']
        )
        self.package_list_frame.pack(fill='both', expand=True, pady=(0, 12))

        ctk.CTkLabel(
            self.package_list_frame,
            text="PACKAGES IN BOX",
            font=FONTS['body_sm'],
            text_color=COLORS['text_muted']
        ).pack(pady=(15, 10))

        self.package_scroll = ctk.CTkScrollableFrame(
            self.package_list_frame,
            fg_color='transparent'
        )
        self.package_scroll.pack(fill='both', expand=True, padx=10, pady=(0, 10))

        # Close box button
        self.close_btn = BigButton(
            right,
            text="CLOSE BOX",
            command=self._on_close_box,
            style='warning',
            state='disabled'
        )
        self.close_btn.pack(fill='x')

        # Status bar
        self.status_bar = StatusBar(self)
        self.status_bar.pack(side='bottom', fill='x')

    def _load_products(self):
        """Load products and build category tabs and grid."""
        self.products_by_category = get_products_by_category()

        # Clear existing tabs
        for widget in self.tabs_scroll.winfo_children():
            widget.destroy()
        self.category_tabs.clear()

        # Create category tabs
        for category in self.products_by_category.keys():
            tab = CategoryTab(
                self.tabs_scroll,
                text=category,
                command=lambda c=category: self._select_category(c)
            )
            tab.pack(side='left', padx=3)
            self.category_tabs[category] = tab

        # Select first category
        if self.products_by_category:
            first = list(self.products_by_category.keys())[0]
            self._select_category(first)

    def _select_category(self, category: str):
        """Select category and display products."""
        self.current_category = category

        # Update tab styling
        for cat, tab in self.category_tabs.items():
            tab.set_active(cat == category)

        # Clear grid
        for widget in self.grid_scroll.winfo_children():
            widget.destroy()
        self.product_cards.clear()

        # Add products in grid (3 columns)
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
            card.grid(row=row, column=col, padx=6, pady=6, sticky='nsew')
            self.product_cards[product.id] = card

        # Configure grid weights
        for col in range(3):
            self.grid_scroll.columnconfigure(col, weight=1)

    def _select_product(self, product: Product):
        """Select a product."""
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

        self._update_print_button()
        self.status_bar.set_status(f"Selected: {product.name}")

    def _setup_scale(self):
        """Setup scale callbacks."""
        if self.scale:
            self.scale.on_weight(self._on_weight)
            self.scale.on_stable(self._on_stable)
            try:
                self.scale.connect()
                self.scale.start_continuous()
            except Exception as e:
                self.status_bar.set_status(f"Scale: {e}", 'error')

    def _on_weight(self, reading: WeightReading):
        """Handle weight update."""
        self.current_weight = reading.weight_lbs
        self.weight_stable = reading.stable
        self.weight_display.set_weight(reading.weight_lbs, reading.stable)
        self._update_print_button()

    def _on_stable(self, reading: WeightReading):
        """Handle stable weight."""
        self.status_bar.set_status(f"Weight stable: {reading.weight_lbs:.2f} lb")

    def _update_print_button(self):
        """Update print button state."""
        can_print = (
            self.selected_product is not None and
            self.current_weight > 0.05 and
            self.weight_stable
        )
        self.print_btn.configure(state='normal' if can_print else 'disabled')

    def _on_print(self):
        """Handle print button."""
        if not self.selected_product or self.current_weight <= 0:
            return

        product = self.selected_product
        weight = self.current_weight

        # Generate barcode
        barcode = generate_package_barcode(product.sku, weight)

        # Create package
        package_id = create_package(product.id, weight, barcode)
        self.pending_package_id = package_id
        self.pending_barcode = barcode

        # Print label
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
            self.status_bar.set_status("Label printed. SCAN TO VERIFY", 'warning')
        except Exception as e:
            self.status_bar.flash_error(f"Print error: {e}")

    def handle_scan(self, event: ScanEvent):
        """Handle barcode scan."""
        barcode = event.barcode.strip()

        # Check pending verification
        if self.pending_barcode and barcode == self.pending_barcode:
            self._verify_pending(barcode)
            return

        # Look up existing
        package = get_package_by_barcode(barcode)
        if package:
            if package.verified:
                self.status_bar.set_status(f"Already verified: {package.product_name}")
            else:
                self.status_bar.flash_error("Unknown context")
        else:
            parsed = parse_package_barcode(barcode)
            if parsed:
                self.status_bar.flash_error(f"Not found: SKU {parsed.sku}")
            else:
                self.status_bar.flash_error("Invalid barcode")
            play_error_beep()

        log_scan('package', 0, barcode, False)

    def _verify_pending(self, barcode: str):
        """Verify pending package."""
        if not self.pending_package_id:
            return

        valid, msg = validate_package_barcode(barcode)
        if not valid:
            show_verification(self, False, msg)
            play_error_beep()
            log_scan('package', self.pending_package_id, barcode, False)
            return

        # Mark verified
        verify_package(self.pending_package_id)

        # Ensure box exists
        if not self.current_box:
            create_box()
            self.current_box = get_current_box()

        # Assign to box
        assign_package_to_box(self.pending_package_id, self.current_box.id)
        update_box_totals(self.current_box.id)

        log_scan('package', self.pending_package_id, barcode, True)

        show_verification(self, True, "Package Verified")
        play_success_beep()
        self.status_bar.flash_success("Added to box")

        # Update UI
        self._load_current_box()

        # Clear pending
        self.pending_package_id = None
        self.pending_barcode = None

    def _load_current_box(self):
        """Load current box info."""
        self.current_box = get_current_box()

        # Clear package list
        for widget in self.package_scroll.winfo_children():
            widget.destroy()

        if self.current_box:
            packages = get_packages_in_box(self.current_box.id)
            total_weight = sum(p.weight_lbs for p in packages)

            self.box_summary.set_box(
                self.current_box.box_number,
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

            self.close_btn.configure(state='normal' if packages else 'disabled')
        else:
            self.box_summary.set_box(None)
            self.close_btn.configure(state='disabled')

    def _on_close_box(self):
        """Signal to close box (handled by boxes screen)."""
        self.status_bar.set_status("Go to BOXES tab to close", 'warning')

    def refresh(self):
        """Refresh display."""
        self._load_current_box()

    def cleanup(self):
        """Cleanup resources."""
        if self.scale:
            self.scale.stop_continuous()
            self.scale.disconnect()
